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

# Check required environment variables, override .env variables if set
OWRT_VERSION=${OWRT_VERSION:?Missing OWRT_VERSION environment variable}
NETHSECURITY_VERSION=${NETHSECURITY_VERSION:?Missing NETHSECURITY_VERSION environment variable}
REPO_CHANNEL=${REPO_CHANNEL:-dev}
TARGET=${TARGET:-x86_64}
NETIFYD_ENABLED=${NETIFYD_ENABLED:-0}
NETIFYD_ACCESS_TOKEN=${NETIFYD_ACCESS_TOKEN}

if [ -z "$USIGN_PRIV_KEY" ] || [ -z "$USIGN_PUB_KEY" ]; then
    USIGN_PRIV_KEY="$(cat ./build-sign-key)"
    USIGN_PUB_KEY="$(cat ./build-sign-key.pub)"
fi

# Clean up previous builds
rm -rf bin
rm -rf build-logs

podman build \
    --force-rm \
    --layers \
    --file builder/Containerfile \
    --tag nethsecurity-next \
    --build-arg OWRT_VERSION="$OWRT_VERSION" \
    --build-arg REPO_CHANNEL="$REPO_CHANNEL" \
    --build-arg TARGET="$TARGET" \
    --build-arg NETHSECURITY_VERSION="$NETHSECURITY_VERSION" \
    --build-arg NETIFYD_ENABLED="$NETIFYD_ENABLED" \
    .

set +e

status=0
podman run \
    --env OWRT_VERSION="$OWRT_VERSION" \
    --env REPO_CHANNEL="$REPO_CHANNEL" \
    --env NETHSECURITY_VERSION="$NETHSECURITY_VERSION" \
    --env TARGET="$TARGET" \
    --env USIGN_PRIV_KEY="$USIGN_PRIV_KEY" \
    --env USIGN_PUB_KEY="$USIGN_PUB_KEY" \
    --env NETIFYD_ENABLED="$NETIFYD_ENABLED" \
    --env NETIFYD_ACCESS_TOKEN="$NETIFYD_ACCESS_TOKEN" \
    --name nethsecurity-builder \
    --interactive \
    --tty \
    --replace \
    --volume nethsecurity_builder_build:/home/buildbot/openwrt/build_dir \
    --volume nethsecurity_builder_staging:/home/buildbot/openwrt/staging_dir \
    --volume nethsecurity_builder_cache:/home/buildbot/openwrt/.ccache \
    --volume nethsecurity_builder_downloads:/home/buildbot/openwrt/download \
    --volume nethsecurity_builder_dl:/home/buildbot/openwrt/dl \
    nethsecurity-next \
    "$@" || status=$?

podman cp nethsecurity-builder:/home/buildbot/openwrt/logs build-logs
podman cp nethsecurity-builder:/home/buildbot/openwrt/bin bin
podman stop nethsecurity-builder
podman rm nethsecurity-builder

exit $status
