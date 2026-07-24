#!/bin/bash

#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

#
# The container assumes the source code is mounted inside /app
#
IMAGE=ghcr.io/nethserver/nethsecurity/python3-nethsec-test
IMAGETAG=${IMAGETAG:-latest}

# Build the test image locally if it is not already available. This keeps the
# tests self-contained: no need to pull a published image or log into a
# registry, in CI or on a developer machine. Remove the image to force a
# rebuild after changing the Containerfile.
if ! podman image exists "${IMAGE}:${IMAGETAG}"; then
    "$(dirname "$0")/builder/build.sh"
fi

podman run --rm --tty --volume .:/app:Z "${IMAGE}:${IMAGETAG}"
