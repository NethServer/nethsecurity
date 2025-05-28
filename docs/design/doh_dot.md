---
layout: default
title: DoH/DoT
parent: Design
---

# DoH/DoT

You can provide the standard DHCP instance with a forward to DNS-over-TLS (DOT) and DNS-over-HTTPs (DOH) servers.
This is done by using the [`https-dns-proxy`](https://openwrt.org/docs/guide-user/services/dns/doh_dnsmasq_https-dns-proxy).

The package can be installed using the following command:

```bash
opkg install https-dns-proxy
```

By default, the proxy listens to the `127.0.0.1:5053` and `127.0.0.1:5054` addresses. The configuration for the service can be found at the
following link: https://docs.openwrt.melmac.net/https-dns-proxy

the tool will edit the dnsmasq configuration automatically, takes care of keeping it up to date, and restart the
services if any changes happen.
