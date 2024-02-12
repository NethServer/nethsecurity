#!/usr/bin/python

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script configures netmap firewall rules.

import subprocess
from euci import EUci
from nethsec import utils, firewall

# The changes variable is already within the scope from the caller
if 'netmap' in changes:
    subprocess.run(["/usr/sbin/ns-netmap"])
