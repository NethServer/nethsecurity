#!/usr/bin/env sh

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

set -e

if [ "$1" = "make" ]; then
    setup-build
fi

# Start the container CMD
exec "${@}"
