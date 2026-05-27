#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""Reporting helpers for the on-device NethSecurity audit tool."""

__all__ = [
    "DEFAULT_BUNDLE_NAME",
    "DEFAULT_OUTPUT_NAME",
    "EXPECTED_JSON_ARTIFACTS",
    "build_log_artifacts",
    "build_report_context",
    "bundle_report_artifacts",
    "find_secret_pattern_matches",
    "load_json_artifact",
    "materialize_log_artifacts",
    "render_report",
    "sanitize_log_artifacts",
]


def __getattr__(name):
    if name in __all__:
        from . import html

        return getattr(html, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
