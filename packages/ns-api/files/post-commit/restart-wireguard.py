#!/usr/bin/python

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# this script reloads wireguard interfaces if configuration has changed

import subprocess
from euci import EUci

if 'network' in changes:
    e_uci = EUci()
    for item in e_uci.get('network'):
        if e_uci.get('network', item, 'proto') == 'wireguard':
            subprocess.call(f'ifdown {item} ; ifup {item}', shell=True)
