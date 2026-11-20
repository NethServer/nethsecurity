---
name: ns-firewall-integration
description: Make a NethSecurity package or API change the firewall the right way — fw4 UCI rules, zones and forwardings through `nethsec.firewall`, or raw nftables snippets auto-included by fw4. Use whenever a task opens a port, allows or blocks traffic, adds a zone, forward, NAT/redirect or netmap rule, marks/labels/logs packets (ct label, dscp, nflog), touches `/etc/config/firewall`, `/usr/share/nftables.d`, `/etc/nftables.d`, `fw4`, `nft`, `ns_tag`, `ns_link`, `system_rule`, or the templates database, even when the user only says "the service needs to be reachable", "block this", "add a rule" or "firewall".
metadata:
  domain: nethsecurity-packages
  type: runtime
---

## How the firewall is built

fw4 (firewall4, pinned at `b6e5157` in OpenWrt v25.12.5) renders `/etc/config/firewall` plus the include files into one ruleset for `table inet fw4`. `fw4 reload` loads it in a single `nft -f` transaction that starts with `flush table inet fw4`. As a consequence:

- Anything added to `inet fw4` at runtime with `nft add ...` is wiped on the next reload. Every rule in that table must come from UCI or an include file.
- If the rendered ruleset has an error, the whole transaction fails. On reload the old ruleset stays loaded. At boot nothing gets loaded, so the box has **no firewall at all**.
- Other tables (`inet banIP`, `inet netifyd`) are untouched by `fw4 reload`. `fw4 flush` deletes every table.

`ns.commit` runs `reload_config` after committing, which reloads the firewall when `firewall` changed. APIs only stage changes.

## Pick the mechanism

| Need | Mechanism |
|---|---|
| Open a port on the firewall, allow/deny between zones, port forward, SNAT/masquerade, zone, forwarding | fw4 UCI via `nethsec.firewall`, tagged `automated` and linked to its owner |
| Something fw4 UCI can't express: ct labels, dscp/marks, nflog, custom chains or hooks | nft snippet in `/usr/share/nftables.d/` |
| Snippet content depends on UCI | generate the snippet from UCI, `fw4 reload` only when the content changed |

The default for non-UCI rules is a snippet inside `inet fw4`, not a separate table. It's atomic with the rest of the ruleset, can reference fw4 sets and chains, and survives reloads. `banIP` and `netifyd` have their own tables because they come from upstream. Don't take them as a model for `ns-*` code.

## References

- `references/fw4-uci.md`: every option of every fw4 section type (`defaults`, `zone`, `forwarding`, `rule`, `redirect`, `nat`, `ipset`, `include`), value formats, unsupported options, and the NethSecurity `ns_*` options. Read it before setting any firewall option by hand, or when a helper doesn't cover what you need. Don't guess option names, since fw4 only warns about unknown ones and ignores them.
- nftables syntax for snippets: https://wiki.nftables.org/wiki-nftables/index.php/Quick_reference-nftables_in_10_minutes. Check the `nft` version on the device (`nft --version`) before using newer statements.

## fw4 UCI from Python

Use `nethsec.firewall` (`packages/python3-nethsec/src/nethsec/firewall/__init__.py`) from APIs and scripts. Read the function before relying on it; signatures and defaults matter.

| Function | Use |
|---|---|
| `add_service(uci, name, port, proto, link)` | ACCEPT rule from `wan` to the device for a service port; section id `ns_allow_<name>` |
| `remove_service` / `disable_service` | remove / disable it |
| `add_template_rule(uci, name, proto, port, link)` | rule from a `template_rule` in the templates database (`docs/design/templates_database.md`) |
| `add_template_zone`, `add_template_forwarding`, `add_template_service_group` | zones, forwardings and service groups from templates |
| `add_trusted_zone`, `add_vpn_interface`, `add_device_to_zone`, `add_interface_to_zone` | VPN/LAN wiring |
| `add_rule` / `edit_rule` / `delete_rule`, `add_nat_rule`, `add_netmap_rule` | user-facing rules, as the `ns.firewall`/`ns.nat` APIs do |
| `get_all_linked`, `disable_linked_rules`, `delete_linked_sections` | find, disable or remove everything a feature created |

Conventions these helpers already apply. Follow them when you set options by hand:

- **IDs**: `ns_` prefix, from `utils.get_id(name)` (stable, derived from a name) or `utils.get_random_id()`. Zones are `ns_<zonename>`.
- **`ns_tag` list**: `automated` marks a rule the system created. `enrich_rule` turns it into `system_rule: true`, and the UI warns before the user edits such a rule. Every rule a package or API creates on its own carries `automated`.
- **`ns_link`**: `<config>/<section>` of the object that owns the rule (e.g. `network/wg1`, `openvpn/ns_roadwarrior1`). When that object is deleted, call `delete_linked_sections(uci, link)` so its firewall rules, zones and forwardings go with it. Without a link, rules leak.
- **Order**: the helpers call `reorder_firewall_config`, which keeps defaults/includes, zones, forwardings, then forward, output and input rules. Section order is rule order.
- **No commit**: helpers `uci.save('firewall')` only. `firewall.apply()` commits and reloads; use it only in scripts outside the API flow.

`nethsec.firewall.enable_service()` currently sets `enabled` to `'0'` (same as `disable_service`). Set `enabled` to `'1'` directly until it's fixed.

## nft snippets in `/usr/share/nftables.d`

fw4 auto-includes every readable `*.nft` file here. The position comes from the directory:

| Directory | Included | Content |
|---|---|---|
| `ruleset-pre/`, `ruleset-post/` | before/after `table inet fw4 { ... }` | whole statements at ruleset level (`table ...`, `define ...`) |
| `table-pre/`, `table-post/` | inside `inet fw4`, before the first / after the last chain | chain, set, map declarations |
| `chain-pre/<chain>/`, `chain-post/<chain>/` | inside chain `<chain>` of `inet fw4`, before the first / after the last rule | rule lines only |

- `<chain>` is a chain fw4 renders: `input`, `forward`, `output`, `prerouting`, `dstnat`, `srcnat`, `mangle_*`, or zone chains like `input_lan`, `forward_wan`, `dstnat_lan`. If the chain doesn't exist (zone not configured), the file is simply not included.
- Files in one directory are included in name order; use `NN-ns-foo.nft`.
- A chain declared in `table-pre` with its own `hook` and `priority` runs alongside fw4's chains (`filter` = 0 for input/forward/output). That's how `dpi_actions` hooks `prerouting` at `filter + 10`.
- Snippets can reference fw4's named sets and chains, since they're in the same table.
- `/etc/nftables.d/` is the **user's** directory: same table context, kept on sysupgrade. Packages never write there.

Static snippet (`ns-don`):

```makefile
	$(INSTALL_DIR) $(1)/usr/share/nftables.d/chain-pre/input
	$(INSTALL_DATA) ./files/20-ns-foo.nft $(1)/usr/share/nftables.d/chain-pre/input/
```

```
iifname "tunFOO" tcp dport 9443 counter accept comment "ns-foo"
```

Package files are reinstalled and removed by apk, so a static snippet needs no cleanup. After install and removal, the firewall needs a reload to pick up the change. Do it in `postinst` and `prerm` under the `IPKG_INSTROOT` guard.

### Generated snippets

When the rules depend on UCI, a one-shot (see `ns-background-work`) renders the snippet and reloads fw4 **only if the content changed**. A reload re-renders everything, so skipping no-op reloads matters:

```python
NFT_FILE = '/usr/share/nftables.d/table-pre/20-ns-foo.nft'

def write_snippet(render):
    current = None
    if os.path.exists(NFT_FILE):
        with open(NFT_FILE) as f:
            current = f.read()
    if current == render:
        return
    os.makedirs(os.path.dirname(NFT_FILE), exist_ok=True)
    with open(NFT_FILE, 'w') as f:
        f.write(render)
    if subprocess.run(['fw4', '-q', 'check']).returncode != 0:
        # fw4 refuses to reload a broken ruleset, and at boot it wouldn't load at all
        if current is None:
            os.remove(NFT_FILE)
        else:
            with open(NFT_FILE, 'w') as f:
                f.write(current)
        raise RuntimeError('invalid_nft_snippet')
    subprocess.run(['fw4', '-q', 'reload'], check=True)
```

- When the feature is disabled, remove the file (and reload) instead of writing an empty one.
- The file isn't owned by the package, so `prerm` must delete it and reload the firewall. `ns-dpi` and `ns-netmap` don't do this yet.
- Render with Jinja2 or plain string building. Any value that comes from UCI or user input must be validated before it reaches nft syntax (IPs, ports, interface names).

## Don't copy

- `firewall.ns_hs_include` (dedalo, `type script`, `/opt/icaro/dedalo/dedalo.user`, created from the Makefile postinst) and `firewall.ns_user_include` (`/etc/firewall.user`). Script includes are fw3-era: they run shell after the ruleset loads and need `fw4_compatible`. Use an nft snippet.
- `ns-binding` managing its own `table inet ns-binding` and deleting it in `stop_service`. Use a generated snippet in `inet fw4`.
- `nethsec.firewall.enable_service()`, see above.

Good references: `ns-don` (static chain snippet), `ns-dpi/files/dpi-nft` (generated `table-pre` chain with change detection), `ns-netmap/files/ns-netmap` (generated `chain-pre/srcnat` and `chain-post/dstnat` rules). Copy the generation, but add the validation and prerm cleanup they lack.

## Verify on a device

```sh
fw4 check                          # renders the ruleset and runs nft -c
fw4 print | less                   # rendered ruleset, includes expanded
nft list chain inet fw4 input      # what's actually loaded
uci show firewall | grep -E 'ns_tag|ns_link'
logread -e firewall
```

Check behavior after `fw4 reload` and after a reboot. A rule that only exists until the next reload was added at runtime, not through UCI or a snippet.

## Sources

- firewall4 at the pinned commit (`root/usr/share/ucode/fw4.uc` for includes, `root/usr/share/firewall4/templates/ruleset.uc` for the chain layout, `root/sbin/fw4` for reload): https://github.com/openwrt/firewall4/tree/b6e5157527d361f99ad52eaa6da273cb0f2dfd59 (pinned in https://github.com/openwrt/openwrt/blob/v25.12.5/package/network/config/firewall4/Makefile)
- `/usr/share/nftables.d/README` on the device (include positions)
- Wiki, firewall configuration: https://openwrt.org/docs/guide-user/firewall/firewall_configuration
- `docs/design/templates_database.md` in this repo
