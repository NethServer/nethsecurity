#!/bin/bash

#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

#
# The container assumes the source code is mounted inside /app
#
IMAGE=python3-nethsec-test

set -e

# Always rebuild from the Containerfile: podman's layer cache makes this cheap
# when nothing changed, and a modified Containerfile can never be shadowed by a
# stale image.
podman build --force-rm --layers --jobs 0 --tag "${IMAGE}" "$(dirname "$0")"

podman run --rm --tty --volume .:/app:Z "${IMAGE}"
