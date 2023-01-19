#!/bin/bash
#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

set -e

source /etc/os-release

DL_DIR=/tmp/download
BASE_URL="https://distfeed.nethserver.org"
ARCH=$(echo $OPENWRT_BOARD | tr '/' '-')
IMG="nextsecurity-$VERSION-$ARCH-generic-ext4-combined-efi.img.gz"
IMG_URL="$BASE_URL/$VERSION/targets/$OPENWRT_BOARD/$IMG"
HASH_URL="$BASE_URL/$VERSION/targets/$OPENWRT_BOARD/sha256sums"

if [ $# -eq 0 ]; then
    echo -e "No arguments supplied, target device for installation needed\n$0 -t /dev/sdX"
    exit 1
fi
F=0
while getopts "ft::" opt; do
            case $opt in
            (f) F=1 ;; #Force write
            (t) T=${OPTARG} ;; #Target disk
            (*) printf "Illegal option '-%s'\n" "$opt" && exit 1 ;;
            esac
done
if [ -b $T ]; then
        if [ "$F" -eq 1 ]; then 
           N=1; 
        else
           N=$(grep "${T##*/}" /proc/partitions | wc -l)
        fi
        M=$(mount | grep $T| wc -l)
        if [ $N -eq 1 ] && [ $M -eq 0 ]; then
           rm -rf $DL_DIR &> /dev/null
           mkdir -p $DL_DIR
           pushd $DL_DIR >/dev/null
           wget -q --show-progress $HASH_URL $IMG_URL
           grep $IMG $DL_DIR/sha256sums | sha256sum -c
           zcat $DL_DIR/$IMG | dd of=$T bs=64K iflag=fullblock conv=fsync oflag=direct 2>/dev/null
           popd >/dev/null
        else
           if [ $M -eq 0 ]; then
              echo -e "Multiple partitions found on target device, check it or use -f to force overwrite"
           else
              echo -e "Target partition in use, umount it first"
           fi
           error=1
        fi
else
        echo -e "Target device not found"
        error=1
fi
exit ${error:-0}
