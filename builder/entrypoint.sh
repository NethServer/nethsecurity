#!/bin/bash

OUTPUT=/home/build/openwrt/.config

# Generate diffconfigfrom .conf file inside config directory
> $OUTPUT
for f in $(find /config -type f -name \*.conf)
do
    cat $f >> $OUTPUT
done

chown 1000:1000 $OUTPUT

# Apply the configuration
make defconfig

# Start the container CMD
exec "${@}"
