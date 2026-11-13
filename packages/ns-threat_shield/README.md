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

Blocks are counted from the banIP kernel log lines in Victoria Logs, not from metrics, as `ns.dashboard counter` and
`ns.controller dump-ts-malware` do; blocks per feed in the last hour:
`app_name:kernel "banIP/" | extract "banIP/<chain>/<verdict>/<feed>: " | filter feed:* | stats by (feed) count() blocked`

### Custom allowlists and blocklists

`ts-ip` owns `banip.global.ban_allowurl` and `/etc/banip/banip.custom.feeds` and rebuilds them from UCI.
With ns-plug credentials the Nethesis allowlist URL is always the first `ban_allowurl` entry: it can't be disabled and it is never stored in UCI, because the credentials rotate.

| UCI (`banip`) | options | effect |
|---|---|---|
| `config ns_allowurl '<name>'` | `url`, `description`, `enabled` | enabled URLs added to `ban_allowurl` |
| `config ns_blockfeed '<name>'` | `url_4`, `url_6`, `chain` (`in`, `out`, `inout`), `description` | feed added to `banip.custom.feeds` with `"rule": "feed 1"` (one IP/CIDR per line); enabled when `<name>` is in `global.ban_feed` |

`banip.custom.feeds` content:

| ns-plug credentials | custom feeds | file |
|---|---|---|
| yes | any | `banip.feeds` + `banip.nethesis.feeds` + custom feeds |
| no | yes | `banip.feeds` + custom feeds |
| no | no | empty, banip uses `banip.feeds` |

- custom feed names must not start with `yoroi` or `nethesis`: those names are removed from `ban_feed` on units without credentials
- allowlist names follow the custom blocklist name rules and share the same namespace (banip section names)
- `banip.custom.feeds` is replaced only by a complete and changed file: banip removes from `ban_feed` the feeds missing from it
- a non-empty `banip.custom.feeds` holds copies of `banip.feeds` (and `banip.nethesis.feeds` when registered), which banip then ignores: uci-defaults `95-banip-housekeeping` (banip upgrade) and `97-nethsec-banip-feeds` (ns-threat_shield upgrade) refresh it with `ts-ip --no-start` (no fail2ban restart)
- the `adjust-banip.py` post-commit hook runs `ts-ip` before restarting banip when `banip` changes, and removes from `/tmp/banIP-backup` the backups of the changed lists (`banIP.allowlist.gz`, `banIP.<name>.v4.gz`, `banIP.<name>.v6.gz`): banip start restores backups instead of downloading
- when `global.ns_allowurl_migrated` is not `1`, `ts-allowurl-migrate` (run on install/upgrade as uci-defaults `97-nethsec-banip-allowurl`, and by every `ts-ip` run, so a restored old backup is migrated on the next banip commit or register/unregister) moves the non-Nethesis `ban_allowurl` entries into `ns_allowurl` sections named `allow<n>` and sets it
- APIs: `ns.threatshield` `*-allowlist-url(s)`, `*-custom-blocklist` and `list-blocklist`, see [ns-api](../ns-api/README.md#nsthreatshield)

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
- only public addresses are reported: private, CGNAT, link-local, loopback and other non-global IPv4/IPv6 addresses are skipped
- the endpoint URL can be overridden with `ns-plug.config.insights_blocklist_url`
  (default `https://insights.nethesis.it/blocklist/v1/events`)
- to stop reporting or to log every report see `ns_insights_report` and `ban_debug` in [fail2ban](#fail2ban)

## fail2ban

Brute force detection for `ts-ip` is done by the upstream
[fail2ban](https://github.com/openwrt/packages/tree/openwrt-25.12/net/fail2ban) package: it reads `/var/log/messages`
and bans offending IPs in the nftables table `inet f2b-table`.

| jail | detects | bans after |
|---|---|---|
| `ns-ssh` | SSH login failures and disconnects before login | 3 in 10m |
| `ns-webui` | web UI and API login failures | 8 in 1h |
| `ns-openvpn` | road warrior authentication and TLS handshake failures | 6 in 10m |
| `ns-proxy-auth` | reverse proxy 403 and Basic auth 401 responses | 6 in 10m |
| `ns-proxy-scan` | reverse proxy and web UI 404 responses, static files excluded | 20 in 2m |

Never banned: loopback, the static networks of non-WAN interfaces (not DHCP or delegated IPv6 prefixes), the banIP allowlist
(its IP and CIDR entries and its nft sets, downloaded `ban_allowurl` feeds included) and the firewall's own addresses.

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
- bans survive firewall reloads: fw4 never touches `inet f2b-table`, so the upstream firewall include that restarts fail2ban is not installed (`patches/feeds/packages/100-fail2ban-no-firewall-include.patch`)
- fail2ban logs to `/var/log/messages` at `NOTICE` level: bans, unbans and errors only, not every failed attempt
- bans are counted from the `Ban` lines in Victoria Logs, not from metrics, as `ns.controller dump-ts-attacks` and `ns.report tsip-attack-report` do; bans per jail:
  `app_name:"fail2ban.actions" "] Ban " | extract "[<jail>] Ban <ip>" | stats by (jail) count() bans`
- a ban drops all traffic from the IP, also replies to connections opened by the firewall or LAN hosts
- adding a banned IP to the local allowlist frees it (downloaded allowlists only prevent new bans), but the ban can come back if the IP leaves the allowlist before the ban expires
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
