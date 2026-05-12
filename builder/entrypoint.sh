#!/usr/bin/env sh

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

set -e

if [ -n "$APK_PRIV_KEY" ] && [ -n "$APK_PUB_KEY" ]; then
    echo "$APK_PRIV_KEY" > /home/buildbot/openwrt/private-key.pem
    echo "$APK_PUB_KEY" > /home/buildbot/openwrt/public-key.pem
fi

# if command $1 is a file or a executable, run it
if which "$1" >/dev/null 2>&1; then
    exec "$@"
else
    # Otherwise, assume it's a make command and run it
    exec make -j"$(nproc)" V=sc "$@"
fi
