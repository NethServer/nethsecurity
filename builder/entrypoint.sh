#!/bin/bash

echo "Preparing build environment ..."

OUTPUT=/home/build/openwrt/.config

# hack to avoid changing permissions on local file system
sudo cp -r /config /config-tmp
sudo cp -r /files/* /home/build/openwrt/files/
sudo cp -r /nspackages /home/build/openwrt/

echo "src-link nethserver /home/build/openwrt/nspackages" >> feeds.conf.default
./scripts/feeds update nethserver
./scripts/feeds install -a -p nethserver

# Fix permissions
sudo chown -R build:build /config-tmp /home/build/openwrt/{files,nspackages} >/dev/null

# Generate diffconfigfrom .conf file inside config directory
> $OUTPUT
for f in $(find /config-tmp -type f -name \*.conf)
do
    cat $f >> $OUTPUT
done

# Apply the configuration
make defconfig

# Generate local build key
if [[ ! -f key-build.pub && -f ./staging_dir/host/bin/usign ]]; then
    ./staging_dir/host/bin/usign -G -s ./key-build -p ./key-build.pub -c "Local build key"
fi

# Start the container CMD
exec "${@}"
