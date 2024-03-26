#!/bin/bash

#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Abort if any setup step fails
set -e

echo "Preparing build environment ..."

OUTPUT=/home/build/openwrt/.config

# hack to avoid changing permissions on local file system
sudo cp -r /config /config-tmp
sudo cp -r /files/* /home/build/openwrt/files/
sudo cp -r /nspackages /home/build/openwrt/
sudo cp -r /patches /home/build/openwrt/

echo "Creating download cache dir"
mkdir -p /home/build/openwrt/download

echo "src-link nethsecurity /home/build/openwrt/nspackages" >> feeds.conf.default
./scripts/feeds update nethsecurity
./scripts/feeds install -a -p nethsecurity

# Update LuCI fork
./scripts/feeds update luci

# Replace upstream packages
for d in $(find /home/build/openwrt/nspackages/ -maxdepth 1 -type d)
do
    package=$(basename $d)
    [ "$package" = "nspackages" ] && continue
    if [ -e "package/feeds/packages/$package" ]; then
        echo "Replacing upstream package: $package"
	    rm -f "package/feeds/packages/$package"
	    ln -s "../../../feeds/nethsecurity/$package" "/home/build/openwrt/package/feeds/packages/$package"
    fi
done

# Fix permissions
sudo chown -R build:build /config-tmp /home/build/openwrt/{files,nspackages,patches} >/dev/null

# Setup branding and version
# Required env variables:
# - VERSION
# - REPO_CHANNEL
# - OWRT_VERSION

if [ -z "$VERSION" ]; then
    echo "VERSION env variable not set"
    exit 1
fi

if [ -z "$REPO_CHANNEL" ]; then
    echo "REPO_CHANNEL env variable not set"
    exit 1
fi

if [ -z "$OWRT_VERSION" ]; then
    echo "OWRT_VERSION env variable not set"
    exit 1
fi

: "${CONFIG_GRUB_TITLE:=NethSecurity}"
: "${CONFIG_VERSION_BUG_URL:=https://github.com/NethServer/nethsecurity/issues}"
: "${CONFIG_VERSION_DIST:=NethSecurity}"
: "${CONFIG_VERSION_HOME_URL:=https://github.com/nethserver/nethsecurity}"
: "${CONFIG_VERSION_MANUFACTURER:=Nethesis}"
: "${CONFIG_VERSION_MANUFACTURER_URL:=https://www.nethesis.it}"
: "${CONFIG_VERSION_PRODUCT:=NethSecurity}"
: "${CONFIG_VERSION_REPO:=https://updates.nethsecurity.nethserver.org/${REPO_CHANNEL}/${OWRT_VERSION}}"
: "${CONFIG_VERSION_SUPPORT_URL:=https://community.nethserver.org}"

echo "CONFIG_GRUB_TITLE=\"${CONFIG_GRUB_TITLE}\"" >> /config-tmp/branding.conf
echo "CONFIG_VERSION_BUG_URL=\"${CONFIG_VERSION_BUG_URL}\"" >> /config-tmp/branding.conf
echo "CONFIG_VERSION_DIST=\"${CONFIG_VERSION_DIST}\"" >> /config-tmp/branding.conf
echo "CONFIG_VERSION_HOME_URL=\"${CONFIG_VERSION_HOME_URL}\"" >> /config-tmp/branding.conf
echo "CONFIG_VERSION_MANUFACTURER=\"${CONFIG_VERSION_MANUFACTURER}\"" >> /config-tmp/branding.conf
echo "CONFIG_VERSION_MANUFACTURER_URL=\"${CONFIG_VERSION_MANUFACTURER_URL}\"" >> /config-tmp/branding.conf
echo "CONFIG_VERSION_NUMBER=\"8-${VERSION}\"" >> /config-tmp/branding.conf
echo "CONFIG_VERSION_PRODUCT=\"${CONFIG_VERSION_PRODUCT}\"" >> /config-tmp/branding.conf
echo "CONFIG_VERSION_REPO=\"${CONFIG_VERSION_REPO}\"" >> /config-tmp/branding.conf
echo "CONFIG_VERSION_SUPPORT_URL=\"${CONFIG_VERSION_SUPPORT_URL}\"" >> /config-tmp/branding.conf

# Setup output target
if [ -z "$TARGET" ]; then
    echo "TARGET env variable not set"
    exit 1
fi
echo "Enabling $TARGET target"
mv -v "/config-tmp/targets/${TARGET}.conf" /config-tmp/target.conf
rm -rf /config-tmp/targets

# Generate diffconfig from .conf file inside config directory
> $OUTPUT
for f in $(find /config-tmp -type f -name \*.conf)
do
    cat $f >> $OUTPUT
done

# Apply package patches
for p in $(find patches/ -type f -name *\.patch)
do
    # find original dir
    dname=$(dirname $p)
    dname=${dname#"patches/"}
    patch -d $dname -F 2 -p 1 < $p
done

if [[ -n "$NETIFYD_ACCESS_TOKEN" ]]; then
    echo "Enabling Netifyd closed-sources plugins.."
    pushd /home/build/openwrt
    git clone https://oauth2:$NETIFYD_ACCESS_TOKEN@gitlab.com/netify.ai/private/nethesis/netify-flow-actions.git
    git clone https://oauth2:$NETIFYD_ACCESS_TOKEN@gitlab.com/netify.ai/private/nethesis/netify-agent-stats-plugin.git

    cat <<EOF >>$OUTPUT
CONFIG_PACKAGE_netify-flow-actions=y
CONFIG_NETIFY_FLOW_ACTIONS_TARGET_LOG=y
CONFIG_NETIFY_FLOW_ACTIONS_TARGET_CTLABEL=y
CONFIG_NETIFY_FLOW_ACTIONS_TARGET_NFTSET=y
EOF

    cat <<EOF >>$OUTPUT
CONFIG_PACKAGE_netify-plugin-stats=y
EOF
    popd
else
    echo "Netifyd closed-sources plugin not enabled: disabling ns-dpi package ..."
    cat <<EOF >>$OUTPUT
CONFIG_PACKAGE_ns-dpi=n
EOF
fi

# Apply the configuration
make defconfig

# Generate local build key

if [[ -n "$USIGN_PUB_KEY" && -n "$USIGN_PRIV_KEY" ]]; then
    echo "$USIGN_PUB_KEY" > ./key-build.pub
    echo "$USIGN_PRIV_KEY" > ./key-build
elif [[ ! -f key-build.pub && -f ./staging_dir/host/bin/usign ]]; then
    ./staging_dir/host/bin/usign -G -s ./key-build -p ./key-build.pub -c "Local build key"
fi

# Start the container CMD
exec "${@}"
