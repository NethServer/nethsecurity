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

Download your preferred image from the below links.

Image types:

- `squashfs`: all system is loaded in RAM with a read-only filesystem, configuration changes are saved to a special persisten partition;
  this image supports the factory default and is more resilient to power outages
- `ext4`: all systemd is loaded in a more convention read-write filesystem; this image is easier for newbie uses to traditional Linux distributions

Standard BIOS images:

- [squashfs]({{site.download_url}}/targets/x86/64/nextsecurity-22.03.0-x86-64-generic-squashfs-combined.img.gz)
- [ext4]({{site.download_url}}/targets/x86/64/nextsecurity-22.03.0-x86-64-generic-ext4-combined.img.gz)

EFI BIOS images:

- [squashfs]({{site.download_url}}/targets/x86/64/nextsecurity-22.03.0-x86-64-generic-squashfs-combined-efi.img.gz)
- [ext4]({{site.download_url}}/targets/x86/64/nextsecurity-22.03.0-x86-64-generic-ext4-combined-efi.img.gz)

Not sure what to choose? Go with [standard BIOS squashfs]({{site.download_url}}/targets/x86/64/nextsecurity-22.03.0-x86-64-generic-squashfs-combined.img.gz)
which should work on most x86 machines.

## Install

To install the system, you must write the downloaded image directly to the disk.

### Virtual machines

1. Extract the downloaded image:
   ```
   gunzip nextsecurity-22.03.0-x86-64-generic-squashfs-combined.img.gz
   ```
2. Create a new virtual machine and select the uncompressed image as disk
3. Boot the virtual machine

### Physical machines

1. Attach the disk to your desktop Linux machine, let's assume the device is named `sdd`
2. Write the image to the device (you must be root):
   ```
   zcat nextsecurity-22.03.0-x86-64-generic-squashfs-combined.img.gz | dd of=/dev/sdd bs=1M
   ```
3. Attach the disk to the server
4. Boot the server

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
