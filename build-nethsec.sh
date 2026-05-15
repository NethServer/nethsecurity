#!/usr/bin/env sh

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

set -e

# Snapshot current environment so it can be restored with highest precedence
_env_snapshot=$(export -p)

# Source versioned defaults first
set -o allexport
if [ -f build.conf.defaults ]; then
    echo "Loading build.conf.defaults..."
    . ./build.conf.defaults
fi

# Source local overrides second (can override defaults)
if [ -f build.conf ]; then
    echo "Loading build.conf (local overrides)..."
    . ./build.conf
fi
set +o allexport

# Re-apply original environment variables so they take final precedence over config files
eval "$_env_snapshot"

# Check required environment variables
OWRT_VERSION=${OWRT_VERSION:?Missing OWRT_VERSION environment variable}
NETHSECURITY_VERSION=${NETHSECURITY_VERSION:?Missing NETHSECURITY_VERSION environment variable}
REPO_CHANNEL=${REPO_CHANNEL:-dev}
TARGET=${TARGET:-x86_64}
BUILD_SEMVER_SUFFIX=${BUILD_SEMVER_SUFFIX:-}

if [ -f "./private-key.pem" ] && [ -f "./public-key.pem" ]; then
    APK_PRIV_KEY="$(cat ./private-key.pem)"
    APK_PUB_KEY="$(cat ./public-key.pem)"
fi


podman build \
    --force-rm \
    --layers \
    --file builder/Containerfile \
    --tag nethsecurity-next \
    --jobs 0 \
    --build-arg OWRT_VERSION="$OWRT_VERSION" \
    --build-arg REPO_CHANNEL="$REPO_CHANNEL" \
    --build-arg TARGET="$TARGET" \
    --build-arg NETHSECURITY_VERSION="$NETHSECURITY_VERSION" \
    --build-arg BUILD_SEMVER_SUFFIX="$BUILD_SEMVER_SUFFIX" \
    .

set +e

status=0
podman run \
    --env APK_PRIV_KEY="$APK_PRIV_KEY" \
    --env APK_PUB_KEY="$APK_PUB_KEY" \
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
