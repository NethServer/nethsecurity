#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from __future__ import annotations

from ns_audit.collectors.commands import command_exists, run_command
from ns_audit.config import UCI_PACKAGES


def collect_uci_packages() -> dict[str, object]:
    if not command_exists("uci"):
        return {"available": False, "error": "command_not_found", "packages": {}}

    return {
        "available": True,
        "packages": {
            package: run_command(
                ("uci", "-q", "show", package), name=f"uci_show_{package}"
            )
            for package in UCI_PACKAGES
        },
    }
