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
  service netifyd restart
  ```

Global options:

- `enabled`
- `log_blocked`
- `firewall_exemption`

Rule options:

- `action`: valid actions are:
  - `block`
  - `bulk`
  - `best_effort`
  - `video`
  - `voice`
- `description`
- `enabled`


All enabled rules are always evaluated by netifyd, order doesn't matter.

Example of `/etc/config/dpi`:
```
config main 'config'
	option log_blocked '1'
	option enabled '1'

config rule
	option action 'bulk'
	option criteria 'ai:netify.twitter'
    option description 'Block Twitter for everyone'
	option enabled 1

config rule
	option action 'block'
	option criteria 'local_ip == 192.168.100.22 && application == "netify.facebook";'
	option enabled 1
```

Notes on `criteria` option syntax:
- the criteria must terminate with `;` when using complex expressions
- the `"` is translated to `'` inside the plugin configuration file (`/etc/netify.d/netify-flow-actions.json`)


To enable the `bulk` rule, you must enable qosify and change its default config:
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
