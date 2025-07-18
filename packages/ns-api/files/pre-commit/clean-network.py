#!/usr/bin/python

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# The changes variable is already within the scope from the caller
if 'network' in changes:
    from euci import EUci

    e_uci = EUci()

    qosify_interfaces = []
    for item in e_uci.get('qosify'):
        if e_uci.get('qosify', item) == 'interface':
            qosify_interfaces.append(item)

    mwan3_entries = e_uci.get('mwan3')
    mwan_interfaces = []
    for entry in mwan3_entries:
        if e_uci.get('mwan3', entry) == 'interface':
            mwan_interfaces.append(entry)

    qosify_changed = False
    mwan_changed = False
    for item in changes['network']:
        # if something in network has been removed
        if len(item) > 0 and item[0] == 'remove':
            to_remove_interface = item[1]
            # if the interface is configured in qosify remove it
            if to_remove_interface in qosify_interfaces:
                qosify_changed = True
                e_uci.delete('qosify', to_remove_interface)
            # if the interface is configured in mwan3 remove the interface
            if to_remove_interface in mwan_interfaces:
                # fetch all configuration
                policies = []
                rules = []
                members = []
                for entry in mwan3_entries:
                    if e_uci.get('mwan3', entry) == 'policy':
                        policies.append(entry)
                    if e_uci.get('mwan3', entry) == 'rule':
                        rules.append(entry)
                    if e_uci.get('mwan3', entry) == 'member':
                        members.append(entry)

                # remove the interface from mwan3
                mwan_changed = True
                e_uci.delete('mwan3', to_remove_interface)

                # iterate over the members of mwan3 and remove the associated member of the interface
                members_removed = []
                for member in members:
                    if e_uci.get('mwan3', member, 'interface') == to_remove_interface:
                        e_uci.delete('mwan3', member)
                        members_removed.append(member)

                # iterate over the policies to see if they use the members removed
                policies_removed = []
                for policy in policies:
                    policy_members = list(e_uci.get('mwan3', policy, 'use_member', default=[], dtype=str, list=True))
                    for member in members_removed:
                        if member in policy_members:
                            policy_members.remove(member)
                    if len(policy_members) == 0:
                        e_uci.delete('mwan3', policy)
                        policies_removed.append(policy)

                # iterate over the rules to see if they use the policies removed
                for rule in rules:
                    rule_policies = list(e_uci.get('mwan3', rule, 'use_policy', default=[], dtype=str, list=True))
                    for policy in policies_removed:
                        if policy in rule_policies:
                            rule_policies.remove(policy)
                    if len(rule_policies) == 0:
                        e_uci.delete('mwan3', rule)

    if qosify_changed:
        e_uci.save('qosify')
        changes['qosify'] = {}

    if mwan_changed:
        e_uci.save('mwan3')
        changes['mwan3'] = {}
