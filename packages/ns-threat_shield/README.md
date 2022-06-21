# ns-threat_shield

ns-threat_shield blocks traffic from a given list of IPs, it's based on fw4..
This is a partial porting of [nethserver-blacklist](https://github.com/NethServer/nethserver-blacklist/).

Main files:

- `/usr/sbin/ts`: sh script to apply threat shield configuration
- `/usr/sbin/ts-download`: sh script to download lists from a remote GIT repository
- `/usr/sbin/ts-nft`: this sh script oupts nft code to stdout
- `/etc/init.d/threat_shield`: start and stop threat_shield service
- `/etc/config/threat_shield`: UCI configuration file

The `threat_shield` service requires the following options:
- `url`
- `categories`
- `status`
```
uci set threat_shield.config.url=https://github.com/firehol/blocklist-ipsets.git
uci add_list threat_shield.config.categories=ciarmy
uci set threat_shield.config.status=1
uci commit
```

Apply the configuration by executing:
```
ts
```

If the machine is registered using [ns-plug](../ns-plug), the `system_id` and the `secret` will be used to authenticate requests to the git repository.

Local whitelist can be enabled by adding IP entries to the `allow` option. Example:
```
uci add_list threat_shield.config.allow=1.1.1.1
uci commit
ts
```

To change the URL, first remove existing repository:
```
rm -rf /var/ns-threat_shield/
uci set threat_shield.config.url=https://mygit.local/repo
uci commit
ts
```

To disable threat shield use:
```
uci set threat_shield.config.status=0
uci commit
ts
```
