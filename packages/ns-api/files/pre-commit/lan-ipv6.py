#!/usr/bin/python

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script is used to set the ip6assign to 64 for all the networks in the lan firewall zone
# This is required to enable IPv6 on the network interfaces when DHCPv6 is used

import sys
import json
from euci import EUci
from nethsec import firewall, utils


save = False
# The changes variable is already within the scope from the caller
if 'network' in changes:
    e_uci = EUci()
    if not firewall.is_ipv6_enabled(e_uci):
        sys.exit(0)
    for zone in utils.get_all_by_type(e_uci, 'firewall', 'zone'):
        if e_uci.get('firewall', zone, 'name', default='') == 'lan':
            try:
                networks = e_uci.get_all('firewall', zone, 'network')
            except:
                continue
            for network in networks:
                try:
                    e_uci.get('network', network, 'ip6assign')
                except:
                    save = True
                    e_uci.set('network', network, 'ip6assign', '64')

if save:
    e_uci.save('network')
