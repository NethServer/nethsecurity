---
layout: default
title: Design
nav_order: 05
---

# Design

**Goals**

Replace NethServer 7 firewall implementation with a dedicated UTM Linux distribution based on [OpenWrt](https://openwrt.org/)

Key features:

- reliability: prevent damage on power loss
- easy to install
- easy and quick restore
- IPv6 support
- optional [remote controller](../packages/ns-plug)

**Architecture and design**

- no modularity: the OS is distributed as a bootable image
- auto-updates only for security fixes or critical bugs
- full updates require reboot
- keep real time data on the machine, send historical data to an external NS8 server


## Admin friendly Linux distribution

OpenWrt is a really tiny distribution which can run on very small hardware.
To achieve this goal it uses [BusyBox](https://busybox.net/) as main tool.

NethSecurity doesn't have such limitations because it has been designed to run
on more powerful hardware with at least 1GB of RAM and 1GB of disk space.
It includes many of the same tools present inside CentOS such as:
top, find, diff, grep, ps and awk.
Also, the default shell is `bash`.

## Conventions

### UCI configuration

Whenever possible, all UCI section are named section.
Automatically generated section are named with a `ns_` prefix.

The user should always avoid to manually edit sections containing the `ns_prefix.`

### Packages

See [Packages](../packages/).
