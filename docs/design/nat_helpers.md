---
layout: default
title: NAT helpers
parent: Design
---

# NAT helpers

NAT helpers management is implemented by `ns.nathelpers` API of `ns-api` package. The rest of this page provides some low-level details regarding NAT helpers.

The image contains already all commonly used NAT helpers,
but helpers are not loaded by default on a new installation.

Please note that after migration, all NAT helpers are loaded
by default to preserve NethServer 7 behavior.

The `kmod-nf-nathelper` package provides the following helpers:
`opkg files kmod-nf-nathelper | grep -e '\.ko$' | cut -d'/' -f 5 | cut -d'.' -f1`
```
nf_nat_ftp
nf_conntrack_ftp
```

The `kmod-nf-nathelper-extra` package provides the following helpers:
`opkg files kmod-nf-nathelper-extra | grep -e '\.ko$' | cut -d'/' -f 5 | cut -d'.' -f1`
```
nf_conntrack_pptp
nf_conntrack_broadcast
nf_conntrack_amanda
nf_nat_h323
nf_conntrack_tftp
nf_conntrack_sip
nf_nat_pptp
nf_conntrack_snmp
nf_nat_amanda
nf_nat_tftp
nf_conntrack_irc
nf_nat_sip
nf_nat_snmp_basic
nf_conntrack_h323
nf_nat_irc
```

## Enable FTP helper

To enable only the FTP helper:
```
echo -ne "nf_conntrack_ftp\nnf_nat_ftp\n" > /etc/modules.d/ns-nathelpers
load-kernel-modules
service firewall restart
```

## Enable SIP helper (SIP ALG)

To enable only SIP helper with default configuration and load it at boot, use:
```
echo nf_nat_sip > /etc/modules.d/ns-nathelpers
load-kernel-modules
service firewall restart
```
The `nf_nat_sip` module will automatically load the `nf_conntrack_sip` module.

Check if SIP helper is loaded:
```
lsmod | grep ^nf_nat_sip
```

List SIP helper module parameters, please note that parameters are under the `nf_conntrack_sip` module:
```
ls /sys/module/nf_conntrack_sip/parameters
```

From [kernel source](https://github.com/torvalds/linux/blob/v5.10/net/netfilter/nf_conntrack_sip.c), these are the parameters of `nf_conntrack_sip` module:
- `ports`: port numbers of SIP servers
- `sip_timeout`: timeout for the master SIP session
- `sip_direct_signalling`: expect incoming calls from registrar only (default 1)
- `sip_direct_media`: expect Media streams between signalling endpoints only (default 1)
- `sip_external_media`: expect Media streams between external endpoints (default 0)


Enable SIP helper with non-default parameters:
```
echo nf_conntrack_sip sip_external_media=1 > /etc/modules.d/ns-nathelpers
echo nf_nat_sip >> /etc/modules.d/ns-nathelpers
load-kernel-modules
service firewall restart
```

When setting non-default parameters, it's recommended to reboot the system to ensure the correct module parameters are applied.

## Disable an helper

To disable an helper, remove it from the `/etc/modules.d/ns-nathelpers` file and reboot.
