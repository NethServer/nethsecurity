#!/usr/bin/python

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script makes sure the status of banip service corresponds to the configured one

import subprocess
from euci import EUci

# The changes variable is already within the scope from the caller
if 'banip' in changes:
    uci = EUci()
    enabled = uci.get('banip', 'global', 'ban_enabled', default='0')
    try:
        subprocess.run(["/etc/init.d/banip", "running"], check=True)
        running = True
    except:
        running = False

    if running and not enabled:
        subprocess.run(["/etc/init.d/banip", "stop"])
    if not running and enabled:
        subprocess.run(["/etc/init.d/banip", "start"])
