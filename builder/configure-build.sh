#!/usr/bin/env sh

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

set -e

# Set up environment
nethsecurity_version=${NETHSECURITY_VERSION:?Missing NETHSECURITY_VERSION environment variable}
repo_channel=${REPO_CHANNEL:?Missing REPO_CHANNEL environment variable}
target=${TARGET:?Missing TARGET environment variable}
owrt_version=${OWRT_VERSION:?Missing OWRT_VERSION environment variable}

# For each file inside the config directory, cat the content into a .config file
for file in config/*.conf; do
    if [ -f "$file" ]; then
        echo "Processing $file"
        cat "$file" >> .config
    else
        echo "Skipping $file, not a regular file"
    fi
done

# Conclude configuration
cat <<EOF >> .config
CONFIG_GRUB_TITLE="NethSecurity"
CONFIG_VERSION_BUG_URL="https://github.com/NethServer/nethsecurity/issues"
CONFIG_VERSION_DIST="NethSecurity"
CONFIG_VERSION_HOME_URL="https://github.com/nethserver/nethsecurity"
CONFIG_VERSION_MANUFACTURER="Nethesis"
CONFIG_VERSION_MANUFACTURER_URL="https://www.nethesis.it"
CONFIG_VERSION_NUMBER="${nethsecurity_version}${BUILD_METADATA}"
CONFIG_VERSION_CODE="${owrt_version}"
CONFIG_VERSION_PRODUCT="NethSecurity"
CONFIG_VERSION_REPO="https://updates.nethsecurity.nethserver.org/${repo_channel}/${nethsecurity_version}"
CONFIG_VERSION_SUPPORT_URL="https://community.nethserver.org"
EOF
cat "config/targets/${target}.conf" >> .config

# Netifyd closed-sources plugin
if [ "$NETIFYD_ENABLED" -eq "0" ]; then
    echo "Netifyd closed-sources plugin not enabled: skipping ns-dpi package"
    echo CONFIG_PACKAGE_ns-dpi=n >> .config
else
    echo "Netifyd closed-sources plugin enabled: enabling ns-dpi package"
    cat << EOF >> .config
CONFIG_PACKAGE_netify-flow-actions=y
CONFIG_NETIFY_FLOW_ACTIONS_TARGET_LOG=y
CONFIG_NETIFY_FLOW_ACTIONS_TARGET_CTLABEL=y
CONFIG_NETIFY_FLOW_ACTIONS_TARGET_NFTSET=y
CONFIG_PACKAGE_netify-plugin-stats=y
EOF
fi

# Write version information into a file
echo "${repo_channel}" > files/etc/repo-channel

# Expand configuration
make defconfig
