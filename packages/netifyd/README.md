# netifyd

Netifyd is a network intelligence platform that provides DPI (Deep Packet Inspection) analysis and network flow monitoring. This package integrates netifyd into NethSecurity for real-time network traffic analysis.

For detailed information, visit [https://www.netify.ai/](https://www.netify.ai/).

## NFQueue capture

On start, `ns-netifyd-configure start` writes `/etc/netifyd/interfaces.d/10-nfqueue.conf` and builds the `inet netifyd` nft table.
There's one queue per CPU core for each role, between 2 and 8: LAN (forward chain) uses the queues from 50, WAN (input and output chains) the ones from 58.
The table isn't removed when netifyd stops: `queue flags bypass` lets the packets through when nobody is listening.

The table comment is a hash of its chains. The table is rebuilt only when it no longer matches the configuration, otherwise only the bypass sets are refreshed, so the script is safe to run again.
A reload refreshes the bypass sets, and restarts netifyd when the table changed (for example after a `firewall_traffic` change), since a chain can't be removed while netifyd is reading its queue.
Run `ns-netifyd-configure --help` for the details.

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
Invalid addresses are skipped with a warning, double quotes are removed from descriptions and descriptions are cut at 128 characters.

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

The `firewall_traffic` option is a list of nftables chains to add for DPI analysis. Valid chain names are:

| Chain     | Description                                                                             |
| --------- | --------------------------------------------------------------------------------------- |
| `input`   | Analyze traffic destined for the firewall itself                                        |
| `output`  | Analyze traffic originated by the firewall itself (e.g., DNS queries, monitoring pings) |
| `forward` | Analyze traffic passing through the firewall (transit traffic)                          |

By default (if the option is missing or empty after validation), all three chains are enabled.

Invalid chain names trigger a warning and are skipped. If all values are invalid, the configuration falls back to enabling all chains with a warning.

### Examples

```bash
# Default: all three chains enabled
uci delete netifyd.config.firewall_traffic
uci commit netifyd
reload_config

# Analyze only forwarded traffic
uci del_list netifyd.config.firewall_traffic
uci add_list netifyd.config.firewall_traffic='forward'
uci commit netifyd
reload_config

# Analyze input and forward, skip firewall-originated traffic
uci del_list netifyd.config.firewall_traffic
uci add_list netifyd.config.firewall_traffic='input'
uci add_list netifyd.config.firewall_traffic='forward'
uci commit netifyd
reload_config

# Full analysis: all chains
uci del_list netifyd.config.firewall_traffic
uci add_list netifyd.config.firewall_traffic='input'
uci add_list netifyd.config.firewall_traffic='output'
uci add_list netifyd.config.firewall_traffic='forward'
uci commit netifyd
reload_config
```

## Monitoring

The package ships `/etc/telegraf.conf.d/netifyd.conf`. Every 60 seconds Telegraf reads `/var/run/netifyd/status.json`, which netifyd rewrites every 15 seconds. When netifyd is stopped the file is missing and Telegraf logs an error for this input.

Metrics:
```
netifyd_flows_in_use = flow table entries in use (also flow_count, flows_active, flows_expiring, flows_expired, flows_purged)
netifyd_lan_flow_dropped, netifyd_wan_flow_dropped = flows dropped, either because the flow table is full or the system is under load
netifyd_plugin_license_status_id{plugin="proc-nfa", license_status="valid"} = 3 when valid
```

Plugins that don't report a status (core processor, sinks) are skipped.
