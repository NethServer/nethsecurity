#!/usr/bin/env sh

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

set -e

find patches/ -type f -name "*.patch" | while read -r patch; do
    dir_name=$(dirname "$patch")
    dir_name=${dir_name#"patches/"}
    patch -d "$dir_name" -F 2 -p 1 < "$patch"
done
