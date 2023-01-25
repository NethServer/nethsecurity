---
layout: default
title: Quickstart guide
nav_order: 01
---

# Quickstart guide

NextSecurity can be installed on virtual machines or x86 hardware.

* TOC
{:toc}

## Hardware requirements

Minimum requirements:

- 2 ethernet network cards
- 1 GB of RAM
- 1 GB of disk

## Download

Download the [x86_64 image]({{site.download_url}}/{{site.version}}/targets/x86/64/nextsecurity-{{site.version}}-x86-64-generic-ext4-combined-efi.img.gz).

The image should work both on machines with legacy and EFI BIOS.

## Install

To install the system you can choose between 2 alternative methods:

- write the downloaded image directly to the disk (recommended for virtual machines)
- boot from an USB stick (recommended for physical machines)

### Virtual machines

You can use the downloaded image as a virtual machine disk:

1. extract the downloaded image:
   ```
   gunzip nextsecurity-22.03.0-x86-64-generic-squashfs-combined.img.gz
   ```
2. create a new virtual machine and select the uncompressed image as disk
3. boot the virtual machine

### Physical machines

NextSecurity can be run directly from a USB stick:

1. plug the USB stick into your desktop Linux machine
2. find the USB stick device name, in this example the device is named `/dev/sdd`
3. as `root` user, write the downloaded image to the device:
   ```
   zcat nextsecurity-22.03.0-x86-64-generic-squashfs-combined.img.gz | dd of=/dev/sdd bs=1M iflag=fullblock status=progress oflag=direct
   ```
4. unplug the USB stick from the desktop and plug it into the server
5. boot the server, make sure to select the USB stick from boot menu
6. connect to VGA or serial console and select option `2` from the menu

   Menu example:
   ```
   Quick options:
   1) Load alternate keyboard maps
   2) Install NextSecurity on sda
   3) Install NextSecurity on other storage
   l) Login
   x) Exit
   ```

If you're running a desktop Windows machine, you will need extra software for point 2.
First, make sure to format the USB drive then unmount it.
Use one of the following tools to write the USB stick:

* [Etcher](https://etcher.io/ )
* [Win32 Disk Imager](http://sourceforge.net/projects/win32diskimager/)
* [Rawrite32](http://www.netbsd.org/~martin/rawrite32/)
* [dd for Windows](http://www.chrysocome.net/dd)

You can also connect to the running machine using SSH and manually
install the system to the disk using `install-nx.sh` command.

Usage Example:
```
install-nx.sh -t /dev/vda
```

## Default network configuration

On first boot the system will try to configure
the network interfaces.

As the default the network configuration will be:

- lan on first ethernet device with static address `192.168.1.1`
- wan on second ethernet device with DHCP

An exception are virtual machines running on KVM and on Digital Ocean cloud provider (droplet).
In this case the network configuration will be:

- lan on first ethernet device with DHCP
- wan on second ethernet device with DHCP

## Access

As default, only `root` user exists.
You can use the `root` user for all access methods listed below.

Default credentials:

- user: `root`
- password: `Nethesis,1234`

Default network configuration:

- static IP address on LAN device named `br-lan`: `192.168.1.1` 
- dynamic IP address on WAN device, usually named `eth1`

### Web user interface

NextSecurity has 2 different web user interface:

- LuCI: standard OpenWrt web interface, some pages may cause unpredictable configuration changes (see below)
- NextSec: custom UI, this is just a prototype and can't be used to configure the system

Both user interfaces listen on port 443 (HTTPs):

- LuCI is accessible at `https://server_ip/cgi-bin/luci`
- NextSec is accessible at `https://server_ip`

#### LuCI

The following sections/options should not be changed from the web interface:

- Logging
- Flashstart firewall rules
- OpenVPN instances starting with `ns_` prefix
- XFRM network interfaces
- HTTP(S) access
- opkg configuration
- Adblock configuration

### SSH

Ad default, the system accepts SSH connections on standard port `22`.
Access with `root` user and default password.

From a Linux machine use:
```
ssh root@192.168.1.1
```

### VGA console

If the machine has a VGA/DVI/HDMI video port, connect a monitor to it.
Then will be able to login to the console using default credentials above.

Please note that the system is configured with `US` keyboard layout.

To temporary change current keyboard layout to Italian, login to the system then execute:
```
loadkmap < /usr/share/keymaps/it.map.bin
```

Keyboard layout configuration can be saved by writing the keyamp path file inside `/etc/keymap`. Example:
```
echo '/usr/share/keymaps/it.map.bin' > /etc/keymap
grep -q /etc/keymap /etc/sysupgrade.conf || echo /etc/keymap >> /etc/sysupgrade.conf
```

To obtain the list of availabile keymaps execute: `ls /usr/share/keymaps`.

Other keymaps can be generated from a CentOS machine with the following command:
```
loadkeys -b it.map.gz -u -q >it.map.bin
```
