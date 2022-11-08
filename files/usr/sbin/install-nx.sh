#!/bin/bash
#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#
if [ $# -eq 0 ]; then
    echo -e "No arguments supplied, target device for installation needed\n$0 -t /dev/sdX [-s source]"    
    exit 1
fi
while getopts "ft::s::" opt; do
            case $opt in
            (f) F=1 ;; #Force write
            (s) S=${OPTARG} ;; #Source image
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
        P=$(df -t vfat /boot | tail -n 1| cut -d " " -f 1| tr "1" "3")
        if [ $N -eq 1 ] && [ $M -eq 0 ]; then
           mkdir /tmp/firmware
           mount -t vfat $P /tmp/firmware
           FW=( $(find /tmp/firmware -name nextsecurity\*img.gz| tr " " "$")) ;
           if [ "${#FW[@]}" -eq 1 ]; then
              IMG=${FW//$/ };
           elif [ ! -z ${S+x} ]; then 
              IMG="$S" 
           else
              let A=1; B=("");
              echo "Choose one of the detected images to install to device:"
              for I in ${FW[@]}; do
                 I=${I//$/ };
                 echo "$A. ${I:14}"; ((A+=1));B+=($I); 
              done;
              echo -n "Your choice: "
              read -r IMG
              IMG=${B[$IMG]}
           fi
           if [ ! -f $IMG ]; then
              echo "Firmware not found"
              umount /tmp/firmware
              rmdir /tmp/firmware
              exit 1
           else
              zcat $IMG| dd of=$T  bs=64K iflag=fullblock conv=notrunc
           fi
           umount /tmp/firmware
           rmdir /tmp/firmware
        else
           if [ $M -eq 0 ]; then
              echo -e "Multiple partitions find on target device, check it or use -f to force overwrite"
           else
              echo -e "Target partition in use, umount it first"
           fi
           exit 1
        fi
else
        echo -e "Target device not found"
        exit 1
fi
