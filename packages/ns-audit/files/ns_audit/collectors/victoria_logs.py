#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""Collect authentication events from victoria-logs via its HTTP query API.

Queries the local victoria-logs instance for SSH, UI, and VPN login/logout
events. Falls back gracefully when victoria-logs is unavailable.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

try:
    from ..config import VICTORIA_LOGS_QUERY_LIMIT, VICTORIA_LOGS_URL
except ImportError:  # pragma: no cover
    from ns_audit.config import VICTORIA_LOGS_QUERY_LIMIT, VICTORIA_LOGS_URL

VICTORIA_LOGS_TIMEOUT = 5

# LogsQL queries for each auth event category
_QUERIES: list[tuple[str, str]] = [
    (
        "ssh",
        'app_name:"dropbear" AND facility_keyword:authpriv',
    ),
    (
        "ui",
        'app_name:"nethsecurity-api" AND (_msg:"login response" OR _msg:"logout response" OR _msg:"login_success" OR _msg:"logout_success" OR _msg:"authentication success for user" OR _msg:"authentication failed for user")',
    ),
    (
        "openvpn_auth",
        'app_name:"openvpn-auth" AND _msg:"event=auth"',
    ),
    (
        "openvpn_connect",
        'app_name:"openvpn-connect" AND _msg:"event=connect"',
    ),
    (
        "openvpn_disconnect",
        'app_name:"openvpn-disconnect" AND _msg:"event=disconnect"',
    ),
    (
        "vpn_legacy",
        'app_name:"openvpn" OR app_name:"strongswan" OR app_name:"charon"',
    ),
]

# Patterns to parse SSH dropbear lines
_RE_SSH_AUTH_OK = re.compile(
    r"(?:Pubkey auth succeeded|Password auth succeeded) for '?(\S+?)'?"
    r"(?: with \S+ key (\S+))? from ([\d.:]+)",
    re.I,
)
_RE_SSH_AUTH_FAIL = re.compile(
    r"(?:Bad password attempt|Login attempt for nonexistent user)(?: from ([\d.:]+))?",
    re.I,
)
_RE_SSH_DISCONNECT = re.compile(
    r"Exit (?:\((\S+)\) )?from <?([\d.:]+)(?::\d+)?>?", re.I
)
_RE_SSH_CONNECT = re.compile(r"Child connection from ([\d.:]+)", re.I)

# Patterns for nethsecurity-api UI events
_RE_UI_LOGIN = re.compile(r"login response success for user (\S+)", re.I)
_RE_UI_LOGIN_FAIL = re.compile(r"login response failed for user (\S+)", re.I)
_RE_UI_LOGOUT = re.compile(r"logout response success for user (\S+)", re.I)
_RE_UI_AUTH_OK = re.compile(r"authentication success for user (\S+)(?: from ([^ ]+))?", re.I)
_RE_UI_AUTH_FAIL = re.compile(
    r"authentication failed for user (\S+)(?: from ([^: ]+)(?::\d+)?)?(?:: (.*))?",
    re.I,
)

# Patterns for VPN events
_RE_VPN_CONNECT = re.compile(
    r"(?:client connected|peer connected|MULTI_sva|established CHILD_SA)", re.I
)
_RE_VPN_DISCONNECT = re.compile(
    r"(?:client disconnected|peer disconnected|SIGTERM|deleting CHILD_SA)", re.I
)
_RE_KEY_VALUE = re.compile(r"(\w+)=([^\s]+)")


def _http_get(url: str, params: dict[str, str]) -> str | None:
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(full_url, timeout=VICTORIA_LOGS_TIMEOUT) as resp:
            return resp.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError):
        return None


def _query(base_url: str, logsql: str, limit: int) -> list[dict[str, Any]] | None:
    """Run a LogsQL query and return parsed JSON lines."""
    raw = _http_get(
        f"{base_url}/select/logsql/query",
        {"query": logsql, "limit": str(limit), "start": "30d"},
    )
    if raw is None:
        return None
    events = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _classify_ssh(entry: dict[str, Any]) -> dict[str, Any] | None:
    msg = entry.get("_msg", "")
    ts = entry.get("_time", "")
    host = entry.get("hostname", "")

    m = _RE_SSH_AUTH_OK.search(msg)
    if m:
        return {
            "time": ts,
            "source": "ssh",
            "event_type": "login_success",
            "user": m.group(1),
            "detail": f"key={m.group(2) or 'password'} from {m.group(3)}",
            "host": host,
        }

    m = _RE_SSH_AUTH_FAIL.search(msg)
    if m:
        return {
            "time": ts,
            "source": "ssh",
            "event_type": "login_failure",
            "user": "",
            "detail": f"failed attempt from {m.group(1) or 'unknown'}",
            "host": host,
        }

    m = _RE_SSH_DISCONNECT.search(msg)
    if m:
        return {
            "time": ts,
            "source": "ssh",
            "event_type": "logout",
            "user": m.group(1) or "",
            "detail": f"disconnected from {m.group(2)}",
            "host": host,
        }

    return None


def _classify_ui(entry: dict[str, Any]) -> dict[str, Any] | None:
    msg = entry.get("_msg", "")
    ts = entry.get("_time", "")
    host = entry.get("hostname", "")

    m = _RE_UI_LOGIN.search(msg)
    if m:
        return {
            "time": ts,
            "source": "ui",
            "event_type": "login_success",
            "user": m.group(1),
            "detail": "web UI login",
            "host": host,
        }

    m = _RE_UI_AUTH_OK.search(msg)
    if m:
        detail = "web UI authentication"
        if m.group(2):
            detail = f"{detail} from {m.group(2)}"
        return {
            "time": ts,
            "source": "ui",
            "event_type": "login_success",
            "user": m.group(1),
            "detail": detail,
            "host": host,
        }

    m = _RE_UI_LOGIN_FAIL.search(msg)
    if m:
        return {
            "time": ts,
            "source": "ui",
            "event_type": "login_failure",
            "user": m.group(1),
            "detail": "web UI login failed",
            "host": host,
        }

    m = _RE_UI_AUTH_FAIL.search(msg)
    if m:
        detail_parts = []
        if m.group(2):
            detail_parts.append(f"from {m.group(2)}")
        if m.group(3):
            detail_parts.append(m.group(3))
        return {
            "time": ts,
            "source": "ui",
            "event_type": "login_failure",
            "user": m.group(1),
            "detail": " ".join(detail_parts) if detail_parts else "web UI authentication failed",
            "host": host,
        }

    m = _RE_UI_LOGOUT.search(msg)
    if m:
        return {
            "time": ts,
            "source": "ui",
            "event_type": "logout",
            "user": m.group(1),
            "detail": "web UI logout",
            "host": host,
        }

    return None


def _parse_key_value_message(message: str) -> dict[str, str]:
    return {key: value for key, value in _RE_KEY_VALUE.findall(message)}


def _classify_openvpn_structured(entry: dict[str, Any]) -> dict[str, Any] | None:
    msg = entry.get("_msg", "")
    ts = entry.get("_time", "")
    host = entry.get("hostname", "")
    values = _parse_key_value_message(msg)
    event = values.get("event")
    if not event:
        return None

    user = values.get("user", "")
    remote_ip = values.get("remote_ip", "")
    instance = values.get("instance", "")
    detail_parts = []
    if instance:
        detail_parts.append(f"instance={instance}")
    if remote_ip:
        detail_parts.append(f"remote_ip={remote_ip}")

    if event == "auth":
        outcome = values.get("outcome", "success").lower()
        reason = values.get("reason", "")
        if reason:
            detail_parts.append(f"reason={reason}")
        return {
            "time": ts,
            "source": "openvpn",
            "event_type": "login_success" if outcome == "success" else "login_failure",
            "user": user,
            "detail": " ".join(detail_parts) if detail_parts else "openvpn authentication",
            "host": host,
        }

    if event == "connect":
        virtual_ip = values.get("virtual_ip", "")
        if virtual_ip:
            detail_parts.append(f"virtual_ip={virtual_ip}")
        return {
            "time": ts,
            "source": "openvpn",
            "event_type": "vpn_connect",
            "user": user,
            "detail": " ".join(detail_parts) if detail_parts else "openvpn connected",
            "host": host,
        }

    if event == "disconnect":
        virtual_ip = values.get("virtual_ip", "")
        duration = values.get("duration", "")
        if virtual_ip:
            detail_parts.append(f"virtual_ip={virtual_ip}")
        if duration:
            detail_parts.append(f"duration={duration}")
        return {
            "time": ts,
            "source": "openvpn",
            "event_type": "vpn_disconnect",
            "user": user,
            "detail": " ".join(detail_parts) if detail_parts else "openvpn disconnected",
            "host": host,
        }

    return None


def _classify_vpn(entry: dict[str, Any]) -> dict[str, Any] | None:
    msg = entry.get("_msg", "")
    ts = entry.get("_time", "")
    host = entry.get("hostname", "")
    app = entry.get("app_name", "vpn")

    if _RE_VPN_CONNECT.search(msg):
        return {
            "time": ts,
            "source": app,
            "event_type": "vpn_connect",
            "user": "",
            "detail": msg.strip()[:120],
            "host": host,
        }
    if _RE_VPN_DISCONNECT.search(msg):
        return {
            "time": ts,
            "source": app,
            "event_type": "vpn_disconnect",
            "user": "",
            "detail": msg.strip()[:120],
            "host": host,
        }
    return None


_CLASSIFIERS = {
    "ssh": _classify_ssh,
    "ui": _classify_ui,
    "openvpn_auth": _classify_openvpn_structured,
    "openvpn_connect": _classify_openvpn_structured,
    "openvpn_disconnect": _classify_openvpn_structured,
    "vpn_legacy": _classify_vpn,
}


def collect_victoria_logs(
    base_url: str = VICTORIA_LOGS_URL,
    limit: int = VICTORIA_LOGS_QUERY_LIMIT,
) -> dict[str, Any]:
    """Query victoria-logs for auth events and return structured results."""
    available = False
    events: list[dict[str, Any]] = []
    errors: dict[str, str] = {}

    for category, logsql in _QUERIES:
        raw_entries = _query(base_url, logsql, limit)
        if raw_entries is None:
            errors[category] = "query_failed"
            continue
        if raw_entries:
            available = True

        classifier = _CLASSIFIERS[category]
        for entry in raw_entries:
            classified = classifier(entry)
            if classified:
                events.append(classified)

    # Sort chronologically (ISO timestamps sort lexicographically)
    events.sort(key=lambda e: e.get("time", ""))

    return {
        "available": available,
        "event_count": len(events),
        "events": events,
        "errors": errors,
    }
