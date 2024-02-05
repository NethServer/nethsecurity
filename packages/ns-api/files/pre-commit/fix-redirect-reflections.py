#!/usr/bin/python

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script is used to remove non-existing zones from port forwards (redirects)
# that uses such zone as reflection zone

import sys
from euci import EUci
from nethsec import firewall, utils


save = False
# The changes variable is already within the scope from the caller
if 'firewall' in changes:
    e_uci = EUci()
    for pf in  utils.get_all_by_type(e_uci, 'firewall', 'redirect'):
        try:
            zones = e_uci.get_all('firewall', pf, 'reflection_zone')
        except Exception as e:
            continue
        to_remove = []
        for zone in zones:
            zid, zname = firewall.get_zone_by_name(e_uci, zone)
            if zid is None:
                to_remove.append(zone)
        if to_remove:
            zones = list(zones)
            save = True
            for zone in to_remove:
                zones.remove(zone)
            e_uci.set('firewall', pf, 'reflection_zone', zones)

if save:
    e_uci.save('firewall')
