---
layout: default
title: Design
nav_order: 05
has_children: true
---

# Design

* TOC
{:toc}

## Goals

Replace NethServer 7 firewall implementation with a dedicated UTM Linux distribution based on [OpenWrt](https://openwrt.org/)

Key features:

- reliability: prevent damage on power loss
- easy to install
- easy and quick restore
- IPv6 support
- optional [remote controller](../packages/ns-plug)

## Architecture and design

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

### Zones

The firewall configuration comprises three default zones:

- `lan`: this zone encompasses all hosts within the local area network. It was previously referred to as `green` in NethServer 7 (NS7).
- `wan`: this zone represents the external network interface providing access to the Internet.
   It is inherently untrusted and should be treated as the gateway to the wider online network. In NethServer 7 (NS7), this zone was formerly denoted as `red`.
- `guest`: this zone encompasses non-trusted devices that are solely granted access to the Internet. It was previously labeled as `blue` in NS7.

The `lan` and `wan` zones are consistently existent, whereas the `guest` zone is instantiated only upon assignment of an interface.

Firewall policies facilitate inter-zone traffic according to the following schema:
```
lan -> guest -> wan
```

Traffic is permitted from left to right and denied from right to left.

### UCI

In the system, named UCI ections are generated whenever possible. Automatically generated sections typically bear a `ns_` prefix.

Several distinctive options have been incorporated into UCI configuration sections:

- `ns_description`: this option contains a comprehensive description aimed at elucidating the purpose of the section
- `ns_link`: this option facilitates the linking of one record to another and adopts the format `<configuration>/<section_name>`.
   It is commonly applied to rules and zones. This functionality serves to associate all rules and zones with a specific service:
   if the particular service is deactivated, the linked rules and zones may also be automatically disabled
- `ns_tag`: this option allows the assignment of a list of tags to any section.
   Users can define custom tags. Meanwhile, the system already employs the special `automated` tag to label automatically generated sections.

### Commit hooks

To overcome UCI limitations, the UI should always use the `ns.commit` API to commit changes.
The API will:
- execute all scripts in `/usr/libexec/ns-api/pre-commit` before committing changes
- commit UCI changes
- execute all scripts in `/usr/libexec/ns-api/post-commit` after committing changes
- notify ubus about the changes to apply them

Execution of hooks script will continue even if a script fails. A failure of the
hook script will not be reflected inside the API exit code.
Every script within the hook directory will be provided with a JSON-formatted list of changes via standard input.

### Packages

See [Packages](../packages/).
