#!/usr/bin/python3

#
# Copyright (C) 2023 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

'''
IPSec utilities
'''

import os
from nethsec import utils, firewall

IPSEC_ZONE='ipsec'

def init_ipsec(uci):
    '''
    Initialize IPSec global configuration, if needed.

    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
    '''
    # Make sure the config file exists
    conf = os.path.join(uci.confdir(), 'ipsec')
    if not os.path.isfile(conf):
        with open(conf, 'a'):
            pass

        # Setup global options
        gsettings = utils.get_id("ipsec_global")
        uci.set("ipsec", gsettings, IPSEC_ZONE)
        uci.set("ipsec", gsettings, "debug", '0')
        uci.set("ipsec", gsettings, "zone", 'ipsec')
        uci.commit('ipsec')

def open_firewall_ports(uci):
    '''
    Open firewall ports for IPSec tunnels, if need.

    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
    '''
    esp_accepted = False
    ike_accepted = False
    nat_accepted = False
    esp = {"src": "wan", "dest_port": "", "proto": "esp", "target": "ACCEPT"}
    ike = {"src": "wan", "dest_port": "500", "proto": "udp", "target": "ACCEPT"}
    nat = {"src": "wan", "dest_port": "4500", "proto": "udp", "target": "ACCEPT"}
    # search for existing rules
    for r in utils.get_all_by_type(uci, 'firewall', 'rule'):
        tmp = dict()
        for opt in ['src', 'dest', 'dest_port', 'proto', 'target']:
              tmp[opt] = uci.get('firewall', r, opt, default='')
        # check if tmp is the esp rule
        if all((tmp.get(k) == v for k, v in esp.items())):
            esp_accepted = True
        # check if tmp is the ike rule
        if all((tmp.get(k) == v for k, v in ike.items())):
            ike_accepted = True
        # check if tmp is the nat rule
        if all((tmp.get(k) == v for k, v in nat.items())):
            nat_accepted = True

    if not ike_accepted:
        firewall.add_template_rule(uci, 'ns_ipsec_ike')

    if not esp_accepted:
        firewall.add_template_rule(uci, 'ns_ipsec_esp')
 
    if not nat_accepted:
        firewall.add_template_rule(uci, 'ns_ipsec_nat')

    if not nat_accepted or not ike_accepted or not esp_accepted:
        uci.save('firewall')

def add_trusted_interface(uci, interface):
    '''
    Add the interface to the 'ipsec' trusted zone. The function also creates the trusted zone, if needed.

    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
    '''
    if firewall.zone_exists(uci, IPSEC_ZONE):
        firewall.add_interface_to_zone(uci, interface, IPSEC_ZONE)
    else:
        firewall.add_trusted_zone(uci, IPSEC_ZONE, [interface])
