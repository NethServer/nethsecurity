#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""Weighted scoring for the NethSecurity audit report."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

try:
    from ..models import (
        AREA_TITLES,
        AREA_WEIGHTS,
        json_safe,
        normalize_severity,
        severity_counts,
    )
except ImportError:  # pragma: no cover - supports direct execution during development
    from ns_audit.models import (
        AREA_TITLES,
        AREA_WEIGHTS,
        json_safe,
        normalize_severity,
        severity_counts,
    )

DEDUCTION_FACTOR = {
    "critical": 0.45,
    "high": 0.30,
    "medium": 0.15,
    "low": 0.05,
    "info": 0.0,
}


def _inventory_counts(inventory: Mapping[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for area, value in inventory.items():
        if isinstance(value, Mapping):
            total = 0
            for item in value.values():
                total += (
                    len(item)
                    if isinstance(item, Sequence)
                    and not isinstance(item, str | bytes | bytearray)
                    else 1
                )
            counts[str(area)] = total
        elif isinstance(value, Sequence) and not isinstance(
            value, str | bytes | bytearray
        ):
            counts[str(area)] = len(value)
        else:
            counts[str(area)] = 1 if value else 0
    return counts


def calculate_area_scores(findings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    area_scores: dict[str, Any] = {}
    for area, weight in AREA_WEIGHTS.items():
        area_findings = [
            finding
            for finding in findings
            if finding.get("score_area", finding.get("area")) == area
        ]
        deductions = []
        deduction_total = 0.0
        for finding in area_findings:
            severity = normalize_severity(finding.get("severity"))
            points = round(weight * DEDUCTION_FACTOR[severity], 2)
            deduction_total += points
            deductions.append(
                {
                    "finding_id": finding.get("id"),
                    "severity": severity,
                    "points": points,
                }
            )
        capped_deduction = min(float(weight), deduction_total)
        earned = round(max(0.0, float(weight) - capped_deduction), 2)
        percent = round((earned / float(weight)) * 100) if weight else 100
        counts = severity_counts(area_findings)
        status = (
            "red"
            if counts["critical"] or counts["high"]
            else "yellow"
            if counts["medium"]
            else "green"
        )
        area_scores[area] = {
            "title": AREA_TITLES.get(area, area.title()),
            "weight": weight,
            "earned_points": earned,
            "deducted_points": round(capped_deduction, 2),
            "raw_deducted_points": round(deduction_total, 2),
            "score": percent,
            "status": status,
            "finding_counts": counts,
            "deductions": deductions,
        }
    return json_safe(area_scores)


def build_summary(
    inventory: Mapping[str, Any], findings: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Build a weighted, JSON-serializable summary from inventory and findings."""
    area_scores = calculate_area_scores(findings)
    total_weight = sum(item["weight"] for item in area_scores.values())
    earned_points = sum(item["earned_points"] for item in area_scores.values())
    overall_score = round((earned_points / total_weight) * 100) if total_weight else 100
    counts = severity_counts(findings)
    status = (
        "red"
        if counts["critical"] or counts["high"]
        else "yellow"
        if counts["medium"]
        else "green"
    )
    top_findings = sorted(
        findings,
        key=lambda finding: (finding.get("risk_score", 0), str(finding.get("id"))),
        reverse=True,
    )[:10]
    return json_safe(
        {
            "overall_score": overall_score,
            "status": status,
            "weighted_points": {
                "earned": round(earned_points, 2),
                "available": total_weight,
            },
            "area_scores": area_scores,
            "finding_counts": counts,
            "finding_count": sum(counts.values()),
            "inventory_counts": _inventory_counts(inventory),
            "top_findings": [
                {
                    "id": finding.get("id"),
                    "title": finding.get("title"),
                    "severity": finding.get("severity"),
                    "area": finding.get("area"),
                    "remediation": finding.get("remediation"),
                }
                for finding in top_findings
            ],
            "scoring_model": {
                "weights": AREA_WEIGHTS,
                "deduction_factor": DEDUCTION_FACTOR,
                "note": "Telemetry findings are scored inside the logging and audit trail area.",
            },
        }
    )


summarize = build_summary
