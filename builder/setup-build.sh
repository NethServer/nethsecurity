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

# Configure repositories
sed -i '/telephony/d' feeds.conf.default
sed -i 's/src-git-full/src-git/' feeds.conf.default
sed -i '1isrc-link nethsecurity /home/buildbot/openwrt/nspackages' feeds.conf.default
./scripts/feeds update
./scripts/feeds install -a

# Apply patches
find patches/ -type f -name "*.patch" | while read -r patch; do
    dir_name=$(dirname "$patch")
    dir_name=${dir_name#"patches/"}
    patch -d "$dir_name" -F 2 -p 1 < "$patch"
done

# Conclude configuration
cat <<EOF >> config/.diffconfig
CONFIG_GRUB_TITLE="NethSecurity"
CONFIG_VERSION_BUG_URL="https://github.com/NethServer/nethsecurity/issues"
CONFIG_VERSION_DIST="NethSecurity"
CONFIG_VERSION_HOME_URL="https://github.com/nethserver/nethsecurity"
CONFIG_VERSION_MANUFACTURER="Nethesis"
CONFIG_VERSION_MANUFACTURER_URL="https://www.nethesis.it"
CONFIG_VERSION_NUMBER="${nethsecurity_version}"
CONFIG_VERSION_CODE="${owrt_version}"
CONFIG_VERSION_PRODUCT="NethSecurity"
CONFIG_VERSION_REPO="https://updates.nethsecurity.nethserver.org/${repo_channel}/${nethsecurity_version}"
CONFIG_VERSION_SUPPORT_URL="https://community.nethserver.org"
EOF
cat "config/targets/${target}.conf" >> config/.diffconfig

# Write version information into a file
echo "${repo_channel}" > files/etc/repo-channel

# Netifyd closed-sources plugin
if [ -z "$NETIFYD_ACCESS_TOKEN" ]; then
    echo "Netifyd closed-sources plugin not enabled: skipping ns-dpi package"
    echo CONFIG_PACKAGE_ns-dpi=n >> config/.diffconfig
else
    echo "Netifyd closed-sources plugin enabled: enabling ns-dpi package"
    git clone "https://oauth2:$NETIFYD_ACCESS_TOKEN@gitlab.com/netify.ai/private/nethesis/netify-flow-actions.git"
    git clone "https://oauth2:$NETIFYD_ACCESS_TOKEN@gitlab.com/netify.ai/private/nethesis/netify-agent-stats-plugin.git"
    cat << EOF >> config/.diffconfig
CONFIG_PACKAGE_netify-flow-actions=y
CONFIG_NETIFY_FLOW_ACTIONS_TARGET_LOG=y
CONFIG_NETIFY_FLOW_ACTIONS_TARGET_CTLABEL=y
CONFIG_NETIFY_FLOW_ACTIONS_TARGET_NFTSET=y
CONFIG_PACKAGE_netify-plugin-stats=y
EOF
fi

# Expand configuration
cp config/.diffconfig .config
make defconfig

# Generate local build key
if [ -n "$USIGN_PUB_KEY" ] && [ -n "$USIGN_PRIV_KEY" ]; then
    echo "Using environment keys"
    echo "$USIGN_PUB_KEY" > ./key-build.pub
    echo "$USIGN_PRIV_KEY" > ./key-build
elif [ -f key-build.pub ] && [ -f key-build ]; then
    echo "Using existing keys to sign the build"
else
    echo "Generating local build key"
    ./staging_dir/host/bin/usign -G -s ./key-build -p ./key-build.pub -c "Local build key"
fi
