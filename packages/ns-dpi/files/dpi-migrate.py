#!/usr/bin/env python3

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# this script is supposed to be run by the 21_dpi_migrate uci-defaults

from euci import EUci
from nethsec import dpi

dpi.migrate_schema(EUci())
