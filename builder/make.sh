#!/bin/sh

#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Start parallel build
make -j $(nproc) V=sc world

IMG=$(find /home/build/openwrt/bin -name nextsecurity\*-x86-64-generic-ext4-combined-efi.img.gz);
gunzip -c ${IMG} > extended.img
dd if=/dev/zero bs=1M count=257 >> extended.img
sed -e 's/\s*\([\+0-9a-zA-Z]*\).*/\1/' << EOF | fdisk extended.img
  n # new partition
  p # primary
  3 # partition number 3
    # start over space of openwrt image
    # default, extend partition to end of disk
  t # change filesystem type
  3 # of partition number 3
  11 # in VFAT
  w # write the partition table
  q # and we're done
EOF
/home/build/openwrt/staging_dir/host/bin/mkfs.fat --invariant -n store -C "store.part" -S 512 262144
/home/build/openwrt/staging_dir/host/bin/mcopy -i "store.part" ${IMG} ::nextsecurity.img.gz
OFFSET=$(echo "$(fdisk -l extended.img| grep img3)" | cut -c 15-22)
dd if="store.part" of="extended.img" bs=512 seek="$OFFSET" conv=notrunc
gzip "extended.img"
cp extended.img.gz ${IMG}
rm "store.part"
