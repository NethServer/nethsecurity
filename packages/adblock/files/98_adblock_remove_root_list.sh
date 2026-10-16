#!/bin/sh

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Remove the blocklist wrongly written to the root filesystem when the dnsmasq
# directory could not be determined (see NethServer/nethsecurity#1940).
# dnsmasq never reads this file, adblock is (re)started anyway after this script
# by the package postinst or by the boot sequence.
rm -f /adb_list.overall

exit 0
