#!/usr/bin/python

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# This script configures banip wans:
# it sets ban_ifv4, ban_ifv6, ban_dev and ban_trigger

from euci import EUci
from nethsec import utils

save = False
# The changes variable is already within the scope from the caller
if 'network' in changes or 'banip' in changes:
    uci = EUci()
    devices = []
    interfaces = []

    if uci.get("banip", "global", "ban_autodetect", default="1") == "1":
        uci.set("banip", "global", "ban_autodetect", "0")
        save = True

    devices = utils.get_all_wan_devices(uci, exclude_aliases=True)
    for d in devices:
        interfaces.append(utils.get_interface_from_device(uci, d))

    for opt in ('ban_ifv4', 'ban_ifv6', 'ban_trigger'):
        if tuple(interfaces) != uci.get("banip", "global", opt, default=()):
            uci.set("banip", "global", opt, list(interfaces))
            save = True

    if tuple(devices) != uci.get("banip", "global", "ban_dev", default=()):
        uci.set("banip", "global", "ban_dev", list(devices))
        save = True

if save:
    if 'banip' in changes:
        # the commit on banip database  will already done later by the system
        uci.save("banip")
    else:
        # make sure to commit banip db when there were changes only to network db
        uci.commit("banip")
