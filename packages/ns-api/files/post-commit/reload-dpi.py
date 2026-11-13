#!/usr/bin/python

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script reloads the DPI when an object referenced by a DPI rule source may have changed:
# the address group of every referenced object is regenerated from the committed configuration.
# reload_config can't do it, as it reloads dpi only when /etc/config/dpi itself changes.

import subprocess

from euci import EUci
from nethsec import utils

# A change to dpi itself is left to reload_config, which reloads the service anyway.
if "dpi" not in changes and ("objects" in changes or "users" in changes or "dhcp" in changes):  # noqa: F821
    for rule in (utils.get_all_by_type(EUci(), "dpi", "rule") or {}).values():
        if rule.get("source_object"):
            subprocess.run(["/etc/init.d/dpi", "reload"], check=False)
            break
