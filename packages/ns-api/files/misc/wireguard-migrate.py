#!/usr/bin/env python

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# this script is supposed to be run by the 99-ns-api.wireguard uci defaults

from euci import EUci


def main():
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


if __name__ == "__main__":
    main()
