#!/usr/bin/env python

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# this script is supposed to be run by the 96_ns-threat_shield uci defaults
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
from nethsec import firewall, utils


def migrate_zones():
    e_uci = EUci()

    if list(e_uci.get('adblock', 'global', 'ns_tsdns_zones', list=True, default=[])):
        # already migrated
        return False

    zones = list(e_uci.get('adblock', 'global', 'adb_nftdevforce', list=True, default=[]))
    if not zones:
        return False

    if not all(firewall.zone_exists(e_uci, zone) for zone in zones):
        # the stored values are device names already, or zones that no longer exist:
        # they can't be mapped back to a selection, leave the configuration untouched
        return False

    devices = set()
    for zone in zones:
        devices.update(utils.get_all_devices_by_zone(e_uci, zone, exclude_aliases=True))

    # record the selection even when it yields no device, so the API keeps reporting
    # the zones the user picked instead of falling back to the default one
    e_uci.set('adblock', 'global', 'ns_tsdns_zones', zones)
    if devices:
        e_uci.set('adblock', 'global', 'adb_nftdevforce', sorted(devices))
    else:
        # no device in the selected zones: adblock skips the enforcement altogether
        e_uci.delete('adblock', 'global', 'adb_nftdevforce')
    e_uci.commit('adblock')
    return True


if __name__ == "__main__":
    if migrate_zones():
        subprocess.run(["/etc/init.d/adblock", "restart"], capture_output=True)
