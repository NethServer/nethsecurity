# dnsdist

[dnsdist](https://dnsdist.org/) can be used:
- as a DNS forwarder to DNS-over-TLS (DOT) and DNS-over-HTTPs (DOH) servers, it replaces [https-dns-proxy](https://openwrt.org/docs/guide-user/services/dns/doh_dnsmasq_https-dns-proxy)
- as a DNS forwarder to remote DNS filters like Flashstart
- as a DNS fronted with dynamic rules forwarding local queries to Dnsmasq

## Forwarder to DOT and DOH

Setup dnsdist as Dnsmasq forwarder:
```
uci del dhcp.@dnsmasq[0].server
uci add_list dhcp.@dnsmasq[0].server='127.0.0.1#5300'
uci commit dhcp
service dnsmasq restart
```

dnsdist listens to 5353:
```
addLocal('0.0.0.0:5353', { reusePort=true })
```

[Cloudflare](https://1.1.1.1/):
```
--- DNS over TLS
newServer({address="1.1.1.1:853", tls="openssl", subjectName="cloudflare-dns.com", validateCertificates=true, checkInterval=10, checkTimeout=2000})
newServer({address="1.0.0.1:853", tls="openssl", subjectName="cloudflare-dns.com", validateCertificates=true, checkInterval=10, checkTimeout=2000})

--- DNS over HTTPS
newServer({address="1.1.1.1:443", tls="openssl", subjectName="cloudflare-dns.com", dohPath="/dns-query", validateCertificates=true, checkInterval=10, checkTimeout=2000})
newServer({address="1.0.0.1:443", tls="openssl", subjectName="cloudflare-dns.com", dohPath="/dns-query", validateCertificates=true, checkInterval=10, checkTimeout=2000})
```

[Quad9](https://www.quad9.net/):
```
--- DNS over TLS
newServer({address="9.9.9.9:853", tls="openssl", subjectName="dns.quad9.net", validateCertificates=true, checkInterval=10, checkTimeout=2000})
newServer({address="149.112.112.112:853", tls="openssl", subjectName="dns.quad9.net", validateCertificates=true, checkInterval=10, checkTimeout=2000})

--- DNS over HTTPS
newServer({address="9.9.9.9:443", tls="openssl", subjectName="dns.quad9.net", dohPath="/dns-query", validateCertificates=true, checkInterval=10, checkTimeout=2000})
newServer({address="9.9.9.9:5053", tls="openssl", subjectName="dns.quad9.net", dohPath="/dns-query", validateCertificates=true, checkInterval=10, checkTimeout=2000})
newServer({address="149.112.112.112:443", tls="openssl", subjectName="dns.quad9.net", dohPath="/dns-query", validateCertificates=true, checkInterval=10, checkTimeout=2000})
newServer({address="149.112.112.112:5053", tls="openssl", subjectName="dns.quad9.net", dohPath="/dns-query", validateCertificates=true, checkInterval=10, checkTimeout=2000})
```

[NextDNS](https://nextdns.io/):
```
--- DNS over TLS
newServer({address="45.90.28.202:853", tls="openssl", subjectName="dns.nextdns.io",  validateCertificates=true, checkInterval=10, checkTimeout=2000})
newServer({address=":45.90.30.202853", tls="openssl", subjectName="dns.nextdns.io",  validateCertificates=true, checkInterval=10, checkTimeout=2000})
```

Configuration from [Cyber Defence Lab](https://cylab.be/blog/211/dns-over-https-and-dns-over-tls-with-dnsdist).

## Frontend

Move Dnsmasq to port 5353
```
uci set dhcp.@dnsmasq[0].port = 5353
uci commit dhcp
service dnsmasq restart
```

Given a local domain named `lan`, and using Cloudflare as a normal forwarder:
```
addLocal('0.0.0.0:53', { reusePort=true })
newServer({address="127.0.0.1:5353", pool="local"})
addAction({"lan."},  PoolAction("local"))
newServer({address="1.1.1.1", pool="flashstart", name="cloudflare1"})
newServer({address="1.0.0.1", pool="flashstart", name="cloudlfare2"})
```
