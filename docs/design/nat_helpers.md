---
layout: default
title: NAT helpers
parent: Design
---

# NAT helpers

NAT helpers management is implemented by `ns.nathelpers` API of `ns-api` package. The rest of this page provides some low-level details regarding NAT helpers.

The image contains already all commonly used NAT helpers,
but helpers are not loaded by default on a new installation:
NethSecurity ships empty `/etc/modules.d/nf-nathelper-*` files to neutralize
the autoload shipped by the `kmod-nf-nathelper-*` packages.

After migration, all NAT helpers are enabled and loaded to preserve NethServer 7 behavior.

The helpers are provided as kernel modules by the `kmod-nf-nathelper*` packages.
List all the available helpers with:
```
for pkg in $(apk list --installed 2>/dev/null | awk '{print $1}' | grep '^kmod-nf-nathelper' | sed 's/-[0-9].*//' | sort -u); do
    apk info -L "$pkg" 2>/dev/null | grep -e '\.ko$' | sed 's|.*/||;s|\.ko$||'
done | sort -u
```

Helpers grouped by the package that provides them:

| Package | Helpers |
| --- | --- |
| `kmod-nf-nathelper` | `nf_conntrack_ftp`, `nf_nat_ftp` |
| `kmod-nf-nathelper-amanda` | `nf_conntrack_amanda`, `nf_nat_amanda` |
| `kmod-nf-nathelper-broadcast` | `nf_conntrack_broadcast` |
| `kmod-nf-nathelper-h323` | `nf_conntrack_h323`, `nf_nat_h323` |
| `kmod-nf-nathelper-irc` | `nf_conntrack_irc`, `nf_nat_irc` |
| `kmod-nf-nathelper-netbios` | `nf_conntrack_netbios_ns` |
| `kmod-nf-nathelper-pptp` | `nf_conntrack_pptp`, `nf_nat_pptp` |
| `kmod-nf-nathelper-sane` | `nf_conntrack_sane` |
| `kmod-nf-nathelper-sip` | `nf_conntrack_sip`, `nf_nat_sip` |
| `kmod-nf-nathelper-snmp` | `nf_conntrack_snmp`, `nf_nat_snmp_basic` |
| `kmod-nf-nathelper-tftp` | `nf_conntrack_tftp`, `nf_nat_tftp` |
| `kmod-nf-nathelper-extra` | *(meta-package, no modules)* |

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
