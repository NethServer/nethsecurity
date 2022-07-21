# ns-threat_shield

This is a porting of [nethserver-blacklist](https://github.com/NethServer/nethserver-blacklist/).

This package is composed of 2 different services:

- [ts-ip](#ts-ip): block traffic from/to a given list of IPs
- [ts-dns](#ts-dns): block DNS queries to a given list of domains

Both services use the adblock JSON file format for category souces.
Source files are gzipped to preserve space.
If the machine is registered using [ns-plug](../ns-plug), the `system_id` and the `secret` will be used to authenticate requests to URL sources.
Please note that to access the extra categories, the machine should have a valid entitlement for this service.

## ts-ip

Threat shield IP (`ts-ip`) blocks traffic from/to a given list of IPs, it's based on fw4.

Main files:

- `/usr/sbin/ts-ip`: sh script to apply threat shield configuration
- `/usr/sbin/ts-ip-download`: sh script to download lists from a remote GIT repository
- `/usr/sbin/ts-ip-nft`: sh script to print nftables code to stdout
- `/etc/init.d/ts-ip`: start and stop threat shield IP service
- `/etc/config/threat_shield`: UCI configuration file

Available options:

| Option             | Default                            | Description/Valid Values                                                                       |
| :----------------- | :--------------------------------- | :--------------------------------------------------------------------------------------------- |
| status             | 1, enabled                         | set to 0 to disable the ts-ip service                                                          |
| categories         | -                                  | list of enabled block categories                                                               |
| allow              | -                                  | list of IP addresses always allowed                                                              |
| log_blocked        | 0, disabled                        | set to 1 to enable the logging of blocked packets. Log prefix: ts:_category_:_direction_.      |
| srcarc             | -, /usr/share/threat_shield/nethesis-ip.sources.gz | full path to the used source archive                                           |


The following categories require a valid entitlement:

- `yoroi_malware_level1`
- `yoroi_malware_level2`
- `yoroi_susp_level1` (was `yoroi_suspicious_level1` on NS7)
- `yoroi_susp_level2` (was `yoroi_suspicious_level2` on NS7)
- `nethesis_level3`

If a category is named `whitelist`, it will be used a global whitelist and all IP inside it will always be allowed.

### Examples

#### Start the service

Enable the service and select one or more categories to block:
```
uci add_list threat_shield.config.categories=yoroi_malware_level1
uci set threat_shield.config.status=1
uci commit
ts-ip
```

To disable `ts-ip` use:
```
uci set threat_shield.config.status=0
uci commit
ts-ip
```

#### Local whitelist

The local whitelist can be enabled by adding IP entries to the `allow` option. Example:
```
uci add_list threat_shield.config.allow=1.1.1.1
uci commit
ts-ip
```

#### Logging

To enable logging of blocked packets:
```
uci set threat_shield.config.log_blocked=1
uci commit
ts-ip
```

Log lines have a prefix like `ts:_category_:_direction_`, where `direction` can be `src` or `dst`.
Example of a log line:
```
Jul 21 08:48:34 nstest kernel: [26244.356917] ts:yoroi_malware_level1:dst IN= OUT=eth0 SRC=192.168.122.40 DST=217.70.184.38 LEN=84 TOS=0x00 PREC=0x00 TTL=64 ID=15590 DF PROTO=ICMP TYPE=8 CODE=0 ID=21415 SEQ=0 MARK=0x3e00
```

#### Replace sources file

To use a different sources file, copy the original one to a different path, then modify it.
Finally, set up the source archive path. Example:
```
uci set threat_shield.config.srcarc=/usr/share/threat_shield/mysources.gz
uci commit
ts-ip
```

## ts-dns

Threat shield DNS (`ts-dns`) is a wrapper around [adblock](https://github.com/openwrt/packages/tree/master/net/adblock).
If `adblock` is enabled and the machine has a valid subscription, the following extra block categories will be available:

- `yoroi_malware_level1`
- `yoroi_malware_level2`
- `yoroi_susp_level1` (was `yoroi_suspicious_level1` on NS7)
- `yoroi_susp_level2` (was `yoroi_suspicious_level2` on NS7)


Extra categories are loaded from `/usr/share/threat_shield/nethesis-dns.sources.gz` and require a valid entitlement.

Usage example:
```
/etc/init.d/ts-dns start
```

DNS block categories will be automatically reloaded every 12 hours.

For more info see [adblock repository](https://github.com/openwrt/packages/tree/master/net/adblock).
