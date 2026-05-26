---
layout: default
title: DoH (DNS over HTTPS)
parent: Design
---

# DoH (DNS over HTTPS)

You can provide the standard DHCP instance with a forward to DNS-over-HTTPS (DoH) servers.
This is done by using the [`https-dns-proxy`](https://openwrt.org/docs/guide-user/services/dns/doh_dnsmasq_https-dns-proxy), which is included in the NethSecurity image.

By default:

- the service is disabled and is not started on boot
- the proxy listens on `127.0.0.1:5053` and `127.0.0.1:5054` when started
- `option dnsmasq_config_update '-'` prevents automatic `dnsmasq` changes

The configuration is stored in `/etc/config/https-dns-proxy`. Upstream options are documented at
[docs.openwrt.melmac.ca/https-dns-proxy](https://docs.openwrt.melmac.ca/https-dns-proxy/).

To integrate the proxy with `dnsmasq`, choose the `dnsmasq_config_update` value you want and then enable the service:

```bash
uci set https-dns-proxy.config.dnsmasq_config_update='*'
uci commit https-dns-proxy
/etc/init.d/https-dns-proxy enable
/etc/init.d/https-dns-proxy start
```

If `dnsmasq_config_update` stays set to `-`, the first-boot defaults script
will consider the service disabled and may disable it again after an image
upgrade. At the moment this is not expected to be a practical problem because
configuration is supported only from the command line.
