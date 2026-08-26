#!/usr/bin/python

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script keeps the adblock local DNS enforcement aligned with the network setup:
# adb_nftdevforce is rendered as an nft iifname match, so it must list the devices of
# the zones selected in ns_tsdns_zones. Without this, adding an interface to an
# enforced zone would silently leave its DNS traffic unfiltered.

# The changes variable is already within the scope from the caller
if 'adblock' in changes or 'firewall' in changes or 'network' in changes:
    import syslog
    from euci import EUci
    from nethsec import utils

    uci = EUci()
    zones = list(uci.get('adblock', 'global', 'ns_tsdns_zones', list=True, default=[]))

    if zones:
        devices = set()
        for zone in zones:
            devices.update(utils.get_all_devices_by_zone(uci, zone, exclude_aliases=True))
        # keep a stable order, the value is compared before being rewritten
        devices = sorted(devices)

        current = list(uci.get('adblock', 'global', 'adb_nftdevforce', list=True, default=[]))
        if devices != current:
            if devices:
                uci.set('adblock', 'global', 'adb_nftdevforce', devices)
            else:
                uci.delete('adblock', 'global', 'adb_nftdevforce')
            uci.save('adblock')
            # adblock is reloaded by the uci reload_config at the end of the commit
            if 'adblock' not in changes:
                changes['adblock'] = {}
