#!/bin/bash

#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

#
# Create ghcr.io/nethserver/nethsecurity/python3-nethsec-test container
#

set -e

podman build --force-rm --layers --jobs 0 --tag ghcr.io/nethserver/nethsecurity/python3-nethsec-test .
images+=("ghcr.io/nethserver/nethsecurity/python3-nethsec-test")

if [[ -n "${CI}" ]]; then
    # Set output value for Github Actions
    printf "images=%s\n" "${images[*]}" >> "${GITHUB_OUTPUT}"
else
    printf "Publish the images with:\n\n"
    for image in "${images[@]}"; do printf "  buildah push %s docker://%s:latest\n" "${image}" "${image}" ; done
    printf "\n"
fi
