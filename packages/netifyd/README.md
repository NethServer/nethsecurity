# netifyd

Netifyd is a network intelligence platform that provides DPI (Deep Packet Inspection) analysis and network flow monitoring. This package integrates netifyd into NethSecurity for real-time network traffic analysis.

For detailed information, visit [https://www.netify.ai/](https://www.netify.ai/).

## NFQueue bypass lists

To improve performance, you can configure bypass lists that prevent netifyd from analyzing traffic matching certain IP addresses or CIDR blocks. This is useful for:
- Exempt traffic on local networks
- Skip analysis for known internal services
- Reduce DPI processing overhead

### Format

Entries can optionally include a description separated by `|`. Descriptions are preserved as per-element comments in the nftables configuration for visibility and documentation purposes.

Each bypass entry can be:
- **Without description:** `192.168.1.0/24`
- **With description:** `192.168.1.0/24 | My local network` or `192.168.1.0/24|My local network`

Descriptions are optional; entries without `|` are treated as addresses only.

### UCI configuration

Bypass lists are configured in `/etc/config/netifyd` under the `ns_config` section:

- `bypassv4`: list of IPv4 addresses or CIDR blocks to bypass DPI analysis
- `bypassv6`: list of IPv6 addresses or CIDR blocks to bypass DPI analysis

Example configuration:

```
config ns_config 'config'
	list bypassv4 '192.168.1.0/24 | Home network'
	list bypassv4 '10.0.0.0/8'
	list bypassv4 '172.16.0.0/12 | Lab network'
	list bypassv6 '2001:db8::/32 | IPv6 network'
	list bypassv6 'fe80::/10'
```

In the generated nftables rules, the bypass lists will appear with comments:

```nft
set nfq_bypass_v4 {
    type ipv4_addr; flags interval; auto-merge;
    elements = { 192.168.1.0/24 comment "Home network", 10.0.0.0/8, 172.16.0.0/12 comment "Lab network" }
}
```

### Managing bypass lists via UCI

Add an entry with description:
```bash
uci add_list netifyd.config.bypassv4='192.168.1.0/24 | My network'
uci commit netifyd
reload_config
```

Remove an entry:
```bash
uci del_list netifyd.config.bypassv4='192.168.1.0/24 | My network'
uci commit netifyd
reload_config
```

## Firewall-local traffic analysis

The `firewall_traffic` option controls how traffic to/from the firewall itself is handled. It accepts three values:

| Value | Description |
|---|---|
| `full` | Analyze all firewall traffic: inbound, outbound (firewall-initiated), and forwarded |
| `inbound` | Analyze only traffic initiated from outside toward the firewall, plus forwarded traffic (default) |
| `forward` | Analyze only forwarded traffic; ignore all firewall-local traffic entirely |

```bash
# Default: only inbound connections to the firewall + forwarded traffic
uci set netifyd.config.firewall_traffic='inbound'

# Full analysis including firewall-originated connections (e.g. DNS, monitoring)
uci set netifyd.config.firewall_traffic='full'

# Forwarded traffic only, skip all local firewall traffic
uci set netifyd.config.firewall_traffic='forward'

uci commit netifyd
reload_config
```
