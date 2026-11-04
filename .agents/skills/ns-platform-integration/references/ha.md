# HA reference

## Events

`keepalived.init` calls `hotplug-call keepalived` with `ACTION` set to:

| ACTION | When |
|---|---|
| `NOTIFY_MASTER` | this node became master |
| `NOTIFY_BACKUP` | this node became backup |
| `NOTIFY_FAULT` | interface/track failure; default handling is a no-op, `999-stop-fault` runs `ns-ha-disable --force` |
| `NOTIFY_STOP` | keepalived stopped |
| `NOTIFY_SYNC` | on the backup, after `ns-rsync.sh` on the master pushed files (every 600 s) |
| `startup` / `shutdown` | keepalived service start/stop |

## Helpers

From `packages/keepalived/files/lib/functions/keepalived/hotplug.sh`, sourced by every script:

| Helper | Effect |
|---|---|
| `set_service_name <init script>` | which `/etc/init.d/<name>` the flags act on |
| `set_restart_if_master` / `set_reload_if_master` | restart/reload on `NOTIFY_MASTER` |
| `set_stop_if_backup` | stop on `NOTIFY_BACKUP` |
| `set_reload_if_backup` | despite the name, restarts on `NOTIFY_BACKUP` |
| `set_reload_if_sync` / `set_restart_if_sync` | on `NOTIFY_SYNC` |
| `set_master_cb` / `set_backup_cb` / `set_fault_cb` / `set_sync_cb <fn>` | custom function per event |
| `keepalived_hotplug` | dispatch; must be the last line |

From `packages/ns-ha/files/ns.sh` (installed to `/lib/functions/keepalived/ns.sh`): `update_cron enable|disable "<space-separated command patterns>"` comments or uncomments matching crontab lines.

Logging inside hotplugs: `log_info` / `log_err` from `/lib/functions/keepalived/common.sh`.

## Ordering

`hotplug-call` runs `ls /etc/hotplug.d/keepalived/*`, so names sort as text, not numbers: `10-adjust` runs before `100-conntrackd`, and a `1000-x` would run before `500-*`. Stick to three-digit prefixes in the existing bands:

| Prefix | Used for |
|---|---|
| `00`–`10` | lock, rsync restore, alert state, network import (ns-ha internals) |
| `100` | conntrackd |
| `5xx` | core: firewall, dhcp, netmap, rpcd, system, dropbear |
| `6xx` | VPN, WAN and network services: openvpn, ipsec, mwan3, acme, qosify, snort |
| `700` | nginx |
| `800` | applications: ui, banip, adblock, netifyd, flashstart, dedalo |
| `900` | cloud and telemetry: ns-plug, telegraf, phonehome, ddns |
| `999` | stop-fault, unlock (must stay last) |

A new application goes in `800`, a new cloud/reporting service in `900`.

## Patterns in the tree

| Pattern | Examples |
|---|---|
| restart on master, stop on backup | `600-openvpn`, `800-flashstart`, `800-banip`, `800-ui` |
| same, plus cron toggling | `600-acme`, `800-netifyd`, `900-ns-plug` |
| runs on both, reloaded on sync | `500-netmap`, keepalived's `501-rpcd`, `511-firewall`, `555-dropbear` |
| restart on master, never stopped | `700-nginx` |
| custom logic only | `05-alert-state`, `10-adjust`, `100-conntrackd`, `500-dhcp-force` |

## How sync works

1. On the master, `ns-rsync.sh` (`/usr/libexec/ns-rsync.sh`, a keepalived `vrrp_script`) runs `ns-ha-export` (dumps WAN, VPN, routes, hotspot into `/etc/ha`), then rsyncs `sysupgrade -l` plus `ha_peer.sync_list`, minus `ha_peer.exclude_list`, into `/tmp/ns-ha` on the backup, with a `restore_list`.
2. On the backup, keepalived's `02-rsync` (`NOTIFY_SYNC`) copies every `restore_list` entry into place: files with `cp -a`, directories with `rsync --delete`.
3. `10-adjust` runs `ns-ha-import`, rebuilding network sections tagged `ns_tag=ha` with `auto=0`.
4. Nothing else is reloaded unless a script set `set_reload_if_sync`/`set_restart_if_sync`. Other services pick up the new config when they're restarted on `NOTIFY_MASTER`.

Never synced: `/etc/config/network`, `/etc/config/keepalived`, `/etc/dropbear/authorized_keys`, `conntrackd.conf`.

A file deleted on the master stays on the backup unless it's inside a synced directory. `900-ns-plug` removes `/etc/backup.pass` by hand for that reason.

## Alerts

`05-alert-state` and `ns-rsync.sh` write `keepalived.ha_alert.*_failed_at` to `/var/state`; `telegraf-ha-alert` turns them into metrics, `ns-plug/files/vmalert-rules/ha.yaml` alerts on them (`HaPrimaryFailed`, `HaSyncFailed`).

## Don't copy

- `ns-ha-disable:58` references an undefined `proc`.
- `ns-ha-enable:149` calls `/sbin/ifup link set` where `/sbin/ip` is meant.
- `500-dhcp-force` runs `uci commit` from a hotplug and redirects with `2&>/dev/null`.
- `100-conntrackd` has no shebang.
- `packages/ns-ha/README.md` gives `/etc/keepalived/scripts/ns-rsync.sh` and `/tmp/restore_list`; the real paths are `/usr/libexec/ns-rsync.sh` and `/tmp/ns-ha/tmp/restore_list`. It also calls the alerts `ha:sync:failed`.
