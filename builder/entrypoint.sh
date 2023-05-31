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

echo "src-link nextsecurity /home/build/openwrt/nspackages" >> feeds.conf.default
./scripts/feeds update nextsecurity
./scripts/feeds install -a -p nextsecurity

# Replace upstream packages
for d in $(find /home/build/openwrt/nspackages/ -maxdepth 1 -type d)
do
    package=$(basename $d)
    [ "$package" = "nspackages" ] && continue
    if [ -e "package/feeds/packages/$package" ]; then
        echo "Replacing upstream package: $package"
	    rm -f "package/feeds/packages/$package"
	    ln -s "../../../feeds/nextsecurity/$package" "/home/build/openwrt/package/feeds/packages/$package"
    fi
done

# Fix permissions
sudo chown -R build:build /config-tmp /home/build/openwrt/{files,nspackages,patches} >/dev/null

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
