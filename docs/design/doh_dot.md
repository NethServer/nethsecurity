---
layout: default
title: DoH/DoT
parent: Design
---

# DoH/DoT

You can provide the standard DHCP instance with a forward to DNS-over-TLS (DOT) and DNS-over-HTTPs (DOH) servers.
This is done by using the [`https-dns-proxy`](https://openwrt.org/docs/guide-user/services/dns/doh_dnsmasq_https-dns-proxy).

By default, the proxy listens to the `127.0.0.1:5053` address. The configuration for the service can be found at the
following link: https://docs.openwrt.melmac.net/https-dns-proxy

To start the service and enable it to automatically start at boot, run the following command:

```bash
/etc/init.d/https-dns-proxy enable
/etc/init.d/https-dns-proxy start
```

This will start the service, edit the dnsmasq configuration automatically and restart the services needed.
