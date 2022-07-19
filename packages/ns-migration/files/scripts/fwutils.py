#!/usr/bin/python3

#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

import re
import sys
import json
import argparse
import subprocess
from glob import glob
from euci import EUci

# Retrieve the physical device name given the MAC address
def get_device_name(hwaddr):
    interfaces = json.loads(subprocess.run(["/sbin/ip", "--json", "address", "show"], check=True, capture_output=True).stdout)
    for interface in interfaces:
        if interface["address"] == hwaddr:
            return interface["ifname"]

    return None

# Retrieve the logical UCI interface name given the MAC address
def get_interface_name(uci, hwaddr):
    name = get_device_name(hwaddr)
    for section in uci.get("network"):
        if  uci.get("network", section) == "interface" and (uci.get("network", section, "device") == name):
            return section

    return None

# Replace illegal chars with _
# UCI identifiers and config file names may contain only the characters a-z, 0-9 and _
def sanitize(name):
    name = re.sub(r'[^\x00-\x7F]+','_', name)
    name = re.sub('[^0-9a-zA-Z]', '_', name)
    return name

# Global print function
vprint = print

#
# Parse command line arguments, initialize UCI and read export file
# Return a tuple of:
#  - euci pointer
#  - hash of parsed export data
#
def init(data_file):
    global vprint

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Import network and basic firewall configuration")
    parser.add_argument("--quiet", "-q", action="store_true", help="don't print executed actions to stdout")
    parser.add_argument("export_dir", nargs=1, help="export directory with uncompressed files")
    args = parser.parse_args()

    # Define print as an empty function if 'quiet' options is enabled
    vprint = print if not args.quiet else lambda *a, **k: None

    # Initialize UCI pointer
    u = EUci()

    # Read NS7 network configurations
    f = open(f'{args.export_dir[0]}/{data_file}')
    data = json.load(f)
    f.close()

    return (u, data)
