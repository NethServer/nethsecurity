#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""ACN/NIS2 technical evidence mapping helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

try:
    from ..models import (
        ACN_NIS2_CATEGORIES,
        json_safe,
        normalize_severity,
        worst_severity,
    )
except ImportError:  # pragma: no cover - supports direct execution during development
    from ns_audit.models import (
        ACN_NIS2_CATEGORIES,
        json_safe,
        normalize_severity,
        worst_severity,
    )


def _finding_categories(finding: Mapping[str, Any]) -> list[str]:
    compliance = finding.get("compliance")
    if not isinstance(compliance, Mapping):
        return []
    categories = compliance.get("acn_nis2") or compliance.get("acn") or []
    if isinstance(categories, str):
        return [categories]
    if isinstance(categories, Sequence):
        return [str(category) for category in categories]
    return []


def map_findings(findings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Group findings by ACN/NIS2 technical category."""
    mapping: dict[str, Any] = {
        category: {
            "category": category,
            "title": title,
            "status": "no_findings",
            "severity": "info",
            "finding_count": 0,
            "findings": [],
            "note": "Technical evidence mapping; not a legal compliance determination.",
        }
        for category, title in ACN_NIS2_CATEGORIES.items()
    }
    for finding in findings:
        for category in _finding_categories(finding):
            mapping.setdefault(
                category,
                {
                    "category": category,
                    "title": ACN_NIS2_CATEGORIES.get(
                        category, category.replace("_", " ").title()
                    ),
                    "status": "no_findings",
                    "severity": "info",
                    "finding_count": 0,
                    "findings": [],
                    "note": "Technical evidence mapping; not a legal compliance determination.",
                },
            )
            item = mapping[category]
            item["status"] = "attention_required"
            item["findings"].append(
                {
                    "id": finding.get("id"),
                    "title": finding.get("title"),
                    "severity": normalize_severity(finding.get("severity")),
                    "area": finding.get("area"),
                }
            )
            item["finding_count"] = len(item["findings"])
            item["severity"] = worst_severity(
                [entry["severity"] for entry in item["findings"]]
            )
    return json_safe(mapping)


build_category_mapping = map_findings
