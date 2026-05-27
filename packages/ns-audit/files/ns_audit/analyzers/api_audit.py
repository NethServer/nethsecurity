#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""NethSecurity API audit trail analyzer.

Parses nethsecurity-api log entries from /var/log/messages to extract:
- Admin login and logout events (timestamp, user, source IP)
- Authentication failures (unauthorized requests, invalid signatures)
- Configuration changes committed via ns.commit (with diff payload)
- Recent admin API actions
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

try:
    from ..models import (
        build_finding,
        build_result,
        json_safe,
    )
except ImportError:  # pragma: no cover - supports direct execution during development
    from ns_audit.models import (
        build_finding,
        build_result,
        json_safe,
    )

AREA = "api_audit"

# nethsecurity-api log line patterns
_RE_API_LINE = re.compile(r"nethsecurity.api\[", re.I)
_RE_AUTH_SUCCESS = re.compile(
    r"authentication success for user (\S+) from ([\d.:]+)", re.I
)
_RE_LOGIN_RESPONSE = re.compile(r"login response success for user (\S+)", re.I)
_RE_LOGOUT = re.compile(r"logout response success for user (\S+)", re.I)
_RE_UNAUTHORIZED = re.compile(r"unauthorized request[:\s]+(.+)", re.I)
_RE_AUTH_FAILURE = re.compile(r"authentication fail(?:ure|ed) for user (\S+)", re.I)
_RE_AUTHORIZATION = re.compile(
    r"authorization success for user (\S+)\.\s+\w+\s+/api/ubus/call\s+(\{.+\})", re.I
)
_RE_SYSLOG_TIMESTAMP = re.compile(r"^(\w+\s+\d+\s+[\d:]+)")


def _extract_timestamp(line: str) -> str:
    m = _RE_SYSLOG_TIMESTAMP.match(line)
    return m.group(1) if m else ""


def _parse_api_payload(json_text: str) -> dict[str, Any]:
    try:
        return json.loads(json_text) if json_text else {}
    except (json.JSONDecodeError, ValueError):
        return {}


def _commit_description(payload: dict[str, Any]) -> str:
    """Build a human-readable description of a ns.commit change payload."""
    changes = payload.get("payload", {}).get("changes", {})
    if not changes:
        return ""
    parts = []
    for pkg, ops in changes.items():
        if not isinstance(ops, list):
            continue
        for op in ops:
            if not isinstance(op, (list, tuple)) or len(op) < 2:
                continue
            op_type = op[0]
            if op_type == "set" and len(op) >= 4:
                parts.append(f"{pkg}.{op[1]}.{op[2]} = {op[3]}")
            elif op_type == "delete" and len(op) >= 3:
                parts.append(f"del {pkg}.{op[1]}.{op[2]}")
            elif op_type == "add" and len(op) >= 3:
                parts.append(f"add {pkg}.{op[1]} ({op[2]})")
            else:
                parts.append(f"{pkg}: {op_type}")
    return "; ".join(parts[:8])


def _collect_log_lines(raw_snapshot: Mapping[str, Any]) -> list[str]:
    """Return all log lines from the collected log evidence.

    Reads from logread, primary files, and secondary_files so that API audit
    events are not missed even when storage is the active bundle source.
    """
    logs = raw_snapshot.get("logs")
    if not isinstance(logs, Mapping):
        return []
    seen: set[str] = set()
    lines: list[str] = []

    def _add_lines(text: str) -> None:
        for ln in text.splitlines():
            if ln not in seen:
                seen.add(ln)
                lines.append(ln)

    logread = logs.get("logread")
    if isinstance(logread, Mapping):
        stdout = logread.get("stdout")
        if isinstance(stdout, str):
            _add_lines(stdout)

    for key in ("files", "secondary_files"):
        for entry in logs.get(key) or []:
            if isinstance(entry, Mapping):
                content = entry.get("content")
                if isinstance(content, str):
                    _add_lines(content)

    return lines


def _parse_events(log_lines: Sequence[str]) -> dict[str, list[dict[str, Any]]]:
    logins: list[dict[str, Any]] = []
    logouts: list[dict[str, Any]] = []
    auth_failures: list[dict[str, Any]] = []
    config_changes: list[dict[str, Any]] = []

    for line in log_lines:
        if not _RE_API_LINE.search(line):
            continue
        ts = _extract_timestamp(line)

        m = _RE_AUTH_SUCCESS.search(line)
        if m:
            logins.append(
                {
                    "timestamp": ts,
                    "user": m.group(1),
                    "source_ip": m.group(2),
                    "type": "login",
                }
            )
            continue

        m = _RE_AUTH_FAILURE.search(line)
        if m:
            auth_failures.append(
                {
                    "timestamp": ts,
                    "user": m.group(1),
                    "reason": "authentication_failure",
                }
            )
            continue

        m = _RE_UNAUTHORIZED.search(line)
        if m:
            auth_failures.append(
                {"timestamp": ts, "user": "", "reason": m.group(1).strip()}
            )
            continue

        m = _RE_LOGOUT.search(line)
        if m:
            logouts.append({"timestamp": ts, "user": m.group(1)})
            continue

        m = _RE_AUTHORIZATION.search(line)
        if m:
            user = m.group(1)
            payload = _parse_api_payload(m.group(2))
            path = payload.get("path", "")
            method = payload.get("method", "")
            if path == "ns.commit" and method == "commit":
                desc = _commit_description(payload)
                config_changes.append(
                    {
                        "timestamp": ts,
                        "user": user,
                        "path": path,
                        "method": method,
                        "description": desc,
                        "raw_payload": json.dumps(
                            payload.get("payload", {}), ensure_ascii=False
                        )[:300],
                    }
                )

    return {
        "logins": logins[-50:],
        "logouts": logouts[-50:],
        "auth_failures": auth_failures[-100:],
        "config_changes": config_changes[-50:],
    }


def analyze(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    log_lines = _collect_log_lines(raw_snapshot)
    api_lines = [ln for ln in log_lines if _RE_API_LINE.search(ln)]
    events = _parse_events(log_lines)

    logins = events["logins"]
    logouts = events["logouts"]
    auth_failures = events["auth_failures"]
    config_changes = events["config_changes"]

    inventory = {
        "api_log_lines": len(api_lines),
        "login_events": logins,
        "logout_events": logouts,
        "auth_failure_events": auth_failures,
        "config_change_events": config_changes,
        "counts": {
            "logins": len(logins),
            "logouts": len(logouts),
            "auth_failures": len(auth_failures),
            "config_changes": len(config_changes),
        },
    }

    findings: list[dict[str, Any]] = []

    if not api_lines:
        findings.append(
            build_finding(
                "api-audit-no-log-evidence",
                "NethSecurity API log entries not found",
                "medium",
                AREA,
                "api_logs",
                "No nethsecurity-api entries were found in the sampled log lines. "
                "API login, logout, and config-change events cannot be audited.",
                {},
                "Verify rsyslog is forwarding nethsecurity-api messages and that the log "
                "buffer is large enough to retain recent activity.",
                nist=("AU-2", "AU-3", "AU-6"),
                acn=("logging_monitoring", "identity_access_governance"),
            )
        )

    if len(auth_failures) >= 20:
        severity = "high"
    elif len(auth_failures) >= 5:
        severity = "medium"
    else:
        severity = ""
    if severity:
        findings.append(
            build_finding(
                "api-audit-auth-failures",
                "Multiple API authentication failures detected",
                severity,
                AREA,
                "api_auth",
                f"{len(auth_failures)} unauthorized or failed authentication events were found "
                "in the sampled API log lines.",
                {"auth_failure_count": len(auth_failures), "sample": auth_failures[:3]},
                "Investigate source addresses and consider enabling account lockout, "
                "rate limiting, or IP allowlisting for the management API.",
                nist=("AC-7", "AU-6", "IA-2", "SI-4"),
                acn=(
                    "identity_access_governance",
                    "logging_monitoring",
                    "threat_detection",
                ),
            )
        )

    if config_changes:
        findings.append(
            build_finding(
                "api-audit-config-changes-detected",
                "Configuration changes committed via API",
                "info",
                AREA,
                "api_config",
                f"{len(config_changes)} ns.commit operations were found in the sampled log. "
                "Each entry records the user, timestamp, and exact UCI change payload.",
                {
                    "config_change_count": len(config_changes),
                    "sample": config_changes[:3],
                },
                "Review configuration change events periodically and ensure all changes "
                "are authorized and traceable to a named administrator account.",
                nist=("AU-2", "AU-3", "CM-3", "CM-5"),
                acn=("logging_monitoring", "risk_management"),
            )
        )

    return build_result(AREA, json_safe(inventory), findings)
