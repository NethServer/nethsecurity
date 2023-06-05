---
layout: default
title: Quickstart guide
nav_order: 01
---

# Quickstart guide

NethSecurity can be installed on virtual machines or x86 hardware.

* TOC
{:toc}

## Hardware requirements

Minimum requirements:

- 2 ethernet network cards
- 1 GB of RAM
- 1 GB of disk

## Download

Download the [x86_64 image]({{site.download_url}}/{{site.version}}/targets/x86/64/nethsecurity-{{site.version}}-x86-64-generic-ext4-combined-efi.img.gz).

The image should work both on machines with legacy and EFI BIOS.

## Install

To install the system you can choose between 2 alternative methods:

- write the downloaded image directly to the disk (recommended for virtual machines)
- boot from an USB stick (recommended for physical machines with Internet access)

### Virtual machines

You can use the downloaded image as a virtual machine disk:

1. extract the downloaded image:
   ```
   gunzip nethsecurity-{{site.version}}-x86-64-generic-squashfs-combined.img.gz
   ```
2. create a new virtual machine and select the uncompressed image as disk
3. boot the virtual machine

#### Proxmox

The image can be imported inside [Proxmox](https://www.proxmox.com/).

First, make sure to have 2 different network bridges. In this example we are going to use `vmbr0` and `vmbr1`.
The described procedure can be also done using the Proxmox UI.

Create the virtual machine, in this example the machine will have id `401`:
```
qm create 401 --name "NethSecurity" --ostype l26 --cores 1 --memory 1024 --net0 virtio,bridge=vmbr0,firewall=0 --net1 virtio,bridge=vmbr1,firewall=0 --scsihw virtio-scsi-pci
```

Download the image:
```
wget "{{site.download_url}}/{{site.version}}/targets/x86/64/nethsecurity-{{site.version}}-x86-64-generic-ext4-combined-efi.img.gz"
```

Extract the image:
```
gunzip nethsecurity-{{site.version}}-x86-64-generic-ext4-combined-efi.img.gz
```

Import the extracted images a virtual machine disk:
```
qm importdisk 401 nethsecurity-{{site.version}}-x86-64-generic-ext4-combined-efi.img local-lvm
```

Attach the disk to the virtual machine:
```
qm set 401 --scsi0 "local-lvm:vm-401-disk-0"
```

Setup the boot order:
```
qm set 401 --boot order=scsi0
```

Finally, start the virtual machine.

### Physical machines

NethSecurity can be run from a USB stick or installed directly to any bootable device like
hard disks or SD cards.

1. attach the target disk/stick/card to a desktop Linux machine
2. find the disk/stick/card device name, in this example the device is named `/dev/sdd`
3. as `root` user, write the downloaded image to the device:
   ```
   zcat nethsecurity-{{site.version}}-x86-64-generic-squashfs-combined.img.gz | dd of=/dev/sdd bs=1M iflag=fullblock status=progress oflag=direct
   ```
4. unplug the disk/stick/card from the desktop and plug it into the server
5. boot the server, select the correct device (USB, SD card or hard disk) from boot menu
6. the server is installed and ready to be used

If you're running a desktop Windows machine, you will need extra software for point 2.
First, make sure to format the USB drive then unmount it.
Use one of the following tools to write the USB stick:

* [Etcher](https://etcher.io/ )
* [Win32 Disk Imager](http://sourceforge.net/projects/win32diskimager/)
* [Rawrite32](http://www.netbsd.org/~martin/rawrite32/)
* [dd for Windows](http://www.chrysocome.net/dd)

### Install from USB to disk

Since running from the USB stick does not guarantee best performances, you can also install
NethSecurity to the hard disk while running it from the USB stick itself:

1. make sure the server has Internet access
2. connect to the server using VGA, serial console or SSH
3. login with default credentials
4. execute `ns-install` and follow the instructions

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

NethSecurity has 2 different web user interface:

- LuCI: forked OpenWrt web interface, some pages may cause unpredictable configuration changes (see below)
- LuCI: standard OpenWrt web interface, some pages may cause unpredictable configuration changes (see below)
- NethSec: custom UI, this is just a prototype and can't be used to configure the system

Both user interfaces listen on port 443 (HTTPs):

- LuCI is accessible at `https://server_ip/cgi-bin/luci`
- NethSec is accessible at `https://server_ip`

#### LuCI

The following sections/options should not be changed from the web interface:

- Flashstart firewall rules
- OpenVPN instances starting with `ns_` prefix
- XFRM network interfaces
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

Keyboard layout configuration can be saved by writing the keymap code inside `/etc/keymap`. Example:
```
echo 'it' > /etc/keymap
grep -q /etc/keymap /etc/sysupgrade.conf || echo /etc/keymap >> /etc/sysupgrade.conf
```

To obtain the list of available keymaps execute: `ls -1 /usr/share/keymaps/ | cut -d'.' -f1`.

Other keymaps can be generated from a CentOS machine with the following command:
```
loadkeys -b it.map.gz -u -q >it.map.bin
```
