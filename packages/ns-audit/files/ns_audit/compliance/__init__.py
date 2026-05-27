#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""Compliance and scoring entry points for ns-audit."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from . import acn_nis2, nist_800_53r5, scoring


def build_compliance_mapping(findings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "nist_800_53r5": nist_800_53r5.map_findings(findings),
        "acn_nis2": acn_nis2.map_findings(findings),
    }


def build_summary(
    inventory: Mapping[str, Any], findings: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    return scoring.build_summary(inventory, findings)


__all__ = [
    "build_compliance_mapping",
    "build_summary",
    "nist_800_53r5",
    "acn_nis2",
    "scoring",
]
