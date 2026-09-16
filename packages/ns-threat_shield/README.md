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
- `nethesisinsights` (attackers reported by the other Nethesis firewalls, see [Nethesis Insights](#nethesis-insights))

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

If the machine is registered, `ts-ip` also joins the [Nethesis Insights](https://github.com/nethesis/nethesis-insights)
threat shield: every IP blocked by the banip log service is reported to the Insights server, and the
list aggregated from the reports of all registered firewalls is blocked locally.
Both directions authenticate with the `system_id` and `secret` of the subscription: no additional
configuration is required and nothing is sent from a machine which is not registered.

Reporting side:

- `ts-ip` sets `banip.global.ban_blockhook` to `/usr/libexec/ts-insights-hook`; banip calls it once
  for every IP added to a blocklist Set by the log service
- the hook only appends a JSON line to `/var/run/ns-insights/threat-events.jsonl`, so that a burst
  of blocked IPs never slows down the banip log service
- `/usr/sbin/ts-insights-report` is executed every 5 minutes by cron: it sends the spooled events to
  `POST /v1/threat-events` in batches of at most 500, then writes the outcome to
  `/var/run/ns-insights/last_push.json`
- only globally routable addresses are reported: private, CGNAT, link-local, reserved and
  documentation ranges are dropped locally, along with the events older than 2 hours
- on a failed push the events are kept in the spool and sent again at the next run, duplicated
  reports are discarded by the server

Blocking side:

- the `nethesisinsights` feed points to `GET /v1/blocklist`, it is added to `ban_feed` on
  registration and it is reloaded with all the other feeds every 4 hours
- an IP is published by the server only after it has been reported by several distinct firewalls,
  and it expires when nobody reports it any more

On unregistration the hook and the feed are both removed.

Check the last report, example:
```
cat /var/run/ns-insights/last_push.json
```

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
