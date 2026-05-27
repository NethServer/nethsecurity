#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""NIST SP 800-53 revision 5 compliance mapping helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

try:
    from ..models import NIST_CONTROLS, json_safe, normalize_severity, worst_severity
except ImportError:  # pragma: no cover - supports direct execution during development
    from ns_audit.models import (
        NIST_CONTROLS,
        json_safe,
        normalize_severity,
        worst_severity,
    )


def _finding_controls(finding: Mapping[str, Any]) -> list[str]:
    compliance = finding.get("compliance")
    if not isinstance(compliance, Mapping):
        return []
    controls = compliance.get("nist_800_53r5") or compliance.get("nist") or []
    if isinstance(controls, str):
        return [controls]
    if isinstance(controls, Sequence):
        return [str(control) for control in controls]
    return []


def map_findings(findings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Group findings by NIST SP 800-53r5 control."""
    mapping: dict[str, Any] = {
        control: {
            "control": control,
            "title": title,
            "status": "no_findings",
            "severity": "info",
            "finding_count": 0,
            "findings": [],
        }
        for control, title in NIST_CONTROLS.items()
    }
    for finding in findings:
        for control in _finding_controls(finding):
            mapping.setdefault(
                control,
                {
                    "control": control,
                    "title": NIST_CONTROLS.get(control, "NIST SP 800-53r5 control"),
                    "status": "no_findings",
                    "severity": "info",
                    "finding_count": 0,
                    "findings": [],
                },
            )
            item = mapping[control]
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


build_control_mapping = map_findings
