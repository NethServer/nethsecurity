# ns-threat_shield

This is a porting of [nethserver-blacklist](https://github.com/NethServer/nethserver-blacklist/).

This package is composed of 2 different services:

- [ts-ip](#ts-ip): block traffic from/to a given list of IPs, it is based on banip
- [ts-dns](#ts-dns): block DNS queries to a given list of domains, it is based on adblock

If the machine is registered using [ns-plug](../ns-plug), the `system_id` and the `secret` will be used to authenticate requests to URL sources.
Please note that to access the extra categories, the machine should have a valid entitlement for this service.

## ts-ip

Threat shield IP (`ts-ip`) blocks traffic from/to a given list of IPs.

The following categories require a valid entitlement:

- `yoroimallvl1` (was `yoroi_malware_level1` on NS7)
- `yoroimallvl2` (was `yoroi_malware_level2` on NS7)
- `yoroisusplvl1` (was `yoroi_souspicious_level1` on NS7)
- `yoroisusplvl2` (was `yoroi_souspicious_level2` on NS7)
- `nethesislvl3` (was `nethesis_level3` on NS7)
- `nethesisinsightslvl2` (attackers reported by the other Nethesis firewalls, see [Nethesis Insights](#nethesis-insights))

After machine registration, above categories will be automatically added to existing banip categories (`/etc/banip/banip.custom.feeds`).

A special global allowlist will also be added to banip (`ban_allowurl` option).

### Examples

#### Start the service

Enable the service and select one or more categories to block:
```
uci add_list banip.global.ban_feed=yoroimallvl1
uci set banip.global.ban_enabled=1
uci commit banip
ts-ip
/etc/init.d/banip restart
```

To disable `ts-ip` use:
```
uci set banip.global.ban_enabled=1
uci commit banip
ts-ip
/etc/init.d/banip restart
```

### Nethesis Insights

On registered machines `ts-ip` joins the [Nethesis Insights](https://github.com/nethesis/nethesis-insights)
threat shield: IPs banned by [fail2ban](#fail2ban) are reported to the Insights server, and IPs reported by
several firewalls can be blocked locally with the `nethesisinsightslvl2` feed.
Authentication uses the subscription `system_id` and `secret`.

| machine | allowlist | reports blocked IPs | `nethesisinsightslvl2` feed |
|---|---|---|---|
| no subscription | no | no | not available |
| subscription | yes | yes | not listed |
| subscription with the Threat Shield entitlement | yes | yes | selectable, disabled by default |

Reporting:

- each new fail2ban ban is reported in background; a report that fails is dropped and logged to `/var/log/messages`
  (tag `threat_shield`)
- the endpoint URL can be overridden with `ns-plug.config.insights_blocklist_url`
  (default `https://insights.nethesis.it/blocklist/v1/events`)
- to stop reporting or to log every report see `ns_insights_report` and `ban_debug` in [fail2ban](#fail2ban)

## fail2ban

Brute force detection for `ts-ip` is done by the upstream
[fail2ban](https://github.com/openwrt/packages/tree/openwrt-25.12/net/fail2ban) package: it reads `/var/log/messages`
and bans offending IPs in the nftables table `inet f2b-table`.

| jail | detects | bans after |
|---|---|---|
| `ns-ssh` | SSH login failures | 5 in 10m |
| `ns-webui` | web UI and API login failures | 8 in 1h |
| `ns-openvpn` | road warrior authentication and TLS handshake failures | 6 in 10m |
| `ns-proxy-auth` | reverse proxy 403 and Basic auth 401 responses | 6 in 10m |
| `ns-proxy-scan` | reverse proxy and web UI 404 responses | 20 in 2m |

Never banned: loopback, the networks of non-WAN interfaces, the IP and CIDR entries of the banIP allowlist
and the firewall's own addresses.

### UCI options

Options of `banip.global`, applied on `ns.commit` (from the command line run `/usr/libexec/ts-fail2ban`):

| option | effect |
|---|---|
| `ban_enabled` | `1`: run fail2ban if at least one jail is enabled |
| `ban_loglimit` | `> 0`: enable the jails listed in `ns_jails` |
| `ns_jails` | jails to enable, all five on a fresh install |
| `ban_nftexpiry` | ban duration, e.g. `30m`, `1h`, `3d` (default `30m`) |
| `ns_insights_report` | `0`: do not report bans to [Nethesis Insights](#nethesis-insights), bans still apply |
| `ban_debug` | `1`: log every Insights report |

### Bans

Check status:
```
fail2ban-client status
fail2ban-client status ns-webui
nft list table inet f2b-table
```

Unban an IP:
```
fail2ban-client unban 203.0.113.7
```

- bans are lost on reboot
- a ban drops all traffic from the IP, also replies to connections opened by the firewall or LAN hosts
- allowlisting a banned IP frees it, but the ban can come back if the IP leaves the allowlist before the ban expires
- `ns-proxy-auth` does not cover the web UI and the path rules on the `_lan` server: their access log has only 404 responses
- `ns-proxy-auth` counts 401 responses only for Basic auth

### Custom jails

Add the jail in `/etc/fail2ban/jail.d/` and its filter in `/etc/fail2ban/filter.d/`; do not edit
`90-ns-threat_shield.local`, it is generated. Custom jails default to `maxretry = 3` and `findtime = 10m`,
and run only while at least one NethSecurity jail is enabled.
Example `/etc/fail2ban/jail.d/50-custom.local`:
```
[custom-app]
enabled = true
filter = custom-app
action = %(ns_banaction)s
         ns-insights[scenario=custom/app-bruteforce]
```
Without `action` the jail bans the same way but does not report to Insights. Apply with `fail2ban-client reload`.

## ts-dns

Threat shield DNS (`ts-dns`) is a special configuration for [adblock](https://github.com/openwrt/packages/tree/master/net/adblock).
The `ts-dns` is invoked every time adblock is started or reloaded.

The package adds new options to `adblock`:

- `ts_enabled`: if set to `1`, it enables the download of enterprise categories and community free categories.
- `ns_tsdns_zones`: the firewall zones where the local DNS enforcement is applied.

Since adblock 4.5.5 the enforcement is rendered as nft rules matching on `iifname`, so the
`adb_nftdevforce` option needs network devices and not zone names. It is therefore a derived
value: it is computed from `ns_tsdns_zones` by the API and kept aligned with the network setup
by the `configure-adblock-devices` pre-commit hook, so that adding an interface to an enforced
zone does not leave its DNS traffic unfiltered. Do not edit `adb_nftdevforce` by hand.

If `ts_enabled` is set to 1:

- a new category source file is generated according to the machine registration and the entitlement
- all DNS queries are redirected to the local machine
- adblock is configured to use the new category source file and will be started

As default a machine has access to all community free categories, that are listed at `/usr/share/threat_shield/community-dns.sources.gz`.
If the machine has a subscription and a valid entitlement for nethesis-blacklists, the machine will have access to the enterprise categories, 
that are listed at `/usr/share/threat_shield/nethesis-dns.sources.gz`.

DNS block categories will be automatically reloaded every 12 hours.

Enable adblock with all available categories, example:
```
echo '{"enabled": true, "zones": ["lan"]}' | /usr/libexec/rpcd/ns.threatshield call dns-edit-settings
uci commit adblock && service adblock restart
```

Keep adblock enabled but disable threat shield categories:
```
echo '{"enabled": false, "zones": ["lan"]}' | /usr/libexec/rpcd/ns.threatshield call dns-edit-settings
uci set adblock.global.ts_enabled=0
uci commit adblock
/etc/init.d/adblock restart
```

### DNS redirect bypass

Allow bypass of DNS redirect for a specific source IP:
```
uci add_list adblock.global.ns_tsdns_bypass=192.168.100.2
uci commit adblock
/etc/init.d/adblock reload
```

For more info see [adblock repository](https://github.com/openwrt/packages/tree/master/net/adblock).
