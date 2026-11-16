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
- `source`: list of addresses, networks or ranges to narrow the rule to; empty, together with
  `source_object`, means every host
- `source_object`: list of objects, in the form `<database>/<id>`, whose addresses narrow the rule, as
  an alternative to `source`: host sets, DHCP static leases, DNS records and VPN users with a reserved IP
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
	list source_object 'objects/ns_16faa17f'
```

### Objects as source

Every firewall object resolving to addresses has a netifyd address group,
`/etc/netifyd/address-groups.d/30-<database>_<id>.conf`, whether a rule uses it or not: host sets, DHCP
static leases, DNS records and VPN users with a reserved IP. A rule references the object as
`local_ip == @<database>_<id>`, so `dpi-config` only builds the criteria and never writes a group.

The files follow the objects, not the rules. They are written by `nethsec.objects.write_address_groups`:

- on commit, by the `update-address-groups.py` post-commit hook of `ns.commit`, when `objects`, `dhcp` or
  `users` change; netifyd is reloaded if a file changed
- by `ns.ovpnrw` when a VPN user gets, changes or loses its reserved IP, as it commits on its own
- at boot, by the `address-groups` service (`START=95`), before netifyd starts (`START=99`)

Each file starts with a comment holding the object name, when the object has one, followed by a comment
holding the object id and `generated from the firewall objects: do not edit`. A file is rewritten only when
its content changes. The `30-` prefix belongs to the writer: every `30-*.conf` file whose object is gone,
or has no address, is removed; files with other prefixes are never touched. An object with no address has
no file: a rule referencing it matches no host, as a missing group matches nothing. The reserved IP of a
VPN user can't be removed while the user is used as an object (`ns.ovpnrw edit-user` fails with
`reserved_ip_is_used`), so a rule can lose its addresses only when the configuration is changed outside
the API, e.g. when a whole user database is deleted.

The `30-*.conf` files are listed in `/lib/upgrade/keep.d/ns-dpi`, so they are part of the backup, of the
HA configuration sync and survive an image upgrade, always matching the configuration they come with.

netifyd keeps the groups it loaded in memory, a reload doesn't drop the ones whose file was removed, and
when it stops it saves all of them back to the directory, without comments. So after a netifyd restart
the files lose their header until the next write, and the group of a deleted object can come back as a
file: no rule references it, and the next write removes it. The write at boot runs after the stop that saved it and before the start that would load it again,
dropping it from memory too.

The addresses are written the way an address group can match them:

- ranges become CIDR blocks, as address groups ignore them. A range whose first address is greater than
  its last becomes the CIDR blocks of the ordered range; the host set itself is left as entered
- references to other objects are resolved
- IPv4-mapped IPv6 addresses (`::ffff:a.b.c.d`) become IPv4 addresses, as they never match IPv4 flows
- `0.0.0.0/0` and `::/0` become their two `/1` halves, as a zero length prefix matches nothing
- the zone of link-local addresses is dropped

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

Check the address groups of the objects:
```
head /etc/netifyd/address-groups.d/30-*
```

Write them again from the configuration:
```
/usr/libexec/ns-dpi/write-address-groups
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
