#!/bin/bash

echo "Preparing build environment ..."

OUTPUT=/home/build/openwrt/.config

# hack to avoid changing permissions on local file system
sudo cp -r /config /config-tmp
sudo cp -r /uci-defaults/* /home/build/openwrt/files/etc/uci-defaults/

# Fix permissions
sudo chown -R build:build /config-tmp /home/build/openwrt/files/etc/uci-defaults 2>/dev/null

# Generate diffconfigfrom .conf file inside config directory
> $OUTPUT
for f in $(find /config-tmp -type f -name \*.conf)
do
    cat $f >> $OUTPUT
done

# Apply the configuration
make defconfig

# Start the container CMD
exec "${@}"
