---
name: ns-firewall-integration
description: Make a NethSecurity package or API change the firewall the right way — fw4 UCI rules, zones and forwardings through `nethsec.firewall`, or raw nftables snippets auto-included by fw4. Use whenever a task opens a port, allows or blocks traffic, adds a zone, forward, NAT/redirect or netmap rule, marks/labels/logs packets (ct label, dscp, nflog), touches `/etc/config/firewall`, `/usr/share/nftables.d`, `/etc/nftables.d`, `fw4`, `nft`, `ns_tag`, `ns_link`, `system_rule`, or the templates database, even when the user only says "the service needs to be reachable", "block this", "add a rule" or "firewall".
metadata:
  domain: nethsecurity-packages
  type: runtime
---

## Ground rules

fw4 rebuilds `table inet fw4` from `/etc/config/firewall` and the include files in one transaction on every reload (read `root/sbin/fw4` and `fw4.uc`, see Sources). So:

- Never add rules to `inet fw4` at runtime with `nft add`: the next reload wipes them. Every rule comes from UCI or an include file.
- Validate anything you render. A broken ruleset leaves the box with no firewall at boot.
- APIs only stage changes; `ns.commit` reloads the firewall.

## Pick the mechanism

| Need | Mechanism |
|---|---|
| Open a port on the firewall, allow/deny between zones, port forward, SNAT/masquerade, zone, forwarding | fw4 UCI via `nethsec.firewall`, tagged `automated` and linked to its owner |
| Something fw4 UCI can't express: ct labels, dscp/marks, nflog, custom chains or hooks | nft snippet in `/usr/share/nftables.d/` |
| Snippet content depends on UCI | generate the snippet from UCI, `fw4 reload` only when the content changed |

Put non-UCI rules in a snippet inside `inet fw4`, not a separate table: it's atomic with the rest, can reference fw4 sets and chains, and survives reloads. `banIP` and `netifyd` have their own tables because they come from upstream; don't take them as a model.

## fw4 UCI from Python

Use `nethsec.firewall` from APIs and scripts, and read the function before relying on it. Don't guess fw4 option names: check `parse_options` in `fw4.uc`.

When a package or API creates rules on its own:

- Tag them `automated` in `ns_tag`, so the UI shows them as system rules.
- Set `ns_link` to the owning `<config>/<section>`, and call `delete_linked_sections(uci, link)` when the owner is deleted.
- Use `ns_`-prefixed ids from `nethsec.utils`.
- Save, don't commit; let `ns.commit` apply.

## nft snippets in `/usr/share/nftables.d`

The subdirectory picks the position (`ruleset-*`, `table-*`, `chain-pre/<chain>`, `chain-post/<chain>`); read `/usr/share/nftables.d/README` on the device and the include handling in `fw4.uc`.

- A snippet for a chain that doesn't exist (zone not configured) is skipped silently: check it's loaded.
- Name files `NN-ns-foo.nft`.
- `/etc/nftables.d/` is the user's directory. Packages never write there.

**Static snippet**: model on `packages/ns-don`. Reload the firewall in `postinst` and `prerm` under the `IPKG_INSTROOT` guard.

**Generated snippet**: model on `packages/ns-dpi/files/dpi-nft`, run from a one-shot (see `ns-background-work`).

- Reload fw4 only if the content changed.
- Validate with `fw4 -q check` after writing and restore the previous file on failure.
- When the feature is disabled, remove the file (and reload) instead of writing an empty one.
- Delete the file and reload the firewall in `prerm`.
- Validate any value from UCI or user input before it reaches nft syntax.

## Don't copy

Script includes (`type script`): use an nft snippet. Packages managing their own nft table: use a generated snippet in `inet fw4`. Generated snippets without validation or prerm cleanup: copy the generation, not the gaps.

## Verify on a device

```sh
fw4 check                          # renders the ruleset and runs nft -c
fw4 print | less                   # rendered ruleset, includes expanded
nft list chain inet fw4 input      # what's actually loaded
```

Check behavior after `fw4 reload` and after a reboot.

## Sources

- firewall4 at the commit pinned in OpenWrt's `package/network/config/firewall4/Makefile` (read at the tag `OWRT_VERSION` in `build.conf.defaults` names): `root/sbin/fw4`, `root/usr/share/ucode/fw4.uc` (`parse_options` in each `parse_<type>`, includes), `root/usr/share/firewall4/templates/ruleset.uc` (chain layout). https://github.com/openwrt/firewall4
- `patches/package/network/config/firewall4/10-hide_warning_ns_options.patch` for the `ns_*` options in fw4 sections
- `enrich_rule` and `setup_rule` in `nethsec.firewall` for the `ns_*` options (`ns_tag`, `ns_link`, `ns_service`, `ns_src`, `ns_dst`)
- Wiki, firewall configuration: https://openwrt.org/docs/guide-user/firewall/firewall_configuration
- nftables syntax: https://wiki.nftables.org/wiki-nftables/index.php/Quick_reference-nftables_in_10_minutes
- `docs/design/templates_database.md` in this repo
