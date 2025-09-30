#!/usr/bin/python

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# this script reloads wireguard interfaces if configuration has changed

import subprocess

if 'network' in changes:
    interfaces_to_restart = []
    for entry in changes['network']:
        if entry[1].startswith('wg'):
            interfaces_to_restart.append(entry[1][:3])
    for item in set(interfaces_to_restart):
        print('restarting interface', item)
        subprocess.call(f'ifdown {item} ; ifup {item}', shell=True)
