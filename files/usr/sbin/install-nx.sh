#!/bin/bash
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
           mkdir firmware
           mount -t vfat $P firmware
           I=$(find firmware -name nextsecurity\*img.gz| wc -l);
           if [ "$I" -eq 1 ]; then
              IMG=$(find firmware -name nextsecurity\*img.gz| tail -n 1);
           else if [ -z ${S+x} ]; then 
              IMG=$S 
           else
              let A=1; B=("");
              echo "Choose one of the detected images to install to device:"
              for I in $(ls -1f firmware/nextsecurity*img.gz); do 
                 echo "$A. $I"; ((A+=1));B+=($I); 
              done;
              read -r $IMG
              IMG=${B[$IMG]}
           fi
           if [ ! -f $IMG ]; then
              echo "Firmware not found"
              umount firmware
              rmdir firmware
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
