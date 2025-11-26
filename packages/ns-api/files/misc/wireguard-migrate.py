#!/usr/bin/env python

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# this script is supposed to be run by the 99-ns-api.wireguard uci defaults

import ipaddress

from euci import EUci


def migrate_old():
    e_uci = EUci()
    wireguard_sections = []
    for wg_id in e_uci.get("network"):
        if (e_uci.get("network", wg_id, "proto", dtype=str, default="") == "wireguard"
                and e_uci.get("network", wg_id, "ns_type", dtype=str, default=None) is None):
            wireguard_sections.append(wg_id)

    associations = {}
    for wg_id in wireguard_sections:
        peers = []
        for peer_id in e_uci.get("network"):
            if e_uci.get("network", peer_id, default="").endswith(wg_id):
                peers.append(peer_id)
        associations[wg_id] = peers

    for wg_id in associations:
        e_uci.set("network", wg_id, "ns_type", "server")
        for peer_id in associations[wg_id]:
            e_uci.set("network", peer_id, "ns_local_routes", e_uci.get("network", wg_id, "ns_routes", dtype=str, default=[], list=True))
            e_uci.delete("network", wg_id, "ns_routes")
            e_uci.set("network", peer_id, "ns_name", e_uci.get("network", peer_id, "description", dtype=str, default=""))
            e_uci.delete("network", peer_id, "description")
            e_uci.delete("network", peer_id, "ns_client_to_client")

    e_uci.save("network")
    e_uci.commit("network")


def fix_addresses():
    """Fix addresses without CIDR notation."""
    e_uci = EUci()
    for wg_id in e_uci.get("network"):
        if e_uci.get("network", wg_id, "proto", dtype=str, default="") == "wireguard":
            addresses = e_uci.get("network", wg_id, "addresses", dtype=str, default="", list=True)
            fixed_addresses = []
            for address in addresses:
                if "/" not in address:
                    try:
                        vpn_network = e_uci.get(
                            "network", wg_id, "ns_network", dtype=str, default=""
                        )
                        interface_network = ipaddress.IPv4Network(vpn_network)
                        first_address = str(list(interface_network.hosts())[0])
                        fixed_addresses.append(first_address + "/" + str(interface_network.prefixlen))
                    except Exception:
                        fixed_addresses.append(address)
                else:
                    fixed_addresses.append(address)
            if fixed_addresses != list(addresses):
                e_uci.set("network", wg_id, "addresses", fixed_addresses)

    e_uci.save("network")


def add_metric_to_wans():
    """
    Add metric to WAN interfaces if missing. This fixes https://github.com/NethServer/nethsecurity/issues/1428.
    This logic has been borrowed from https://github.com/NethServer/python3-nethsec/blob/ab7bfb757d602bdbba5aeb2b6e53ef0f3a36d02b/src/nethsec/mwan/__init__.py#L64.
    """
    e_uci = EUci()
    for network in e_uci.get('firewall', 'ns_wan', 'network', dtype=str, default=[], list=True):
        if e_uci.get('network', network, 'metric', default=None) is None:
            e_uci.set('network', network, 'metric', 20)

    e_uci.save('network')


if __name__ == "__main__":
    migrate_old()
    fix_addresses()
    add_metric_to_wans()
