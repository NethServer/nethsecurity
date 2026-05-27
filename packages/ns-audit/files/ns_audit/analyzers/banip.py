#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""BanIP threat-feed and rate-limiting configuration analyzer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from ..models import (
        build_finding,
        build_result,
        option_value,
        string_list,
        to_bool,
        uci_sections,
    )
except ImportError:  # pragma: no cover - supports direct execution during development
    from ns_audit.models import (
        build_finding,
        build_result,
        option_value,
        string_list,
        to_bool,
        uci_sections,
    )

AREA = "banip"


def _banip_global(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    sections = uci_sections(raw_snapshot, "banip")
    main = {}
    for section in sections:
        name = str(section.get(".name", "") or section.get("name", "")).strip()
        if name == "global" or not main:
            main = section
    if not main:
        return {"present": False}

    feeds = string_list(option_value(main, "ban_feed", []))
    return {
        "present": True,
        "enabled": to_bool(option_value(main, "ban_enabled", "0"), default=False),
        "loglimit": str(option_value(main, "ban_loglimit", "") or "").strip(),
        "icmplimit": str(option_value(main, "ban_icmplimit", "") or "").strip(),
        "synlimit": str(option_value(main, "ban_synlimit", "") or "").strip(),
        "udplimit": str(option_value(main, "ban_udplimit", "") or "").strip(),
        "ban_feeds": feeds,
    }


def analyze(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    cfg = _banip_global(raw_snapshot)
    inventory = {"banip": cfg}
    findings = []

    if not cfg.get("present"):
        findings.append(
            build_finding(
                "banip-not-installed",
                "BanIP is not installed",
                "medium",
                AREA,
                "banip",
                "BanIP provides automated IP blocklisting using threat feeds and rate-limiting. "
                "No BanIP configuration was found in the snapshot.",
                {},
                "Install and enable BanIP to block known malicious IPs and rate-limit ICMP/SYN/UDP traffic.",
                nist=("SC-5", "SC-7", "SI-3", "SI-4"),
                acn=("threat_detection", "network_segmentation", "risk_management"),
            )
        )
        return build_result(AREA, inventory, findings)

    if not cfg.get("enabled"):
        findings.append(
            build_finding(
                "banip-disabled",
                "BanIP is installed but not enabled",
                "medium",
                AREA,
                "banip",
                "BanIP is present in the configuration but ban_enabled is not set to 1. "
                "Threat-feed blocking and rate-limiting are inactive.",
                {"ban_enabled": cfg.get("enabled")},
                "Set banip.global.ban_enabled=1 and configure at least one threat feed to activate protection.",
                nist=("SC-5", "SC-7", "SI-3", "SI-4"),
                acn=("threat_detection", "network_segmentation", "risk_management"),
            )
        )
        return build_result(AREA, inventory, findings)

    # BanIP is enabled — check individual hardening options
    if not cfg.get("loglimit"):
        findings.append(
            build_finding(
                "banip-no-loglimit",
                "BanIP log rate limit not configured",
                "low",
                AREA,
                "banip",
                "ban_loglimit is not set. Without a log rate limit, banip may generate excessive log entries under heavy attack.",
                {},
                "Set banip.global.ban_loglimit to a reasonable value (e.g., 100) to prevent log flooding.",
                nist=("AU-9", "AU-11", "SC-5"),
                acn=("logging_monitoring", "risk_management"),
            )
        )

    rate_limits = [
        ("icmplimit", "ban_icmplimit", "ICMP"),
        ("synlimit", "ban_synlimit", "SYN"),
        ("udplimit", "ban_udplimit", "UDP"),
    ]
    for key, uci_key, proto in rate_limits:
        if not cfg.get(key):
            findings.append(
                build_finding(
                    f"banip-no-{key}",
                    f"BanIP {proto} rate limit not configured",
                    "low",
                    AREA,
                    "banip",
                    f"{uci_key} is not set. {proto} flood attacks may not be rate-limited.",
                    {},
                    f"Set banip.global.{uci_key}=1 to enable {proto} rate limiting.",
                    nist=("SC-5", "SC-7"),
                    acn=("threat_detection", "network_segmentation"),
                )
            )

    if not cfg.get("ban_feeds"):
        findings.append(
            build_finding(
                "banip-no-feeds",
                "No threat intelligence feeds configured in BanIP",
                "high",
                AREA,
                "banip",
                "BanIP is enabled but no ban_feed entries are configured. Without feeds, "
                "no IP blocklisting is active against known threat actors.",
                {},
                "Add at least one threat feed (e.g., debl, firehol1, etcompromised) via: "
                "uci add_list banip.global.ban_feed=debl",
                nist=("SC-5", "SC-7", "SI-3", "SI-4"),
                acn=("threat_detection", "risk_management"),
            )
        )

    return build_result(AREA, inventory, findings)


analyze_banip = analyze
