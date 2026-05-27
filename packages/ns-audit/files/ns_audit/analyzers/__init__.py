#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""Normalization and analysis entry points for ns-audit."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from ..compliance import build_compliance_mapping, build_summary
    from ..models import json_safe, severity_counts
except ImportError:  # pragma: no cover - supports direct execution during development
    from ns_audit.compliance import build_compliance_mapping, build_summary
    from ns_audit.models import json_safe, severity_counts

from . import (
    api_audit,
    banip,
    firewall,
    identity,
    ips,
    logging as logging_analyzer,
    telemetry,
    updates,
    vpn,
)

ANALYZERS = (identity, firewall, vpn, ips, logging_analyzer, telemetry, api_audit, banip, updates)


def analyze_snapshot(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Analyze a sanitized raw snapshot and return all JSON report structures."""
    inventory: dict[str, Any] = {}
    findings: list[dict[str, Any]] = []
    area_summaries: dict[str, Any] = {}
    for analyzer in ANALYZERS:
        result = analyzer.analyze(raw_snapshot)
        result_inventory = (
            result.get("inventory", {}) if isinstance(result, Mapping) else {}
        )
        result_findings = (
            result.get("findings", []) if isinstance(result, Mapping) else []
        )
        result_summary = (
            result.get("summary", {}) if isinstance(result, Mapping) else {}
        )
        if isinstance(result_inventory, Mapping):
            inventory.update(result_inventory)
        if isinstance(result_findings, list):
            findings.extend(result_findings)
        if isinstance(result_summary, Mapping):
            area_summaries.update(result_summary)
    compliance_mapping = build_compliance_mapping(findings)
    summary = build_summary(inventory, findings)
    summary["area_summaries"] = area_summaries
    return json_safe(
        {
            "inventory": inventory,
            "findings": findings,
            "summary": summary,
            "compliance_mapping": compliance_mapping,
            "compliance": compliance_mapping,
        }
    )


def build_analysis_outputs(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Return structures suitable for inventory/findings/summary/compliance JSON files."""
    analysis = analyze_snapshot(raw_snapshot)
    findings = analysis["findings"]
    return json_safe(
        {
            "inventory": analysis["inventory"],
            "findings": {
                "findings": findings,
                "finding_counts": severity_counts(findings),
                "finding_count": len(findings),
            },
            "summary": analysis["summary"],
            "compliance_mapping": analysis["compliance_mapping"],
        }
    )


analyze = analyze_snapshot
__all__ = ["analyze", "analyze_snapshot", "build_analysis_outputs"]
