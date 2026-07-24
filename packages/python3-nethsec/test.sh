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
podman run --rm --tty --volume .:/app:Z "${IMAGE}:${IMAGETAG}"
