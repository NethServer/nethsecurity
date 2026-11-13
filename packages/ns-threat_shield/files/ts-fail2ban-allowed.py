#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# fail2ban ignorecommand: exit 0 if the IP is in a banIP allowlist set, 1 otherwise

import ipaddress
import json
import subprocess
import sys


def allowed(ip):
    # list only this set: "nft get element" would load every set, blocklists included
    result = subprocess.run(
        ["nft", "-j", "list", "set", "inet", "banIP", f"allowlist.v{ip.version}"],
        capture_output=True,
        timeout=10,
    )
    for item in json.loads(result.stdout)["nftables"]:
        for elem in item.get("set", {}).get("elem", []):
            # elements with counters are wrapped in {"elem": {"val": ...}}
            if isinstance(elem, dict) and "elem" in elem:
                elem = elem["elem"]["val"]
            if isinstance(elem, str):
                if ip == ipaddress.ip_address(elem):
                    return True
            elif "prefix" in elem:
                prefix = elem["prefix"]
                if ip in ipaddress.ip_network(f"{prefix['addr']}/{prefix['len']}"):
                    return True
            elif "range" in elem:
                first, last = elem["range"]
                if ipaddress.ip_address(first) <= ip <= ipaddress.ip_address(last):
                    return True
    return False


def main():
    try:
        sys.exit(0 if allowed(ipaddress.ip_address(sys.argv[1])) else 1)
    except Exception:
        # missing set, bad input or nft error: not allowlisted
        sys.exit(1)


if __name__ == "__main__":
    main()
