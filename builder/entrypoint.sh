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

# if command $1 is a file or a executable, run it
if [ -f "$1" ] && [ -x "$1" ]; then
    exec "$@"
else
    # Otherwise, assume it's a make command and run it 
    if [ -n "$USIGN_PUB_KEY" ] && [ -n "$USIGN_PRIV_KEY" ]; then
        echo "$USIGN_PUB_KEY" > /home/buildbot/openwrt/key-build.pub
        echo "$USIGN_PRIV_KEY" > /home/buildbot/openwrt/key-build
    elif [ ! -f key-build.pub ] && [ ! -f key-build ] && [ -f ./staging_dir/host/bin/usign ]; then
        ./staging_dir/host/bin/usign -G -s ./key-build -p ./key-build.pub -c "Local build key"
    else 
        echo "No signing keys found. Please provide USIGN_PUB_KEY and USIGN_PRIV_KEY environment variables or place key-build.pub and key-build in the current directory."
        exit 1
    fi

    exec make -j"$(nproc)" "$@"
fi