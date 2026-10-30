#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Regenerate fail2ban jails and ignore list when related configurations change

import subprocess

# `changes` is injected by ns.commit when the hook is exec'd
if changes.keys() & {"banip", "network", "firewall"}:
    subprocess.run(["/usr/libexec/ts-fail2ban"])
