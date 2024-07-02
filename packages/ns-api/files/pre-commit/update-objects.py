#!/usr/bin/python

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script updates firewall configuration if an object has been updated.
# It updates the following:
# - input/output/forward firewall rules
# - redirects rules (port forward)


import sys
from euci import EUci
from nethsec import firewall

need_update = False
# The changes variable is already within the scope from the caller
for db in ['objects', 'users', 'dhcp']:
    if db in changes:
        need_update = True
        break
if need_update:
    e_uci = EUci()
    firewall.update_firewall_rules(e_uci)
    firewall.update_redirect_rules(e_uci)
    # If the firewall configuration does not have change,
    # this hook must force the commit to update all existing rules
    if not 'firewall' in changes:
        changes["firewall"] = []
