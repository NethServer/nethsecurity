#!/usr/bin/python

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script writes the netifyd address groups of the firewall objects once their changes are committed:
# one file per object resolving to addresses, the ones of objects that are gone removed, and netifyd
# reloaded when a file changed. DPI rules match an object through its group.

from euci import EUci
from nethsec import objects

if "objects" in changes or "dhcp" in changes or "users" in changes:  # noqa: F821
    objects.update_address_groups(EUci())
