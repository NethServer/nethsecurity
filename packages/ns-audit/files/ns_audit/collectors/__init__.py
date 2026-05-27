#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from __future__ import annotations

from datetime import UTC, datetime

from ns_audit import __version__
from ns_audit.collectors.commands import (
    collect_automatic_updates,
    collect_default_password_check,
    collect_storage_status,
    collect_subscription,
    collect_ubus,
    collect_update_check,
    collect_wireguard,
)
from ns_audit.collectors.local_files import collect_local_files
from ns_audit.collectors.logs import collect_logs
from ns_audit.collectors.uci import collect_uci_packages
from ns_audit.collectors.victoria_logs import collect_victoria_logs


def _file_map(files: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(entry["path"]): entry for entry in files if "path" in entry}


def _uci_map(
    uci_result: dict[str, object], files: dict[str, dict[str, object]]
) -> dict[str, object]:
    packages = uci_result.get("packages")
    if not isinstance(packages, dict):
        packages = {}

    configs: dict[str, object] = {}
    for package, result in packages.items():
        if isinstance(result, dict) and result.get("stdout"):
            configs[str(package)] = result["stdout"]

    for path, entry in files.items():
        prefix = "/etc/config/"
        if not path.startswith(prefix) or not entry.get("readable"):
            continue
        package = path.removeprefix(prefix)
        configs.setdefault(package, entry.get("content", ""))
    return configs


def _command_map(
    ubus: dict[str, object], wireguard: dict[str, object], logs: dict[str, object]
) -> dict[str, object]:
    commands: dict[str, object] = {}
    for name, result in ubus.items():
        if isinstance(result, dict):
            commands[" ".join(result.get("args", [])) or name] = result
    wg_result = wireguard.get("result")
    if isinstance(wg_result, dict):
        commands[" ".join(wg_result.get("args", [])) or "wireguard"] = wg_result
    logread = logs.get("logread")
    if isinstance(logread, dict):
        commands[" ".join(logread.get("args", [])) or "logread"] = logread
    return commands


def collect_all() -> dict[str, object]:
    files = collect_local_files()
    uci = collect_uci_packages()
    ubus = collect_ubus()
    wireguard = collect_wireguard()
    storage_status = collect_storage_status()
    logs = collect_logs()
    victoria_logs = collect_victoria_logs()
    files_by_path = _file_map(files)

    # Extract local version for update check
    board_cmd = ubus.get("system_board") or {}
    board_json = board_cmd.get("parsed_json") or {}
    release = board_json.get("release") or {}
    local_version = str(release.get("version", "")).strip() or None

    default_password = collect_default_password_check()
    update_check = collect_update_check(local_version=local_version)
    automatic_updates = collect_automatic_updates()
    subscription = collect_subscription()

    security_checks = {
        "default_pw_check": default_password,
        "update": update_check,
        "automatic_updates": automatic_updates,
        "subscription": subscription,
    }

    return {
        "schema_version": 1,
        "collector": {
            "name": "ns-audit",
            "version": __version__,
            "collected_at": datetime.now(UTC).isoformat(),
            "mode": "local_read_only",
        },
        "files": files_by_path,
        "uci": _uci_map(uci, files_by_path),
        "commands": _command_map(ubus, wireguard, logs),
        "storage_status": storage_status,
        "logs": logs,
        "wireguard": wireguard,
        "victoria_logs": victoria_logs,
        "security_checks": security_checks,
        "sources": {
            "files": files,
            "uci": uci,
            "ubus": ubus,
            "wireguard": wireguard,
            "storage_status": storage_status,
            "logs": logs,
            "victoria_logs": victoria_logs,
        },
    }
