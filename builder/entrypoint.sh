#!/usr/bin/env sh

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

set -e

if [ ! "$NETIFYD_ENABLED" -eq "0" ]; then
    echo "Netifyd is enabled, downloading sources..."
    git clone "https://oauth2:$NETIFYD_ACCESS_TOKEN@gitlab.com/netify.ai/private/nethesis/netify-flow-actions.git"
    git clone "https://oauth2:$NETIFYD_ACCESS_TOKEN@gitlab.com/netify.ai/private/nethesis/netify-agent-stats-plugin.git"
fi

if [ -n "$USIGN_PUB_KEY" ] && [ -n "$USIGN_PRIV_KEY" ]; then
    echo "$USIGN_PUB_KEY" > /home/buildbot/openwrt/key-build.pub
    echo "$USIGN_PRIV_KEY" > /home/buildbot/openwrt/key-build
else
    echo "No signing keys found. Generating dummy keys..."
    usign -G -s ./key-build -p ./key-build.pub -c "Local build key"
fi

# if command $1 is a file or a executable, run it
if which "$1" >/dev/null 2>&1; then
    exec "$@"
else
    # Otherwise, assume it's a make command and run it
    exec make -j"$(nproc)" "$@"
fi