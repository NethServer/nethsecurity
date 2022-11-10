#!/bin/bash
#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

function loadkmap_it() {
    loadlmap < /usr/share/keymaps/it.map.bin
    echo "Done"
}

function memory_check() {
    msg=$(free -h)
    echo -e "Memory usage on $HOSTNAME is: \n$msg"
}

function cpu_check() {
    msg=$(uptime)
    echo -e "CPU load on $HOSTNAME is: \n$msg"
}

function tcp_check() {
    msg=$(cat  /proc/net/tcp | wc -l)
    echo -e "TCP connections on $HOSTNAME: \n$msg"
}

function kernel_check() {
    msg=$(uname -r)
    echo -e "Kernel version on $HOSTNAME is: \n$msg"
}

function all_checks() {
	memory_check
	cpu_check
	tcp_check
	kernel_check
}

function install_NextSecurity() {
    disk=$(find /dev/sd[a-z] | grep -v $(df -t vfat /boot | tail -n 1| cut -d " " -f 1| tr -d "1") | head -n 1)
    msg=(install-nx.sh -t $disk)
    echo -e "Install: \n$msg"
}

function force_install_NextSecurity() {
    disk=$(find /dev/sd[a-z] | grep -v $(df -t vfat /boot | tail -n 1| cut -d " " -f 1| tr -d "1") | head -n 1)
    msg=$(install-nx.sh -f -t $disk)
    echo -e "Install: \n$msg"
}

##
# Color  Variables
##
red='\e[31m'
green='\e[32m'
blue='\e[34m'
white='\e[97m'
clear='\e[0m'

##
# Color Functions
##

ColorRed(){
	echo -ne $red$1$clear
}
ColorGreen(){
	echo -ne $green$1$clear
}
ColorBlue(){
	echo -ne $blue$1$clear
}
ColorWhite(){
	echo -ne $white$1$clear
}

WrongCommand(){
        echo -e $red"Wrong option."$clear;
        }

menu(){
disk=$(find /dev/sd[a-z] | grep -v $(df -t vfat /boot | tail -n 1| cut -d " " -f 1| tr -d "1"))
echo -ne "
Quick options:
$(ColorGreen '1)') Memory usage				$(ColorGreen '2)') CPU load
$(ColorGreen '3)') Number of TCP connections 		$(ColorGreen '4)') Kernel version
$(ColorGreen '5)') Check All				$(ColorGreen '6)') loadkmap IT
$(ColorGreen '7)') install NextSecurity	on ${disk:5}		$(ColorGreen '8)') force install NextSecurity on ${disk:5}
$(ColorGreen '9)') Reboot				$(ColorGreen '0)') Exit
$(ColorGreen 's)') go to shell
$(ColorWhite 'Choose an option:') "
        read choice
        case $choice in
	        1) memory_check ; menu ;;
	        2) cpu_check ; menu ;;
	        3) tcp_check ; menu ;;
	        4) kernel_check ; menu ;;
	        5) all_checks ; menu ;;
	        6) loadkmap_it ; menu ;;
	        7) install_NextSecurity; menu;;
	        8) force_install_NextSecurity; menu;;
	        9) reboot; menu;;
		0) exit 0 ;;
		s) kill -INT $$ ;;
		*) WrongCommand; menu ;;
        esac
}

# Call the menu function
menu