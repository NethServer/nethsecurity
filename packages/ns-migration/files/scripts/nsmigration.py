#!/usr/bin/python3

#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

import json
import argparse
from euci import EUci

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
