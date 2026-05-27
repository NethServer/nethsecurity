#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""Syslog, log retention, and log protection analyzer."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

try:
    from ..models import (
        build_finding,
        build_result,
        file_map,
        file_metadata,
        files_matching,
        get_file,
        option_value,
        section_type,
        string_list,
        to_bool,
        uci_sections,
    )
except ImportError:  # pragma: no cover - supports direct execution during development
    from ns_audit.models import (
        build_finding,
        build_result,
        file_map,
        file_metadata,
        files_matching,
        get_file,
        option_value,
        section_type,
        string_list,
        to_bool,
        uci_sections,
    )

AREA = "logging"
MIN_LOG_SIZE_KIB = 128


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _mode_is_world_writable(metadata: Mapping[str, Any]) -> bool:
    mode = metadata.get("mode") or metadata.get("permissions")
    if mode is None:
        return False
    text = str(mode)
    try:
        numeric = int(text, 8) if not text.startswith("0o") else int(text, 8)
    except ValueError:
        match = re.search(r"([0-7]{3,4})", text)
        numeric = int(match.group(1), 8) if match else 0
    return bool(numeric & 0o002)


def _system_logging(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    system_sections = [
        section
        for section in uci_sections(raw_snapshot, "system")
        if section_type(section) in {"system", ""}
    ]
    system = system_sections[0] if system_sections else {}
    log_ip = str(option_value(system, "log_ip", ""))
    log_port = str(option_value(system, "log_port", ""))
    log_proto = str(option_value(system, "log_proto", "udp") or "udp").lower()
    ntp_sections = [
        section
        for section in uci_sections(raw_snapshot, "system")
        if section_type(section) == "timeserver"
    ]
    ntp_enabled = any(
        to_bool(option_value(section, "enabled", "1"), default=True)
        for section in ntp_sections
    )
    ntp_servers = []
    for section in ntp_sections:
        ntp_servers.extend(string_list(option_value(section, "server", [])))
    return {
        "log_size_kib": _int_value(option_value(system, "log_size", 0)),
        "log_ip": log_ip,
        "log_port": log_port,
        "log_proto": log_proto,
        "remote_syslog_configured": bool(log_ip),
        "hostname": str(option_value(system, "hostname", "")),
        "timezone": str(option_value(system, "timezone", "")),
        "ntp_enabled": ntp_enabled,
        "ntp_servers_configured": bool(ntp_servers),
    }


def _rsyslog(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    sections = uci_sections(raw_snapshot, "rsyslog")
    config_texts = [get_file(raw_snapshot, "/etc/rsyslog.conf")]
    config_texts.extend(
        str(value.get("content", "")) if isinstance(value, Mapping) else str(value)
        for value in files_matching(raw_snapshot, "rsyslog").values()
    )
    remotes = []
    tls_indicator = False
    for section in sections:
        target = option_value(section, ("target", "server", "host", "remote"), "")
        if target:
            remotes.append(
                {
                    "target_present": True,
                    "proto": str(option_value(section, "proto", "")),
                }
            )
        tls_indicator = tls_indicator or bool(
            option_value(section, ("tls", "streamdriver", "ca_file", "cert_file"))
        )
    for text in config_texts:
        for line in str(text).splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if (
                "@@" in stripped
                or "omfwd" in stripped
                or re.search(r"(^|\s)@[^@]", stripped)
            ):
                remotes.append(
                    {
                        "target_present": True,
                        "source": "rsyslog.conf",
                        "tcp": "@@" in stripped,
                    }
                )
            if any(
                token in stripped.lower()
                for token in ("gtls", "streamdriver", "x509", "tls")
            ):
                tls_indicator = True
    return {
        "sections": len(sections),
        "remote_targets": remotes,
        "tls_indicator": tls_indicator,
    }


def _storage_status(raw_snapshot: Mapping[str, Any]) -> str:
    status = raw_snapshot.get("storage_status")
    if not isinstance(status, Mapping):
        return ""
    stdout = str(status.get("stdout", "")).strip().lower()
    if stdout in {"ok", "error", "not_configured"}:
        return stdout
    return ""


def _log_files(raw_snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result = []

    def _add_entry(
        path_text: str, content_present: bool, metadata: Mapping[str, Any]
    ) -> None:
        if path_text in seen:
            return
        seen.add(path_text)
        result.append(
            {
                "path": path_text,
                "content_present": content_present,
                "persistent": path_text.startswith("/mnt/data/"),
                "mode": metadata.get("mode") or metadata.get("permissions"),
                "world_writable": _mode_is_world_writable(metadata),
            }
        )

    # Config files / logrotate files (stored in raw_snapshot["files"])
    for path, value in file_map(raw_snapshot).items():
        path_text = str(path)
        if (
            "/log/" not in path_text
            and not path_text.endswith("/messages")
            and "logrotate" not in path_text
        ):
            continue
        _add_entry(path_text, bool(value), file_metadata(raw_snapshot, path_text))

    # Actual log files (stored in raw_snapshot["logs"]["files"] as a list)
    logs = raw_snapshot.get("logs")
    if isinstance(logs, Mapping):
        log_file_list = logs.get("files")
        if isinstance(log_file_list, (list, tuple)):
            for entry in log_file_list:
                if not isinstance(entry, Mapping):
                    continue
                path_text = str(entry.get("path", ""))
                if not path_text:
                    continue
                if (
                    "/log/" not in path_text
                    and not path_text.endswith("/messages")
                    and "logrotate" not in path_text
                ):
                    continue
                content_present = bool(entry.get("readable") and entry.get("content"))
                _add_entry(path_text, content_present, {})

    return result


def _controller_connection(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Check if the device is registered with a NethSecurity controller."""
    for section in uci_sections(raw_snapshot, "ns-plug"):
        server = str(option_value(section, "server", "") or "").strip()
        if server:
            return {"connected": True, "server_present": True}
    return {"connected": False, "server_present": False}


def _logging_assessment(
    storage_mounted: bool,
    persistent_log_files: list[dict[str, Any]],
    remote_targets: list[dict[str, Any]],
    controller: Mapping[str, Any],
) -> dict[str, Any]:
    has_persistent_storage = storage_mounted or bool(persistent_log_files)
    controller_connected = bool(controller.get("connected"))
    remote_forwarding = bool(remote_targets)

    if has_persistent_storage and controller_connected:
        overall = "perfect"
        detail = (
            "Persistent log storage is enabled and the firewall is also forwarding "
            "logs to the controller."
        )
    elif has_persistent_storage and remote_forwarding:
        overall = "excellent"
        detail = (
            "Persistent log storage is enabled and remote forwarding is configured."
        )
    elif has_persistent_storage:
        overall = "very good"
        detail = "Persistent log storage is enabled, so audit evidence survives reboot."
    elif controller_connected or remote_forwarding:
        overall = "good"
        detail = (
            "Remote forwarding is configured, but persistent local storage was not detected."
        )
    else:
        overall = "baseline"
        detail = "Only local volatile logging evidence was detected."

    forwarding = (
        "controller forwarding enabled"
        if controller_connected
        else "remote forwarding configured"
        if remote_forwarding
        else "local only"
    )
    storage = (
        "persistent storage mounted"
        if has_persistent_storage
        else "volatile ring buffer only"
    )
    return {
        "overall_posture": overall,
        "storage_posture": storage,
        "forwarding_posture": forwarding,
        "controller_connected": controller_connected,
        "persistent_storage": has_persistent_storage,
        "summary": detail,
    }


def analyze(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    system_logging = _system_logging(raw_snapshot)
    rsyslog = _rsyslog(raw_snapshot)
    log_files = _log_files(raw_snapshot)
    logrotate_files = sorted(files_matching(raw_snapshot, "logrotate").keys())
    storage_status = _storage_status(raw_snapshot)
    storage_mounted = storage_status == "ok"
    controller = _controller_connection(raw_snapshot)
    remote_targets = []
    if system_logging["remote_syslog_configured"]:
        remote_targets.append(
            {
                "source": "system",
                "target_present": True,
                "proto": system_logging.get("log_proto"),
                "port": system_logging.get("log_port"),
            }
        )
    remote_targets.extend(rsyslog["remote_targets"])
    # Controller connection means logs are automatically forwarded to the remote controller
    if controller["connected"]:
        remote_targets.append({"source": "controller", "target_present": True, "proto": "https"})
    persistent_log_files = [item for item in log_files if item.get("persistent")]
    assessment = _logging_assessment(
        storage_mounted, persistent_log_files, remote_targets, controller
    )
    inventory = {
        "system": system_logging,
        "rsyslog": rsyslog,
        "remote_targets": remote_targets,
        "logrotate_files": logrotate_files,
        "log_files": log_files,
        "storage_status": storage_status or "unknown",
        "persistent_log_files": persistent_log_files,
        "controller": controller,
        "assessment": assessment,
    }
    findings = []

    if not remote_targets:
        findings.append(
            build_finding(
                "logging-no-remote-syslog",
                "Remote syslog/SIEM forwarding not detected",
                "medium",
                AREA,
                "syslog",
                "The snapshot does not show log forwarding to a remote syslog or SIEM destination.",
                {
                    "system_log_ip_present": bool(system_logging.get("log_ip")),
                    "rsyslog_targets": len(rsyslog["remote_targets"]),
                    "controller_connected": controller["connected"],
                },
                "Forward security and system logs to a protected remote collector or SIEM with documented retention. "
                "Connecting to a NethSecurity controller automatically forwards logs.",
                nist=("AU-2", "AU-6", "AU-9", "AU-11", "SI-4"),
                acn=("logging_monitoring", "risk_management"),
            )
        )

    insecure_remote = [
        target
        for target in remote_targets
        if str(target.get("proto", "udp")).lower() == "udp"
        and not rsyslog["tls_indicator"]
    ]
    if insecure_remote:
        findings.append(
            build_finding(
                "logging-remote-syslog-udp",
                "Remote logging appears to use UDP without TLS evidence",
                "medium",
                AREA,
                "syslog",
                "UDP syslog can lose messages and does not provide transport confidentiality or integrity.",
                {"targets": insecure_remote},
                "Prefer TCP/TLS syslog or another authenticated log transport to the collector/SIEM.",
                nist=("AU-9", "SC-8", "SC-13"),
                acn=("logging_monitoring", "secure_communications"),
            )
        )

    if (
        system_logging.get("log_size_kib", 0)
        and system_logging["log_size_kib"] < MIN_LOG_SIZE_KIB
        and not (storage_mounted or inventory["persistent_log_files"])
    ):
        findings.append(
            build_finding(
                "logging-small-ring-buffer",
                "Local log buffer is small",
                "medium",
                AREA,
                "system_log",
                "The OpenWrt system log buffer may roll over quickly when persistent storage is not mounted.",
                {
                    "storage_status": inventory["storage_status"],
                    "storage_mounted": storage_mounted,
                    "persistent_log_files": [
                        item.get("path") for item in inventory["persistent_log_files"]
                    ],
                },
                "Mount persistent storage and/or increase log_size so audit evidence survives rollover.",
                nist=("AU-2", "AU-11", "SI-4"),
                acn=("logging_monitoring", "risk_management"),
            )
        )

    if not inventory["persistent_log_files"]:
        findings.append(
            build_finding(
                "logging-no-persistent-log-evidence",
                "Persistent log storage evidence not detected",
                "low",
                AREA,
                "log_retention",
                "No log files under /mnt/data/log were present in the sanitized snapshot.",
                {"log_files": [item.get("path") for item in log_files]},
                "Use persistent storage or remote forwarding so evidence survives reboot and volatile log rotation.",
                nist=("AU-9", "AU-11"),
                acn=("logging_monitoring", "risk_management"),
            )
        )

    if not logrotate_files:
        findings.append(
            build_finding(
                "logging-no-logrotate-evidence",
                "Log rotation evidence not detected",
                "medium",
                AREA,
                "logrotate",
                "No logrotate configuration files were found in the sanitized snapshot.",
                {},
                "Configure log rotation for local audit logs and verify retention aligns with policy.",
                nist=("AU-9", "AU-11", "CM-6"),
                acn=("logging_monitoring", "risk_management"),
            )
        )

    writable_logs = [item for item in log_files if item.get("world_writable")]
    if writable_logs:
        findings.append(
            build_finding(
                "logging-world-writable-logs",
                "World-writable log files detected",
                "high",
                AREA,
                "log_files",
                "At least one local log file has world-writable permissions in metadata evidence.",
                {"files": writable_logs},
                "Restrict log file permissions to root or the dedicated logging service account.",
                nist=("AU-9", "AC-6"),
                acn=("logging_monitoring", "identity_access_governance"),
            )
        )

    if not (
        system_logging.get("ntp_enabled")
        and system_logging.get("ntp_servers_configured")
    ):
        findings.append(
            build_finding(
                "logging-time-sync-not-confirmed",
                "Time synchronization evidence is incomplete",
                "medium",
                AREA,
                "time_sync",
                "Reliable timestamps require configured and enabled NTP/time synchronization.",
                {
                    "ntp_enabled": system_logging.get("ntp_enabled"),
                    "ntp_servers_configured": system_logging.get(
                        "ntp_servers_configured"
                    ),
                },
                "Enable NTP and configure trusted time servers so audit records have reliable timestamps.",
                nist=("AU-2", "AU-6"),
                acn=("logging_monitoring", "risk_management"),
            )
        )

    return build_result(AREA, inventory, findings)


analyze_logging = analyze
