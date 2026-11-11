# ns-dpi

Block traffic by application and protocol using the netifyd DPI engine.

How it works:
- `dpi-config` turns `/etc/config/dpi` into the netifyd flow actions config,
  `/etc/netifyd/netify-proc-flow-actions.json`
- netifyd sets a conntrack label on the flows matching a rule
- the `dpi_actions` nft chain, written by `dpi-nft` in `/usr/share/nftables.d/table-pre/`, rejects the
  flows labelled `netify-blocked`

netifyd runs all the time: traffic is filtered as soon as one rule is enabled.
Flows seen on the WAN interfaces are excluded from the DPI rules (global `iface == 'wan'` exemption, as
in the netifyd `10-nfqueue.conf`).
Rules and application groups are managed by the `ns.dpi` API, see `packages/ns-api/README.md`.
After editing `/etc/config/dpi` by hand, apply the changes with:
```
uci commit dpi
/etc/init.d/dpi reload
```

## Configuration

Global options, in the `config` section:

- `log_blocked`: `1` logs the blocked connections in `/var/log/messages`, with the `DPI block: ` prefix

Application group (`appgroup` section), a named set of members:

- `ns_name`: name of the group
- `app`: list of application names, as reported by the engine (e.g. `netify.netflix`)
- `app_category`: list of application category tags (e.g. `games`)
- `proto`: list of protocol names, as reported by the engine (e.g. `HTTP/Connect`)
- `proto_category`: list of protocol category tags

Rule (`rule` section):

- `ns_name`: name of the rule
- `enabled`: `0` or `1`
- `action`: `block` or `allow`
- `priority`: evaluation order, starting at `1`; the first rule matching a flow wins
- `appgroup`: list of application groups to match
- `source`: list of addresses, networks or ranges to narrow the rule to; empty means every host
- `ns_match_all`: `1` matches every flow instead of naming application groups
- `ns_managed`: `1` for the rules created by the API
- `criteria`: raw netifyd expression, used by the rules not created by the API; the API can't edit them

Example:
```
config main 'config'
	option log_blocked '1'

config appgroup 'ns_1a2b3c4d'
	option ns_name 'Streaming and games'
	list app 'netify.netflix'
	list app_category 'games'

config rule 'ns_3869dc35'
	option ns_name 'Allow the office'
	option ns_managed '1'
	option enabled '1'
	option action 'allow'
	option priority '1'
	option ns_match_all '1'
	list source '192.168.1.10'

config rule 'ns_9d40be71'
	option ns_name 'Block streaming and games'
	option ns_managed '1'
	option enabled '1'
	option action 'block'
	option priority '2'
	list appgroup 'ns_1a2b3c4d'
	list source '192.168.1.0/24'
```

## Migration from the previous schema

On upgrade, and every time the DPI service starts, `/usr/libexec/ns-dpi/dpi-migrate` converts the
configuration written before application groups existed, e.g. after restoring an old backup:

- every rule with `device`, `application`, `protocol` or `category` becomes an unmanaged rule, with its
  behaviour kept in `criteria`. Rules with an action other than `block`, such as the QoS ones (`bulk`,
  `best_effort`, `video`, `voice`), and rules matching nothing are dropped. The per-rule `exemption` and
  `log` options are removed
- every `exemption` section becomes an `allow` rule at the top of the list, named after the exemption
  description
- `popular_filters` is removed

Dropped rules and removed options are logged in `/var/log/messages`. The `enabled` and `firewall_exemption`
global options, which no longer switch anything, are removed on upgrade as well.

## Troubleshooting

Check the generated rules:
```
cat /etc/netifyd/netify-proc-flow-actions.json
nft list chain inet fw4 dpi_actions
```

List the blocked connections:
```
conntrack -L -o label -l netify-blocked
```

## Signatures and catalogs

- `dpi-update` downloads the extra signatures, available only with a valid subscription, every night;
  run it by hand to force an update. On unregistration the extra signatures are removed and the ones
  shipped with the image are restored
- `dpi-data-update` downloads the application and protocol catalogs (labels, categories, icons) into
  `/etc/netifyd`, every night
