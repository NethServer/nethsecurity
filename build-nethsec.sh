#!/usr/bin/env sh

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

set -e

# Source build files if it exists
set -o allexport
if [ -f build.conf ]; then
    echo "Loading build.conf file..."
    . ./build.conf
fi
set +o allexport

# Check required environment variables
OWRT_VERSION=${OWRT_VERSION:?Missing OWRT_VERSION environment variable}
NETHSECURITY_VERSION=${NETHSECURITY_VERSION:?Missing NETHSECURITY_VERSION environment variable}
REPO_CHANNEL=${REPO_CHANNEL:-dev}
TARGET=${TARGET:-x86_64}
NETIFYD_ENABLED=${NETIFYD_ENABLED:-0}
NETIFYD_ACCESS_TOKEN=${NETIFYD_ACCESS_TOKEN}

if [ -f "./key-build" ] && [ -f "./key-build.pub" ]; then
    USIGN_PRIV_KEY="$(cat ./key-build)"
    USIGN_PUB_KEY="$(cat ./key-build.pub)"
fi


podman build \
    --force-rm \
    --layers \
    --file builder/Containerfile \
    --tag nethsecurity-next \
    --target builder \
    --jobs 0 \
    --build-arg OWRT_VERSION="$OWRT_VERSION" \
    --build-arg REPO_CHANNEL="$REPO_CHANNEL" \
    --build-arg TARGET="$TARGET" \
    --build-arg NETHSECURITY_VERSION="$NETHSECURITY_VERSION" \
    --build-arg NETIFYD_ENABLED="$NETIFYD_ENABLED" \
    .

set +e

status=0
podman run \
    --env USIGN_PRIV_KEY="$USIGN_PRIV_KEY" \
    --env USIGN_PUB_KEY="$USIGN_PUB_KEY" \
    --env NETIFYD_ENABLED="$NETIFYD_ENABLED" \
    --env NETIFYD_ACCESS_TOKEN="$NETIFYD_ACCESS_TOKEN" \
    --name nethsecurity-builder \
    --interactive \
    --tty \
    --replace \
    --volume "nethsecurity_builder_${OWRT_VERSION}_build:/home/buildbot/openwrt/build_dir" \
    --volume "nethsecurity_builder_${OWRT_VERSION}_staging:/home/buildbot/openwrt/staging_dir" \
    --volume "nethsecurity_builder_${OWRT_VERSION}_cache:/home/buildbot/openwrt/.ccache" \
    --volume "nethsecurity_builder_${OWRT_VERSION}_downloads:/home/buildbot/openwrt/download" \
    --volume "nethsecurity_builder_${OWRT_VERSION}_dl:/home/buildbot/openwrt/dl" \
    nethsecurity-next \
    "$@" || status=$?

if [ $status -eq 0 ]; then
    # Clean up previous builds
    rm -rf bin
    podman cp nethsecurity-builder:/home/buildbot/openwrt/bin bin
fi

rm -rf build-logs
podman cp nethsecurity-builder:/home/buildbot/openwrt/logs build-logs
podman stop nethsecurity-builder
podman rm nethsecurity-builder

exit $status
