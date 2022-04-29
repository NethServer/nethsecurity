#!/bin/bash

OUTPUT=/home/build/openwrt/.config

# Fix permissions
sudo chown -R build:build /config /home/build/openwrt/files/etc/uci-defaults /home/build/openwrt/bin

# Generate diffconfigfrom .conf file inside config directory
> $OUTPUT
for f in $(find /config -type f -name \*.conf)
do
    cat $f >> $OUTPUT
done

# Apply the configuration
make defconfig

# Start the container CMD
exec "${@}"
