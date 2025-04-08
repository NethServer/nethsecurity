#!/usr/bin/env sh

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

if [ -z "$OWRT_VERSION" ]; then
    echo "OWRT_VERSION env variable not set"
    exit 1
fi

if [ -z "$VERSION" ]; then
    echo "VERSION env variable not set"
    exit 1
fi

if [ -z "$REPO_CHANNEL" ]; then
    echo "REPO_CHANNEL env variable not set"
    exit 1
fi

if [ -z "$TARGET" ]; then
    echo "TARGET env variable not set"
    exit 1
fi

# Generate branding.conf
cat << EOF >> config/branding.conf
CONFIG_GRUB_TITLE="NethSecurity"
CONFIG_VERSION_BUG_URL="https://github.com/NethServer/nethsecurity/issues"
CONFIG_VERSION_DIST="NethSecurity"
CONFIG_VERSION_HOME_URL="https://github.com/nethserver/nethsecurity"
CONFIG_VERSION_MANUFACTURER="Nethesis"
CONFIG_VERSION_MANUFACTURER_URL="https://www.nethesis.it"
CONFIG_VERSION_NUMBER="${VERSION}"
CONFIG_VERSION_PRODUCT="NethSecurity"
CONFIG_VERSION_REPO="https://updates.nethsecurity.nethserver.org/${REPO_CHANNEL}/${OWRT_VERSION}"
CONFIG_VERSION_SUPPORT_URL="https://community.nethserver.org"
EOF

# Generate target
mv -v "config/targets/${TARGET}.conf" config/target.conf
rm -rf config/targets

# Generate diffconfig from .conf files in config directory
find config -type f -name "*.conf" -exec cat {} \; >> .config
