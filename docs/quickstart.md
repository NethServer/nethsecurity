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

See the [download page]({{site.manual_url}}/download.html) inside manual.

## Install

See the [install page]({{site.manual_url}}/install.html) inside manual.

## Access

See the [access page]({{site.manual_url}}/remote_access.html) inside manual.

## Console setup

The image ships the `/usr/sbin/setup` helper for basic console-first
configuration.

The command uses a `whiptail` interface to:

- switch the console keyboard between `it` and the default `us`
- assign physical network cards to `lan` and `wan`
- configure `lan` IPv4/CIDR
- configure `wan` as `dhcp` or `static`

### LuCI

The following sections/options should not be changed from the web interface:

- Flashstart firewall rules
- OpenVPN instances starting with `ns_` prefix
- XFRM network interfaces
- apk configuration
- Adblock configuration
