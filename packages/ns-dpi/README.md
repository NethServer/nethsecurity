# ns-dpi

Manage network traffic using DPI on network flows.

How it works:
- Netify flow actions plugin adds a label to matching connections
- nft rules can block or change priority (`dscp`) to connections with labels

To enable traffic processing:
- configure `dpi` UCI database (see below for an example)
- enable DPI service:
  ```
  uci set dpi.config.enabled=1
  uci commit dpi
  /etc/init.d/dpi restart
  service netifyd reload
  ```

Global options:

- `enabled`: can be `0` or `1`, if set to `1` enable the service
- `log_blocked`: can be `0` or `1`, if set to `1` blocked connections will be logged
- `firewall_exemption`: can be `0` or `1`, if set to `1` all firewall IP addresses will be
  added to global exemption list and will not match DPI rules
- `popular_filters`: list of filters that will be returned to from `api-cli ns.dpi list-popular` call.
- `ns_exclude`: list of network interface exclusions in Netifyd that will be returned by `uci show netifyd.@netifyd[0].ns_exclude`

Rule options:

- `criteria`: DPI expression to match the traffic
  - the criteria must terminate with `;` when using complex expressions
  - use the `"` symbol to enclose strings, double-qoutes will be then translated to `'` inside the plugin configuration file (`/etc/netifyd/netify-flow-actions.json`)
- `source`: match all traffic from the given address, it accepts also an object like `<database>/<id>`;  when using an object make sure to not use complex criteria
- `action`: valid actions are:
  - `block`: matching traffic will be blocked
  - `bulk`: matching traffic will be moved to low priority QoS class named `Bulk`
  - `best_effort`: matching traffic will be moved to average priority QoS class named `Best Effort`
  - `video`: matching traffic will be moved to high priority QoS class named `Video`
  - `voice`: matching traffic will be moved to very high priority QoS class named `Voice`
- `description`: an optional rule description
- `device`: optional device name, if set the rule will be applied only to the given device, example `br-lan`
- `application`: list of applications to match, the list can contain application names like `netify.amazon-prime`
- `enabled`: can be `0` or `1`, if set to `1` the rule will be enabled
- `log`: can be set to `1` to log matching connections, gives an improved visibility on matched connections; 
  instead of logging a simple message in `/var/log/messages`, logs are stored in `/var/run/netifyd/dpi-actions-*.json`

Global exemptions options:

- `criteria`: global exemption criteria, usually it's an IP address; it can also be an object like `<database>/<id>`
- `enabled`: can be `0` or `1`, if set to `1` enable the exemption
- `description`: an optional exemption description

All enabled rules are always evaluated by netifyd, the rule order doesn't matter.

Example of `/etc/config/dpi`:
```
config main 'config'
	option log_blocked '1'
	option enabled '1'
	option firewall_exemption '1'
	list popular_filters 'netify.netflix'
	list popular_filters 'netify.telegram'
	list popular_filters 'DoT'
	list popular_filters 'netify.twitch'
	list popular_filters 'netify.teamviewer'
	list popular_filters 'DoH'

config rule
	option action 'bulk'
	option criteria 'local_ip == 192.168.100.22 && application == "netify.facebook";'
	option description 'Low priority for 192.168.100.22 when accessing Facebook'
	option enabled 1

config rule 'ns_e775b8a7'
	option enabled '1'
	option device 'br-lan'
	option action 'block'
	list application 'netify.amazon-prime'
	option description 'Block Amazon Prime for everyone'

config rule
	option action 'block'
	list application 'netify.twitter
	list application 'netify.instagram'
	list source 'objects/ns_hostset_1'
	list source 'dhcp/ns_reservation_1'
	option description 'Block Twitter and Instagrm for some hosts'
	option enabled 1

config exemption
	option criteria '192.168.1.22'
	option description 'Important host'
	option enabled '1'

config exemption
	option criteria 'dhcp/ns_271ca281'
	option description 'Important host with a reservation'
	option enabled '1'
```

QoS rules do not have any effect if qosify is not enabled.
To enable qosify use:
```
uci set qosify.wan.disabled=0
uci commit qosify
/etc/init.d/qosify restart
```

To inspect qosify status use:
```
qosify-status
```

Check if traffic is matching:
```
nft list table inet dpi
```

List connections with `block` labels:
```
conntrack -L -o label -l block
```

If needed, start netifyd in debug mode:
```
netifyd -R -d -I br-lan -E eth1
```

## Supplementary signatures

By default, netifyd is equipped to detect around 430 protocols and applications. With the inclusion of
supplementary signatures, netifyd can extend its recognition capabilities to encompass over 1600 protocols and applications.

Extra signatures are accessible only from a machine with a valid subscription.
A cron job will update DPI signatures during the night and upon machine registration.
The download will be authenticated using a Nethesis proxy.

To force the update execute:
```
dpi-update
```

You can use a different proxy by overriding the `HOST` env variable.
If the proxy is authenticated, use the `__USER__` and `__PASSWORD__` placeholders.
The placeholders will be replaced with systemd id and secret from `ns-plug`.

Example:
```
HOST=http://__USER__:__PASSWORD__@sp.gs.nethserver.net dpi-update
```

## Managing Interface Exclusions in Netifyd

By default, Netifyd monitors all interfaces. To exclude specific interfaces, you can define an exclusion list. Below are commands to add, modify, or remove excluded interfaces.

- Add interfaces to exclusion list
```
uci add_list netifyd.@netifyd[0].ns_exclude='eth1'
uci add_list netifyd.@netifyd[0].ns_exclude='tun*'
uci add_list netifyd.@netifyd[0].ns_exclude='wg*'
uci commit netifyd
echo '{"changes": {"network": {}}}' | /usr/libexec/rpcd/ns.commit call commit
```

- Modify exclusion list
```
uci delete netifyd.@netifyd[0].ns_exclude='eth1'
uci add_list netifyd.@netifyd[0].ns_exclude='eth2'
uci commit netifyd
echo '{"changes": {"network": {}}}' | /usr/libexec/rpcd/ns.commit call commit
```

- Clear exclusion list
```
uci delete netifyd.@netifyd[0].ns_exclude
uci commit netifyd
echo '{"changes": {"network": {}}}' | /usr/libexec/rpcd/ns.commit call commit
```

- Return the exclusion list
```
uci show netifyd.@netifyd[0].ns_exclude
```
