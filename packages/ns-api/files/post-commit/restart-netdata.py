#!/usr/bin/python

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script restarts netdata is a WAN has changed to update the multiwan chart.

import subprocess

# The changes variable is already within the scope from the caller
if 'mwan3' in changes:
    subprocess.run(["/etc/init.d/netdata", "restart"])
