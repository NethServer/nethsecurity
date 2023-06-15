---
layout: default
title: NAT helpers
nav_order: 40
---

# NAT helpers

As default the image does not contain many NAT helpers.
To install extra helpers like SIP ALG use:
```
opkg update
opkg install kmod-nf-nathelper-extra
```

Modules listed inside inside `/etc/modules.d/nf-nathelper-extra` are automatically loaded.

The `kmod-nf-nathelper-extra` provides the following helpers: 
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

## SIP helper (SIP ALG)

To enable only SIP helper with default configuration and load it at boot, use:
```
echo nf_nat_sip > /etc/modules.d/nf-nat-sip
reboot
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
echo nf_conntrack_sip sip_external_media=1 sip_direct_media=1 > /etc/modules.d/nf-nat-sip
echo nf_nat_sip >> /etc/modules.d/nf-nat-sip
reboot
```
