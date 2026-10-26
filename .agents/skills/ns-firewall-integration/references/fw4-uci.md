# fw4 UCI options reference (`/etc/config/firewall`)

Extracted from firewall4 `root/usr/share/ucode/fw4.uc` at `b6e5157527d361f99ad52eaa6da273cb0f2dfd59`, the commit OpenWrt v25.12.5 pins. The `parse_options(...)` block of each `parse_<type>` function is the authoritative list. When `OWRT_VERSION` changes, or an option here doesn't behave as described, re-read that file at the new pin:

- Source: https://github.com/openwrt/firewall4/blob/b6e5157527d361f99ad52eaa6da273cb0f2dfd59/root/usr/share/ucode/fw4.uc
- Pin: https://github.com/openwrt/openwrt/blob/v25.12.5/package/network/config/firewall4/Makefile
- Wiki (fw3-era wording, mostly still valid): https://openwrt.org/docs/guide-user/firewall/firewall_configuration

## Contents

1. Reading the tables
2. Value formats
3. `defaults`
4. `zone`
5. `forwarding`
6. `rule`
7. `redirect`
8. `nat`
9. `ipset`
10. `include`
11. NethSecurity `ns_*` options

## 1. Reading the tables

- **list**: the option accepts a UCI `list` (several values).
- **unsupported**: fw4 parses it only to warn "not supported by fw4" and ignores it. Never write these.
- **`!` prefix**: most match options accept a leading `!` to invert (`option src_ip '!10.0.0.0/8'`). Options marked "no invert" reject it.
- Unknown options produce a warning. NethSecurity patches fw4 (`patches/package/network/config/firewall4/10-hide_warning_ns_options.patch`) so options starting with `ns_` are silently accepted. That's what makes the `ns_*` metadata below safe to store in fw4 sections.
- `fw4 check` / `fw4 print` show the warnings for the current config.

## 2. Value formats

| Type | Accepted values |
|---|---|
| bool | `0`/`1` (also `yes`/`no`, `on`/`off`, `true`/`false`) |
| policy | `accept`, `reject`, `drop` (case-insensitive; `ACCEPT` is common in configs) |
| target (rule) | `accept`, `reject`, `drop`, `notrack`, `helper`, `mark`, `dscp` |
| target (redirect) | `dnat` (default), `snat` |
| target (nat) | `masquerade` (default), `snat`, `accept` |
| family | `any`/`all`/`*` (both), `ipv4`/`inet`/anything with `4`, `ipv6`/anything with `6` |
| zone_ref | a zone `name`, or `*` for any zone |
| proto | `tcp`, `udp`, `tcpudp` (rule/redirect default, expands to tcp + udp), `icmp`, `icmpv6`/`ipv6-icmp`, `all`/`any`/`*`, other protocol names or numbers |
| network | IP, CIDR, or `addr/mask` |
| port | `80`, `8000-8080` |
| limit | `N[/second\|minute\|hour\|day]`, e.g. `10/minute` (default unit second) |
| mark | `0xVALUE[/0xMASK]`, up to 32 bit |
| dscp | class name (`CS0`-`CS7`, `AF11`-`AF43`, `EF`, `BE`, `LE`) or 0-63 |
| reject_code | `tcp-reset`, `port-unreachable`, `admin-prohibited`, `host-unreachable`, `no-route` |
| direction | `in`/`ingress`, `out`/`egress` |
| setmatch (`ipset`) | `<setname> [src\|dst ...]`, e.g. `blocklist src` |
| ipsettype (`match`) | `[src_\|dst_]ip`, `port`, `mac`, `net`, `set` |
| weekdays | `Monday` ... `Sunday`, list or space-separated |
| date | `YYYY[-MM[-DD[Thh:mm:ss]]]`, years 1970-2038 |
| time | `hh[:mm[:ss]]` |

## 3. `defaults`

| Option | Type | Default |
|---|---|---|
| `input`, `output`, `forward` | policy | `drop` |
| `drop_invalid` | bool | |
| `tcp_reject_code` | reject_code | `tcp-reset` |
| `any_reject_code` | reject_code | `port-unreachable` |
| `syn_flood` / `synflood_protect` | bool | |
| `synflood_rate` | limit | `25/second` |
| `synflood_burst` | int | `50` |
| `tcp_syncookies` | bool | `1` |
| `tcp_ecn` | int | |
| `tcp_window_scaling` | bool | `1` |
| `accept_redirects`, `accept_source_route` | bool | |
| `auto_helper` | bool | `1` |
| `flow_offloading`, `flow_offloading_hw` | bool | `0` |
| `auto_includes` | bool | `1` — set `0` and `/usr/share/nftables.d` stops being included |
| `custom_chains`, `disable_ipv6` | — | unsupported |

## 4. `zone`

| Option | Type | Default / notes |
|---|---|---|
| `enabled` | bool | `1` |
| `name` | identifier | **required**; the name referenced by rules (`src`, `dest`) |
| `family` | family | both |
| `network` | list | logical interfaces from `/etc/config/network` |
| `device` | list | raw Linux devices (`tun+` wildcard allowed) |
| `subnet` | list, network | match by subnet instead of device |
| `input`, `output`, `forward` | policy | inherit from `defaults` |
| `masq` | bool | masquerade IPv4 leaving this zone |
| `masq6` | bool | masquerade IPv6 |
| `masq_src`, `masq_dest` | list, network | restrict masquerading |
| `masq_allow_invalid` | bool | |
| `mtu_fix` | bool | MSS clamping |
| `log` | int | `1` logs traffic dropped/rejected by the zone policy |
| `log_limit` | limit | |
| `auto_helper` | bool | `1` |
| `helper` | list | conntrack helpers |
| `counter` | bool | `1` |
| `extra`, `extra_src`, `extra_dest`, `custom_chains` | — | unsupported |

## 5. `forwarding`

| Option | Type | Default / notes |
|---|---|---|
| `enabled` | bool | `1` |
| `name` | string | |
| `family` | family | |
| `src`, `dest` | zone_ref | **required**; allows new connections from `src` zone to `dest` zone |

## 6. `rule`

| Option | Type | Default / notes |
|---|---|---|
| `enabled` | bool | `1` |
| `name` | string | section id |
| `family` | family | |
| `src` | zone_ref | no `src` = output rule (traffic from the device) |
| `dest` | zone_ref | no `dest` = input rule (traffic to the device); both = forward rule |
| `device` | string, no invert | with `direction` |
| `direction` | direction | |
| `ipset` | setmatch | match against a named set |
| `helper` | cthelper | match connections using a helper |
| `set_helper` | cthelper, no invert | with `target helper` |
| `proto` | list | `tcpudp` |
| `src_ip`, `dest_ip` | list, network | |
| `src_mac` | list | |
| `src_port`, `dest_port` | list, port | |
| `icmp_type` | list | names or numbers |
| `limit` | limit | |
| `limit_burst` | int | |
| `utc_time` | bool | interpret time options as UTC (per wiki) |
| `start_date`, `stop_date` | date | |
| `start_time`, `stop_time` | time | |
| `weekdays` | weekdays | |
| `mark` | mark | match |
| `set_mark`, `set_xmark` | mark, no invert | with `target mark` |
| `dscp` | dscp | match |
| `set_dscp` | dscp, no invert | with `target dscp` |
| `counter` | bool | `1` |
| `log` | string | `1` to log matches |
| `log_limit` | limit | |
| `target` | target | `accept`, `reject`, `drop`, `notrack`, `helper`, `mark`, `dscp` |
| `monthdays`, `extra` | — | unsupported |

## 7. `redirect` (port forward / DNAT)

| Option | Type | Default / notes |
|---|---|---|
| `enabled` | bool | `1` |
| `name` | string | section id |
| `family` | family | |
| `src` | zone_ref | zone the traffic comes from (usually `wan`) |
| `dest` | zone_ref | zone of the internal host |
| `ipset` | setmatch | |
| `helper` | cthelper, no invert | |
| `proto` | list | `tcpudp` |
| `src_ip`, `src_mac`, `src_port` | | match the original source |
| `src_dip` | network | original destination IP (the public address) |
| `src_dport` | port | original destination port (the public port) |
| `dest_ip` | network | internal host |
| `dest_port` | port | internal port |
| `limit`, `limit_burst`, time/date options, `mark` | | as in `rule` |
| `reflection` | bool | `1` — NAT loopback (hairpin) |
| `reflection_src` | `internal` / `external` | `internal` |
| `reflection_zone` | list, zone_ref | zones that get reflection rules |
| `counter` | bool | `1` |
| `log`, `log_limit` | | |
| `target` | `dnat` / `snat` | `dnat` |
| `monthdays`, `extra` | — | unsupported |

## 8. `nat` (SNAT / masquerade rules)

| Option | Type | Default / notes |
|---|---|---|
| `enabled` | bool | `1` |
| `name` | string | section id |
| `family` | family | |
| `src` | zone_ref | outgoing zone |
| `device` | string | outgoing device |
| `proto` | list | `all` |
| `src_ip`, `src_port`, `dest_ip`, `dest_port` | | match |
| `snat_ip`, `snat_port` | no invert | with `target snat` |
| `limit`, `limit_burst`, `connlimit_ports`, time/date options, `mark` | | |
| `counter` | bool | `1` |
| `log` | string | |
| `target` | `masquerade` / `snat` / `accept` | `masquerade`; `accept` excludes the traffic from NAT |
| `ipset`, `monthdays`, `extra` | — | unsupported |

## 9. `ipset` (named nftables set)

| Option | Type | Default / notes |
|---|---|---|
| `enabled` | bool | `1` |
| `name` | identifier | **required**; reference it from `rule`/`redirect` `ipset` or from nft snippets as `@name` |
| `family` | family | `4` |
| `match` | list, ipsettype | e.g. `src_net`, `dest_port` |
| `entry` | list | initial elements |
| `loadfile` | string | file with one element per line |
| `maxelem` | int | |
| `timeout` | int | `-1` (no timeout); seconds otherwise |
| `counters` | bool | |
| `comment` | string | |
| `reload_set` | bool | |
| `storage`, `iprange`, `portrange`, `netmask`, `hashsize`, `external` | — | unsupported |

`fw4 reload-sets` reloads set contents without rebuilding the ruleset.

## 10. `include`

| Option | Type | Default / notes |
|---|---|---|
| `enabled` | bool | `1` |
| `path` | string | **required**; must exist, or the include is skipped with a warning |
| `type` | `script` / `nftables` | `script` |
| `fw4_compatible` | bool | required `1` for `script` includes, else ignored |
| `position` | | `nftables` only: `ruleset-prepend`, `ruleset-append`, `table-prepend` (default `table-append`), `table-append`, `chain-prepend`, `chain-append` |
| `chain` | identifier | required for `chain-*` positions |
| `family`, `reload` | — | unsupported |

Files in `/usr/share/nftables.d/<position>/` are turned into `nftables` includes automatically (see the main skill). Prefer them over `include` sections.

## 11. NethSecurity `ns_*` options

Stored in fw4 sections, ignored by fw4 (see the patch in section 1), used by `nethsec.firewall` and the UI:

| Option | On | Meaning |
|---|---|---|
| `ns_tag` | rule, zone, forwarding, redirect | list; `automated` = created by the system, exposed as `system_rule` |
| `ns_link` | any | `<config>/<section>` of the owning object; used by `delete_linked_sections` |
| `ns_service` | rule | service name from the service suggestions, or `custom` |
| `ns_src`, `ns_dst` | rule, redirect | object reference `<database>/<id>` (users/objects DB); `update_firewall_rules` expands it into `src_ip`/`dest_ip` or `ipset` |
| `ns_description` | zone (templates) | human description |

There's also a section `firewall.ns_defaults` (type `defaults`) holding NethSecurity-wide settings such as `rule_log_limit` (`get_default_logging_options` / `apply_default_logging_options`).
