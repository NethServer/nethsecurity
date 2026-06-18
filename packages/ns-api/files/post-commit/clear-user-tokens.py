#!/usr/bin/python3

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Log out users that have been deleted or demoted from the admin role:
# remove their token store so the API server invalidates all their sessions.
# Only admins (rpcd login sections) can authenticate against the API, so any
# token file whose username is no longer an admin is stale and must be purged.

import glob
import os

from euci import EUci
from nethsec import utils

TOKENS_DIR = "/var/run/ns-api-server/tokens"

# Admin role changes are tracked in the rpcd configuration.
# `changes` is injected by ns.commit when the hook is exec'd.
if "rpcd" in changes and os.path.isdir(TOKENS_DIR):  # noqa: F821
    u = EUci()
    admins = set()
    for login in (utils.get_all_by_type(u, "rpcd", "login") or {}).values():
        username = login.get("username")
        if username:
            admins.add(username)

    for token_file in glob.glob(os.path.join(TOKENS_DIR, "*")):
        username = os.path.basename(token_file)
        if username not in admins:
            try:
                os.remove(token_file)
            except OSError:
                pass
