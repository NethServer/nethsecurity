#!/usr/bin/python

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script configures netmap firewall rules.

import subprocess

# The changes variable is already within the scope from the caller
if 'netmap' in changes:
    # force firewall reload: fw4 does not reload if there any changes in /usr/share/nftables.d
    subprocess.run(["/etc/init.d/firewall", "reload"])
