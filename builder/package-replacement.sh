#!/usr/bin/env sh

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

find /home/buildbot/openwrt/nspackages/ -maxdepth 1 -type d | while read -r dir;
    do
        package=$(basename "$dir")
        [ "$package" = "nspackages" ] && continue
        if [ -e "package/feeds/packages/$package" ]; then
            echo "Replacing upstream package: $package"
            rm -f "package/feeds/packages/$package"
            ln -s "../../../feeds/nethsecurity/$package" "/home/buildbot/openwrt/package/feeds/packages/$package"
        fi
    done
