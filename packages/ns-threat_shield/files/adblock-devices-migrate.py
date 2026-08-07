#!/usr/bin/env python

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# this script is supposed to be run by the 36_ns-threat_shield uci defaults
#
# Up to adblock 4.1.5 the local DNS enforcement was configured through adb_zonelist,
# holding firewall zone names, and adblock turned it into uci redirect sections
# letting fw4 resolve the zones. Since 4.5.5 the enforcement is rendered as nft rules
# matching on iifname, so adb_nftdevforce needs device names: the zone names stored
# there produce rules that never match and DNS traffic is no longer redirected.
#
# Move the selection to ns_tsdns_zones and rebuild adb_nftdevforce out of it.

import subprocess

from euci import EUci
from nethsec import utils


def migrate_zones():
    e_uci = EUci()

    if list(e_uci.get('adblock', 'global', 'ns_tsdns_zones', list=True, default=[])):
        # already migrated
        return False

    zones = list(e_uci.get('adblock', 'global', 'adb_nftdevforce', list=True, default=[]))
    if not zones:
        return False

    devices = []
    for zone in zones:
        for device in utils.get_all_devices_by_zone(e_uci, zone, exclude_aliases=True):
            if device not in devices:
                devices.append(device)

    if not devices:
        # the stored values are not zone names, or the zones have no interface:
        # leave the configuration untouched rather than clearing it
        return False

    e_uci.set('adblock', 'global', 'ns_tsdns_zones', zones)
    e_uci.set('adblock', 'global', 'adb_nftdevforce', sorted(devices))
    e_uci.commit('adblock')
    return True


if __name__ == "__main__":
    if migrate_zones():
        subprocess.run(["/etc/init.d/adblock", "restart"], capture_output=True)
