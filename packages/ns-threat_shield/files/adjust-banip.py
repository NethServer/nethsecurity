#!/usr/bin/python

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script makes sure the status of banip service corresponds to the configured one

import os
import subprocess
from euci import EUci

# The changes variable is already within the scope from the caller
if 'banip' in changes or 'network' in changes:

    # banIP start restores lists from backups: drop the changed ones to force a download
    stale = []

    # if ban_country property was modified, remove stale backup files to prevent old country selections from being restored
    if 'banip' in changes and any('ban_country' in op for op in changes['banip']):
        stale += ['country.v4', 'country.v6']

    # rebuild custom feeds and ban_allowurl from UCI before banIP (re)starts
    if 'banip' in changes:
        allow_before = EUci().get('banip', 'global', 'ban_allowurl', list=True, default=[])
        subprocess.run(["/usr/sbin/ts-ip"])
        # new instance: EUci caches loaded configs and would miss what ts-ip committed
        uci = EUci()
        if allow_before != uci.get('banip', 'global', 'ban_allowurl', list=True, default=[]):
            stale.append('allowlist')
        for op in changes['banip']:
            # ns_blockfeed sections whose url_4/url_6 changed: drop that family's backup
            if len(op) > 2 and op[0] == 'set' and op[2] in ('url_4', 'url_6') and str(op[1]).isalnum() and uci.get('banip', op[1], default='') == 'ns_blockfeed':
                stale.append(f'{op[1]}.v{op[2][-1]}')

    for name in stale:
        try:
            os.remove(f'/tmp/banIP-backup/banIP.{name}.gz')
        except FileNotFoundError:
            pass
    
    uci = EUci()
    enabled = uci.get('banip', 'global', 'ban_enabled', default='0')
    try:
        subprocess.run(["/etc/init.d/banip", "running"], check=True)
        running = True
    except:
        running = False

    if running and not enabled:
        subprocess.run(["/etc/init.d/banip", "stop"])
    elif not running and enabled:
        subprocess.run(["/etc/init.d/banip", "start"])
    else:
        # force nft rules reload for wan changes
        # a restart is not good because sometimes banip
        # service executes a reload and not a real restart
        subprocess.run(["/etc/init.d/banip", "stop"])
        subprocess.run(["/etc/init.d/banip", "start"])
