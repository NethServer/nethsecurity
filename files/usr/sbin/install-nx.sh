#!/bin/bash
if [ $# -eq 0 ]; then
    echo -e "No arguments supplied, target device for installation needed\n$0 -t /dev/sdX [-s source]"    
    exit 1
fi
while getopts "ft::" opt; do
            case $opt in
            (f) F=1 ;;
            (s) S=${OPTARG} ;;
            (t) T=${OPTARG} ;;
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
        S=$(df -t vfat /boot | tail -n 1| cut -d " " -f 1| tr "1" "3")
        if [ $N -eq 1 ] && [ $M -eq 0 ]; then
           mkdir mymount
           mount -t vfat $S mymount
           IMG=$(find mymount -name nextsecurity.img.gz| tail -n 1);
           if [ -z ${S+x} ]; then IMG=$S fi
           if [ ! -f $IMG ]; then
              echo "Firmware not found"
              umount mymount
              rmdir mymount
              exit 1
           else
              zcat $IMG| dd of=$T conv=notrunc
           fi
           umount mymount
           rmdir mymount
        else
           echo -e "Multiple partitions find on target device, check it or use -f to force overwrite"
        fi
else
        echo -e "Target device not found"
fi
