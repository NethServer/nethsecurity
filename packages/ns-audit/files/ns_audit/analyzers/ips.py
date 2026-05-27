#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""IPS/IDS engine status and coverage analyzer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from ..models import (
        build_finding,
        build_result,
        contains_indicator,
        file_map,
        is_enabled_section,
        option_value,
        service_state,
        string_list,
        uci_sections,
    )
except ImportError:  # pragma: no cover - supports direct execution during development
    from ns_audit.models import (
        build_finding,
        build_result,
        contains_indicator,
        file_map,
        is_enabled_section,
        option_value,
        service_state,
        string_list,
        uci_sections,
    )

AREA = "ips"
RULE_EVIDENCE_TERMS = (
    "rules",
    "community.rules",
    "emerging.rules",
    "last_update",
    "download",
    "oinkcode",
)


def _snort_engine(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    sections = uci_sections(raw_snapshot, "snort") + uci_sections(
        raw_snapshot, "snort3"
    )
    main = sections[0] if sections else {}
    service = service_state(raw_snapshot, ("snort", "snort3"))
    enabled = any(is_enabled_section(section, default=False) for section in sections)
    mode = str(option_value(main, "mode", "")).lower()
    interfaces = []
    for section in sections:
        interfaces.extend(
            string_list(
                option_value(section, ("interface", "interfaces", "ifname"), [])
            )
        )
    rule_evidence = contains_indicator(
        {"sections": sections, "files": file_map(raw_snapshot)}, RULE_EVIDENCE_TERMS
    )
    return {
        "name": "snort",
        "present": bool(sections) or service.get("present"),
        "enabled": enabled,
        "service_running": service.get("running"),
        "service_enabled": service.get("enabled"),
        "mode": mode or "unknown",
        "action": str(option_value(main, "action", "")),
        "method": str(option_value(main, "method", "")),
        "interfaces": sorted(set(interfaces)),
        "logging_enabled": bool(option_value(main, "logging", "")),
        "rule_update_evidence": rule_evidence,
    }


def _suricata_engine(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    sections = uci_sections(raw_snapshot, "suricata")
    main = sections[0] if sections else {}
    service = service_state(raw_snapshot, ("suricata",))
    enabled = any(is_enabled_section(section, default=False) for section in sections)
    interfaces = []
    for section in sections:
        interfaces.extend(
            string_list(
                option_value(section, ("interface", "interfaces", "ifname"), [])
            )
        )
    rule_evidence = contains_indicator(
        {"sections": sections, "files": file_map(raw_snapshot)}, RULE_EVIDENCE_TERMS
    )
    return {
        "name": "suricata",
        "present": bool(sections) or service.get("present"),
        "enabled": enabled,
        "service_running": service.get("running"),
        "service_enabled": service.get("enabled"),
        "mode": str(option_value(main, "mode", "unknown")).lower(),
        "interfaces": sorted(set(interfaces)),
        "rule_update_evidence": rule_evidence,
    }


def analyze(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    engines = [_snort_engine(raw_snapshot), _suricata_engine(raw_snapshot)]
    active_engines = [
        engine
        for engine in engines
        if engine.get("present")
        or engine.get("enabled")
        or engine.get("service_running")
    ]
    inventory = {
        "engines": active_engines or [engines[0]],
        "active_engine_count": len(active_engines),
        "running_engine_count": len(
            [engine for engine in engines if engine.get("service_running")]
        ),
    }
    findings = []

    if not active_engines:
        findings.append(
            build_finding(
                "ips-no-engine-evidence",
                "No IPS/IDS engine evidence found",
                "high",
                AREA,
                "ips_ids",
                "The sanitized snapshot does not show Snort configuration or service status.",
                {},
                "Enable and tune Snort on protected interfaces.",
                nist=("RA-5", "SI-3", "SI-4", "CM-6"),
                acn=("threat_detection", "risk_management"),
            )
        )
    elif inventory["running_engine_count"] == 0:
        # Engines are present/configured but none is actually running
        findings.append(
            build_finding(
                "ips-no-engine-running",
                "IPS/IDS engine is configured but none is running",
                "high",
                AREA,
                "ips_ids",
                "At least one IPS/IDS engine was detected in the configuration, but no engine process is currently active.",
                {"active_engine_count": inventory["active_engine_count"], "running_engine_count": 0},
                "Start the IPS/IDS service, check logs for startup errors, and verify interface binding.",
                nist=("SI-3", "SI-4", "CM-6"),
                acn=("threat_detection", "risk_management"),
            )
        )

    for engine in active_engines:
        name = engine.get("name")
        if engine.get("enabled") and not engine.get("service_running"):
            findings.append(
                build_finding(
                    f"ips-{name}-not-running",
                    f"{name} is enabled but not running",
                    "high",
                    AREA,
                    name,
                    "The IPS/IDS configuration is enabled but procd service status does not show a running instance.",
                    engine,
                    "Start the service, inspect its logs, and resolve configuration or rule loading errors.",
                    nist=("SI-3", "SI-4", "CM-6"),
                    acn=("threat_detection", "risk_management"),
                )
            )
        if engine.get("service_running") and not engine.get("enabled"):
            findings.append(
                build_finding(
                    f"ips-{name}-running-without-enabled-config",
                    f"{name} service is running but enabled configuration was not found",
                    "medium",
                    AREA,
                    name,
                    "Runtime service status and UCI enablement evidence do not match.",
                    engine,
                    "Review UCI configuration and service startup settings so audit evidence matches runtime state.",
                    nist=("CM-6", "SI-4"),
                    acn=("threat_detection", "risk_management"),
                )
            )
        if engine.get("enabled") and not engine.get("interfaces"):
            findings.append(
                build_finding(
                    f"ips-{name}-no-interfaces",
                    f"{name} has no protected interfaces in snapshot",
                    "medium",
                    AREA,
                    name,
                    "The IPS/IDS engine is enabled but no inspected interfaces were found in configuration.",
                    engine,
                    "Assign the engine to the ingress/egress interfaces that require detection or prevention coverage.",
                    nist=("SI-3", "SI-4", "SC-7"),
                    acn=("threat_detection", "network_segmentation"),
                )
            )
        if engine.get("enabled") and not engine.get("rule_update_evidence"):
            findings.append(
                build_finding(
                    f"ips-{name}-no-rule-update-evidence",
                    f"{name} rule update evidence not found",
                    "medium",
                    AREA,
                    name,
                    "No local evidence of IPS/IDS rules or update metadata was found in the sanitized snapshot.",
                    engine,
                    "Download current rules, schedule rule updates, and retain update status in audit evidence.",
                    nist=("RA-5", "SI-3", "SI-4"),
                    acn=("threat_detection", "risk_management"),
                )
            )
        if name == "snort" and engine.get("enabled") and engine.get("mode") == "ids":
            findings.append(
                build_finding(
                    "ips-snort-ids-only",
                    "Snort is configured in IDS mode only",
                    "medium",
                    AREA,
                    "snort",
                    "IDS mode detects threats but does not block malicious traffic inline.",
                    engine,
                    "Use IPS mode for inline protection where supported, or document monitoring-only compensating controls.",
                    nist=("SI-3", "SI-4", "SC-7"),
                    acn=("threat_detection", "network_segmentation"),
                )
            )

    return build_result(AREA, inventory, findings)


analyze_ips = analyze
