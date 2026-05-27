#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""Security event and telemetry indicator analyzer."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

try:
    from ..models import (
        build_finding,
        build_result,
        contains_indicator,
        get_file,
        json_safe,
    )
except ImportError:  # pragma: no cover - supports direct execution during development
    from ns_audit.models import (
        build_finding,
        build_result,
        contains_indicator,
        get_file,
        json_safe,
    )

AREA = "telemetry"
MAX_LOG_LINES = 5000
PATTERNS = {
    "auth_failures": re.compile(
        r"failed password|authentication failure|login failed|invalid user|bad password",
        re.I,
    ),
    "ssh_successes": re.compile(
        r"accepted (password|publickey)|login succeeded|session opened", re.I
    ),
    "firewall_drops": re.compile(
        r"\b(drop|reject)\b.*\b(in=|src=)|\b(in=|src=).*\b(drop|reject)\b", re.I
    ),
    "ips_alerts": re.compile(r"snort|suricata|\[\*\*\]|\bids\b|\bips\b", re.I),
    "vpn_failures": re.compile(
        r"auth_failed|tls error|verify error|openvpn.*fail|wireguard.*fail", re.I
    ),
    "config_changes": re.compile(
        r"uci|ns\.commit|configuration changed|config.*commit", re.I
    ),
    "reboots": re.compile(r"syslogd started|kernel:|boot", re.I),
}
TELEMETRY_TERMS = (
    "netify",
    "telegraf",
    "prometheus",
    "loki",
    "promtail",
    "grafana",
    "monitoring",
)


def _log_summary(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    logs = (
        raw_snapshot.get("logs")
        if isinstance(raw_snapshot.get("logs"), Mapping)
        else {}
    )
    summary = (
        logs.get("summary")
        if isinstance(logs, Mapping) and isinstance(logs.get("summary"), Mapping)
        else {}
    )
    counters = (
        {key: int(value) for key, value in summary.items() if str(value).isdigit()}
        if isinstance(summary, Mapping)
        else {}
    )
    return counters


def _entry_lines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return value.splitlines()
    if isinstance(value, Mapping):
        return [" ".join(f"{key}={item}" for key, item in value.items())]
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        lines = []
        for item in value:
            lines.extend(_entry_lines(item))
        return lines
    return [str(value)]


def _log_lines(raw_snapshot: Mapping[str, Any]) -> list[str]:
    logs = (
        raw_snapshot.get("logs")
        if isinstance(raw_snapshot.get("logs"), Mapping)
        else {}
    )
    lines: list[str] = []

    # Collect from logread stdout
    if isinstance(logs, Mapping):
        logread = logs.get("logread")
        if isinstance(logread, Mapping):
            stdout = logread.get("stdout")
            if isinstance(stdout, str) and stdout:
                lines.extend(stdout.splitlines())

    # Collect from log file evidence list (raw_snapshot["logs"]["files"])
    if isinstance(logs, Mapping):
        log_files = logs.get("files")
        if isinstance(log_files, (list, tuple)):
            for entry in log_files:
                if isinstance(entry, Mapping):
                    content = entry.get("content")
                    if isinstance(content, str) and content:
                        lines.extend(content.splitlines())

    # Fallback: check top-level files dict (in case logs are stored there)
    for path in ("/var/log/messages", "/mnt/data/log/messages"):
        extra = get_file(raw_snapshot, path)
        if extra:
            lines.extend(extra.splitlines())

    return lines[-MAX_LOG_LINES:]


def _count_patterns(lines: Sequence[str]) -> dict[str, int]:
    counts = {name: 0 for name in PATTERNS}
    for line in lines:
        for name, pattern in PATTERNS.items():
            if pattern.search(line):
                counts[name] += 1
    return counts


def analyze(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    lines = _log_lines(raw_snapshot)
    counters = _count_patterns(lines)
    for key, value in _log_summary(raw_snapshot).items():
        counters[key] = max(counters.get(key, 0), value)
    telemetry_detected = contains_indicator(raw_snapshot, TELEMETRY_TERMS)
    inventory = {
        "log_lines_analyzed": len(lines),
        "security_event_counters": counters,
        "telemetry_indicators_detected": telemetry_detected,
        "telemetry_terms": [
            term
            for term in TELEMETRY_TERMS
            if contains_indicator(raw_snapshot, (term,))
        ],
    }
    findings = []

    if not lines and not any(counters.values()):
        findings.append(
            build_finding(
                "telemetry-no-log-evidence",
                "No log or telemetry evidence was available for analysis",
                "medium",
                AREA,
                "logs",
                "The sanitized snapshot did not include log lines or precomputed security counters.",
                {},
                "Collect bounded log samples or summarized counters from logread and persistent log files for audit evidence.",
                nist=("AU-2", "AU-6", "SI-4"),
                acn=("logging_monitoring", "risk_management"),
            )
        )

    auth_failures = counters.get("auth_failures", 0)
    if auth_failures >= 50:
        severity = "high"
    elif auth_failures >= 10:
        severity = "medium"
    else:
        severity = ""
    if severity:
        findings.append(
            build_finding(
                "telemetry-auth-failure-spike",
                "Repeated authentication failures found in logs",
                severity,
                AREA,
                "authentication_logs",
                "Log indicators show repeated failed authentication attempts during the sampled period.",
                {"auth_failures": auth_failures},
                "Investigate source addresses, block abusive sources, and verify account lockout/MFA controls.",
                nist=("AU-6", "IA-2", "SI-4"),
                acn=(
                    "identity_access_governance",
                    "logging_monitoring",
                    "threat_detection",
                ),
            )
        )

    vpn_failures = counters.get("vpn_failures", 0)
    if vpn_failures >= 10:
        findings.append(
            build_finding(
                "telemetry-vpn-failures",
                "VPN failure indicators found in logs",
                "medium",
                AREA,
                "vpn_logs",
                "OpenVPN or WireGuard failure patterns were observed in the sampled logs.",
                {"vpn_failures": vpn_failures},
                "Review VPN authentication and TLS errors, then correlate with user and source address activity.",
                nist=("AU-6", "AC-17", "SI-4"),
                acn=("secure_communications", "logging_monitoring", "threat_detection"),
            )
        )

    ips_alerts = counters.get("ips_alerts", 0)
    if ips_alerts:
        findings.append(
            build_finding(
                "telemetry-ips-alerts",
                "IPS/IDS alert indicators found in logs",
                "medium",
                AREA,
                "ips_logs",
                "Snort/Suricata or generic IDS/IPS alert indicators were observed in the sampled logs.",
                {"ips_alerts": ips_alerts},
                "Triage alerts, confirm rule freshness, and document incident handling or false-positive disposition.",
                nist=("AU-6", "RA-5", "SI-3", "SI-4"),
                acn=("threat_detection", "logging_monitoring", "risk_management"),
            )
        )

    firewall_drops = counters.get("firewall_drops", 0)
    if firewall_drops >= 500:
        findings.append(
            build_finding(
                "telemetry-high-firewall-drops",
                "High firewall drop/reject volume found in logs",
                "low",
                AREA,
                "firewall_logs",
                "Firewall drop/reject indicators exceed the informational audit threshold.",
                {"firewall_drops": firewall_drops},
                "Review whether the volume reflects expected internet noise or targeted scanning and tune alerting thresholds.",
                nist=("AU-6", "SI-4"),
                acn=("logging_monitoring", "threat_detection"),
            )
        )

    if not telemetry_detected:
        findings.append(
            build_finding(
                "telemetry-monitoring-not-detected",
                "Monitoring/telemetry integration indicator not detected",
                "low",
                AREA,
                "telemetry",
                "No local evidence of monitoring integrations such as Netify, Telegraf, Prometheus, Loki, or Promtail was found.",
                {"terms_checked": TELEMETRY_TERMS},
                "Enable telemetry integrations appropriate for the deployment and document where operational metrics are reviewed.",
                nist=("AU-6", "SI-4"),
                acn=("logging_monitoring", "risk_management"),
            )
        )

    return build_result(AREA, json_safe(inventory), findings)


analyze_telemetry = analyze
