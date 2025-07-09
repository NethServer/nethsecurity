#!/usr/bin/env sh

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

set -e

# Clean up previous builds
rm -rf bin
rm -rf build-logs

podman build \
    --force-rm \
    --layers \
    --file builder/Containerfile \
    --tag nethsecurity-next \
    --build-arg-file build.conf \
    .

set +e

if [ -f "key-build.pub" ] && [ -f "key-build" ]; then
    USIGN_PUB_KEY=$(cat key-build.pub)
    USIGN_PRIV_KEY=$(cat key-build)
elif [ -n "$USIGN_PUB_KEY" ] && [ -n "$USIGN_PRIV_KEY" ]; then
    echo "Using provided USIGN keys."
fi

status=0
podman run \
    --name nethsecurity-builder \
    --interactive \
    --tty \
    --replace \
    --env-file build.conf \
    --env USIGN_PUB_KEY \
    --env USIGN_PRIV_KEY \
    --volume nethsecurity_builder_build:/home/buildbot/openwrt/build_dir \
    --volume nethsecurity_builder_cache:/home/buildbot/openwrt/.ccache \
    --volume nethsecurity_builder_dl:/home/buildbot/openwrt/dl \
    --volume nethsecurity_builder_downloads:/home/buildbot/openwrt/download \
    --volume nethsecurity_builder_staging:/home/buildbot/openwrt/staging_dir \
    nethsecurity-next \
    "$@" || status=$?

podman cp nethsecurity-builder:/home/buildbot/openwrt/logs build-logs
podman cp nethsecurity-builder:/home/buildbot/openwrt/bin bin
podman stop nethsecurity-builder
podman rm nethsecurity-builder

exit $status
