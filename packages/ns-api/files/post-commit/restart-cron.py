#!/usr/bin/python

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script forces cron restart

import subprocess

force_restart = False

# snort: added or removed cron job for rules download
if 'snort' in changes:
    for change in changes['firewall']:
        if 'enabled' in change:
            force_restart = True
            break

if force_restart:
    subprocess.run(["/etc/init.d", "cron", "restart"])
