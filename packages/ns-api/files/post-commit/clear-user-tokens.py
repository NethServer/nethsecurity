#!/usr/bin/python3

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Log out users that have been deleted or demoted from the admin role:
# remove their token store so the API server invalidates all their sessions,
# and delete their 2FA secret so they start over if they become admins again.
# Only admins (rpcd login sections) can authenticate against the API, so any
# token file or 2FA secret whose username is no longer an admin is stale and must be purged.

import glob
import os

from euci import EUci
from nethsec import users, utils

TOKENS_DIR = "/var/run/ns-api-server/tokens"
SECRETS_DIR = "/etc/ns-api-server"

# Admin role changes are tracked in the rpcd configuration.
# `changes` is injected by ns.commit when the hook is exec'd.
if "rpcd" in changes:  # noqa: F821
    u = EUci()
    admins = set()
    for login in (utils.get_all_by_type(u, "rpcd", "login") or {}).values():
        username = login.get("username")
        if username:
            admins.add(username)

    if os.path.isdir(TOKENS_DIR):
        for token_file in glob.glob(os.path.join(TOKENS_DIR, "*")):
            username = os.path.basename(token_file)
            if username not in admins:
                try:
                    os.remove(token_file)
                except OSError:
                    pass

    if os.path.isdir(SECRETS_DIR):
        for username in os.listdir(SECRETS_DIR):
            if username not in admins:
                users.delete_2fa(username)
