#!/usr/bin/python

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script configures netifyd:
# - add new interfaces to internal_if and external_if options
# - disable rules for interfaces that are not in the internal_if and external_if options
# - reload netifyd service

import subprocess
from euci import EUci
from nethsec import utils, firewall

commit = False
# The changes variable is already within the scope from the caller
if 'network' in changes:
    uci = EUci()
    config = uci.get_all("netifyd")
    cname = list(config.keys())[0]
    if config[cname].get('autoconfig', '1') == "1":
        uci.set("netifyd", cname, "autoconfig", "0")
        commit = True
        
    internal_if = set()
    external_if = set()
    zones = firewall.list_zones(uci)
    for z in zones:
        zone = zones[z]
        if zone['name'] == "wan":
            external_if.update(utils.get_all_devices_by_zone(uci, zone['name'], exclude_aliases=True))
        else:
            internal_if.update(utils.get_all_devices_by_zone(uci, zone['name'], exclude_aliases=True))

    if tuple(internal_if) != uci.get("netifyd", cname, "internal_if", default=()):
        uci.set("netifyd", cname, "internal_if", list(internal_if))
        commit = True

    if tuple(external_if) != uci.get("netifyd", cname, "external_if", default=()):
        uci.set("netifyd", cname, "external_if", list(external_if))
        commit = True
    
    rules = utils.get_all_by_type(uci, 'dpi', 'rule')
    for r in rules:
        rule = rules[r]
        if rule['device'] not in internal_if and rule['device'] not in external_if:
            uci.delete("dpi", r)
            commit = True

if commit:
    uci.commit("netifyd")
    uci.commit("dpi")
    subprocess.run(["/etc/init.d/netifyd", "restart"])
