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

After machine registration, above categories will be automatically added to existing banip categories (`/etc/banip/banip.custom.feeds`).

A special global allowist will also be added to banip (`ban_allowurl` option).

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

## ts-dns

Threat shield DNS (`ts-dns`) is a special configuration for [adblock](https://github.com/openwrt/packages/tree/master/net/adblock).
If `adblock` is enabled and the machine has a valid subscription, the following extra block categories will be available:

- `yoroi_malware_level1`
- `yoroi_malware_level2`
- `yoroi_susp_level1` (was `yoroi_suspicious_level1` on NS7)
- `yoroi_susp_level2` (was `yoroi_suspicious_level2` on NS7)

The package adds a new option to `adblock`:

- `ts_enabled`: if set to `1`, it enables the download of threat shield DNS categories

Extra categories are loaded from `/usr/share/threat_shield/nethesis-dns.sources.gz` and require a valid entitlement.
DNS block categories will be automatically reloaded every 12 hours.

Enable adblock with threat shield categories, example:
```
uci set adblock.global.ts_enabled=1
uci set adblock.global.adb_enabled=1
uci add_list adblock.global.adb_sources=yoroi_malware_level1
uci add_list adblock.global.adb_sources=yoroi_malware_level2
uci add_list adblock.global.adb_sources=yoroi_susp_level1
uci add_list adblock.global.adb_sources=yoroi_susp_level2
uci commit adblock
/etc/init.d/adblock start
```

Keep adblock enabled but disable threat shield categories:
```
uci set adblock.global.ts_enabled=0
uci commit adblock
/etc/init.d/adblock reload
```

Allow bypass of DNS redirect for a specific source IP:
```
uci set adblock.global.adb_forcedns=1
uci add_list adblock.global.adb_bypass=192.168.100.2
uci add_list adblock.global.adb_zonelist=lan
uci add_list adblock.global.adb_portlist=53
uci commit adblock
/etc/init.d/adblock restart
```

For more info see [adblock repository](https://github.com/openwrt/packages/tree/master/net/adblock).
