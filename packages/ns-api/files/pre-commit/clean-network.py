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
    mwan_interfaces = []
    for item in e_uci.get('mwan3'):
        if e_uci.get('mwan3', item) == 'interface':
            mwan_interfaces.append(item)

    for item in changes['network']:
        # if something in network has been removed
        if len(item) > 0 and item[0] == 'remove':
            to_remove_interface = item[1]
            # if the interface is configured in qosify remove it
            if to_remove_interface in qosify_interfaces:
                e_uci.delete('qosify', to_remove_interface)
            # if the interface is configured in mwan3 remove the interface
            if to_remove_interface in mwan_interfaces:
                e_uci.delete('mwan3', to_remove_interface)
                # iterate over the members of mwan3 and remove the associated member of the interface
                members_removed = []
                for entry in e_uci.get('mwan3'):
                    if e_uci.get('mwan3', entry) == 'member':
                        if to_remove_interface == e_uci.get('mwan3', entry, 'interface'):
                            e_uci.delete('mwan3', entry)
                            members_removed.append(entry)

                # iterate over the members removed and remove them from the policies
                for entry in e_uci.get('mwan3'):
                    if e_uci.get('mwan3', entry) == 'policy':
                        members = list(e_uci.get('mwan3', entry, 'use_member', default=[], dtype=str, list=True))
                        for member in members_removed:
                            if member in members:
                                members.remove(member)
                        e_uci.set('mwan3', entry, 'use_member', members)


    e_uci.save('qosify')
    e_uci.save('mwan3')
