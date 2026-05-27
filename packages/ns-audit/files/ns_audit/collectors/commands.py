#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from __future__ import annotations

import json
import shutil
import subprocess
import urllib.error
import urllib.request
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ns_audit.config import COMMAND_OUTPUT_BYTES, COMMAND_TIMEOUT, LATEST_RELEASE_URL, UBUS_CALLS, UPDATE_CHECK_TIMEOUT
from ns_audit.models import CommandEvidence

_DEFAULT_PASSWORDS = ("Nethesis,1234",)


def _decode_limited(data: bytes | None, max_bytes: int) -> tuple[str, bool]:
    if not data:
        return "", False
    truncated = len(data) > max_bytes
    limited = data[:max_bytes]
    text = limited.decode("utf-8", "replace")
    if truncated:
        text = f"{text}\n<truncated>"
    return text, truncated


def _parse_json(text: str) -> Any:
    if not text.strip():
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def run_command(
    args: Sequence[str],
    *,
    name: str | None = None,
    timeout: int = COMMAND_TIMEOUT,
    max_bytes: int = COMMAND_OUTPUT_BYTES,
) -> dict[str, object]:
    command = list(args)
    evidence_name = name or " ".join(command)
    if not command:
        return CommandEvidence(
            name=evidence_name, args=[], found=False, error="empty_command"
        ).to_dict()
    if not command_exists(command[0]):
        return CommandEvidence(
            name=evidence_name, args=command, found=False, error="command_not_found"
        ).to_dict()

    try:
        completed = subprocess.run(
            command, capture_output=True, check=False, timeout=timeout
        )
    except subprocess.TimeoutExpired as exc:
        stdout, stdout_truncated = _decode_limited(exc.stdout, max_bytes)
        stderr, stderr_truncated = _decode_limited(exc.stderr, max_bytes)
        return CommandEvidence(
            name=evidence_name,
            args=command,
            found=True,
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
            truncated=stdout_truncated or stderr_truncated,
            error="timeout",
        ).to_dict()
    except OSError as exc:
        return CommandEvidence(
            name=evidence_name, args=command, found=True, error=str(exc)
        ).to_dict()

    stdout, stdout_truncated = _decode_limited(completed.stdout, max_bytes)
    stderr, stderr_truncated = _decode_limited(completed.stderr, max_bytes)
    return CommandEvidence(
        name=evidence_name,
        args=command,
        found=True,
        returncode=completed.returncode,
        stdout=stdout,
        stderr=stderr,
        truncated=stdout_truncated or stderr_truncated,
        parsed_json=_parse_json(stdout),
    ).to_dict()


def collect_ubus() -> dict[str, object]:
    return {name: run_command(args, name=name) for name, args in UBUS_CALLS}


def collect_wireguard() -> dict[str, object]:
    if command_exists("wg-json"):
        return {
            "source": "wg-json",
            "result": run_command(("wg-json",), name="wg-json"),
        }
    if command_exists("wg"):
        return {
            "source": "wg",
            "result": run_command(("wg", "show", "all"), name="wg_show_all"),
        }
    return {
        "source": None,
        "result": CommandEvidence(
            "wireguard", [], found=False, error="command_not_found"
        ).to_dict(),
    }


def collect_storage_status() -> dict[str, object]:
    if command_exists("/usr/sbin/storage-status"):
        return run_command(("/usr/sbin/storage-status",), name="storage-status")
    return CommandEvidence(
        "storage-status",
        ["/usr/sbin/storage-status"],
        found=False,
        error="command_not_found",
    ).to_dict()


def collect_default_password_check() -> dict[str, object]:
    """Check if root account uses the known factory-default password.

    Returns only a boolean result — never stores the actual hash or password.
    """
    shadow = Path("/etc/shadow")
    if not shadow.exists():
        return {"checked": False, "error": "shadow_not_found"}
    try:
        content = shadow.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"checked": False, "error": str(exc)}

    root_hash: str | None = None
    for line in content.splitlines():
        if line.startswith("root:"):
            parts = line.split(":")
            if len(parts) >= 2:
                root_hash = parts[1]
            break

    if not root_hash or root_hash in {"!", "!!", "*", "x", ""}:
        return {"checked": True, "has_pw": False, "is_default": False}

    try:
        from passlib.hash import md5_crypt, sha256_crypt, sha512_crypt

        for candidate in _DEFAULT_PASSWORDS:
            for verifier in (sha512_crypt, sha256_crypt, md5_crypt):
                try:
                    if verifier.verify(candidate, root_hash):
                        return {"checked": True, "has_pw": True, "is_default": True}
                except Exception:
                    pass
        return {"checked": True, "has_pw": True, "is_default": False}
    except ImportError:
        return {"checked": True, "has_pw": True, "is_default": None, "error": "passlib_unavailable"}


def collect_update_check(local_version: str | None = None) -> dict[str, object]:
    """Fetch the latest NethSecurity release version and compare to local."""
    try:
        req = urllib.request.Request(LATEST_RELEASE_URL, headers={"User-Agent": "ns-audit/1"})
        with urllib.request.urlopen(req, timeout=UPDATE_CHECK_TIMEOUT) as resp:
            latest = resp.read(200).decode("utf-8", "replace").strip().splitlines()[0].strip()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return {"checked": False, "latest_version": None, "local_version": local_version, "error": str(exc)}

    if not local_version:
        return {"checked": True, "latest_version": latest, "local_version": None, "up_to_date": None}

    def _parse(v: str) -> tuple[int, ...]:
        # Extract leading numeric version (e.g. "8.8.0" from "8.8.0-nethsecurity-...")
        base = v.split("-")[0]
        parts = base.split(".")
        result = []
        for p in parts:
            if p.isdigit():
                result.append(int(p))
            else:
                break
        return tuple(result)

    try:
        up_to_date = _parse(local_version) >= _parse(latest)
    except Exception:
        up_to_date = None

    return {
        "checked": True,
        "latest_version": latest,
        "local_version": local_version,
        "up_to_date": up_to_date,
    }


def collect_automatic_updates() -> dict[str, object]:
    """Check whether automatic updates are enabled via local ubus."""
    result = run_command(
        ("ubus", "call", "ns.update", "get-automatic-updates-status"),
        name="ns.update get-automatic-updates-status",
    )
    parsed = result.get("parsed_json")
    if isinstance(parsed, dict):
        return {
            "checked": True,
            "enabled": bool(parsed.get("enabled")),
        }
    error = str(result.get("error") or result.get("stderr") or "").strip()
    return {
        "checked": False,
        "enabled": None,
        "error": error or "no_response",
    }


def collect_subscription() -> dict[str, object]:
    """Collect subscription status via ubus."""
    try:
        result = subprocess.run(
            ["ubus", "call", "ns.subscription", "info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            active = bool(data.get("active"))
            plan = str(data.get("plan", "") or "").strip()
            server_id = data.get("server_id")
            expiration = data.get("expiration", 0)
            return {
                "available": True,
                "active": active,
                "plan": plan if plan else None,
                "server_id": server_id,
                "expiration": expiration,
            }
        return {"available": True, "active": False}
    except Exception as exc:
        return {"available": False, "error": str(exc)}
