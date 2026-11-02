---
name: ns-platform-integration
description: Plug a NethSecurity package or device service into the platform services around it — High Availability (keepalived master/backup, ns-ha sync), metrics and alerts (telegraf, VictoriaMetrics, vmalert), logging (rsyslog, /var/log/messages, VictoriaLogs, controller log forwarding) and remote management (controller, my.nethesis.it, ns-plug, inventory facts). Use whenever a task adds or changes a daemon, cron job or feature on the device, or touches `/etc/hotplug.d/keepalived`, `ns-ha`, `ns-rsync.sh`, `telegraf.conf.d`, `/etc/vmalert/rules`, `MONITORED_SERVICES`, rsyslog, `logger`, `ns-plug`, `send-inventory`, `fact_*`, `ns.controller`, `ns-push-reports`, even when the user only asks "should it run on the backup node", "add an alert", "where do the logs go", "does the controller see it" or "make it a well-behaved service".
metadata:
  domain: nethsecurity-packages
  type: runtime
---

## Integration points

Most packages need only some of these. Go through the rows, integrate where the condition holds and skip the rest without adding anything. A tool that just runs, writes config and exits has nothing to do in HA or telegraf.

| Point | Integrate only when | Ships | `DEPENDS` |
|---|---|---|---|
| HA | it's a running service or cron job that must not run on both nodes (talks to the outside, sends notifications, owns a listener) | `/etc/hotplug.d/keepalived/NNN-ns-foo` | `+keepalived` (`+ns-ha` too if it uses `update_cron`) |
| Service-down alert | it's a long-running procd daemon | a line in `MONITORED_SERVICES` (central) | none |
| Own metrics | it has a health signal worth graphing or alerting on | telegraf drop-in + collector | `+telegraf` |
| Own alerts | one of its metrics needs an alert | `/etc/vmalert/rules/ns-foo.yaml` | `+victoria-metrics` |
| Logging | always (writing to syslog needs nothing) | an rsyslog include only if the user asks for routing | `+rsyslog` only with an include |
| Inventory | my or phonehome stats must know the feature is in use | `fact_<name>` in `python3-nethsec` (central) | none |
| Register/unregister hook | it must react to the unit joining or leaving my | `/usr/share/ns-plug/hooks/{register,unregister}/` | `+ns-plug` |
| Controller push | the controller needs data it can't get by calling the API | `dump-*` in `ns.controller` (central) | none |

Persistence, firewall, scheduling and code placement have their own skills (`ns-state-and-persistence`, `ns-firewall-integration`, `ns-background-work`, `ns-code-placement`). This one covers what's left.

**Ownership rule**: when a package does integrate, it ships its own files and declares the dependency from the table. Don't add them to `packages/ns-ha`, `packages/telegraf` or `packages/ns-plug` like the existing ones are. The only central edits are `MONITORED_SERVICES`, inventory facts and controller dumps.

## HA

Both nodes boot every service; keepalived hotplugs then stop or restart them on each state change. Anything that talks to the outside world, sends things, or owns a VIP-bound listener runs on the master only. A one-shot that writes config needs nothing.

Model the hotplug on `packages/ns-ha/files/800-banip`, shipped from the package with `+keepalived` in `DEPENDS`.

- Install it with `INSTALL_DATA`.
- Keep `set_service_name` and `set_stop_if_backup` as literal lines; `stop_services()` in `packages/ns-ha/files/ns-ha-disable` greps for them.
- Cron jobs: disable them on `NOTIFY_BACKUP` and `NOTIFY_SYNC`, enable on `NOTIFY_MASTER`, with `update_cron`. `packages/ns-ha/files/900-ns-plug` is the example.
- Config reaches the backup through `conffiles` (see `ns-state-and-persistence`), not through `ha_peer.sync_list`.
- Add `set_reload_if_sync` only when the service also runs on the backup and must follow config changes.
- Add the service to the list in `packages/ns-ha/README.md`.

`references/ha.md` points at the helpers, sync and naming.

## Metrics and alerts

telegraf reads `/etc/telegraf.conf.d/*.conf` into the local VictoriaMetrics; vmalert reads `/etc/vmalert/rules/*.yaml`. Read `packages/telegraf/README.md` and `packages/victoria-metrics/README.md` for the full pipeline.

**Service down**: add a long-running daemon's procd service name to `MONITORED_SERVICES` in `packages/telegraf/files/telegraf-services`. Skip one-shots.

**Own metric**: a collector that prints JSON plus an `inputs.exec` drop-in, modeled on the files in `packages/telegraf/files/telegraf.conf.d/`, with `+telegraf` in `DEPENDS`. Use only plugins listed in `GO_PKG_TAGS` of `packages/telegraf/Makefile`: an unknown one breaks the whole telegraf config. Keep the collector fast and side-effect free.

**Alert rule**: same format as `packages/ns-plug/files/vmalert-rules/storage.yaml`, with `+victoria-metrics` in `DEPENDS`.

- `severity` is `info`, `warning` or `critical`; use a `service:` label. English and Italian annotations are both required.
- Reload vmalert in the package `postinst` and `postrm`, under the `IPKG_INSTROOT` guard.

## Logging

Log to syslog; everything ends up in `/var/log/messages` and its forwarders. There is no `logread`.

| Code | How |
|---|---|
| procd daemon | print to stdout/stderr, `procd_set_param stdout 1` and `stderr 1` |
| Python daemon | `logging` with a `StreamHandler()` to stderr, under procd as above |
| shell script / cron job | `logger -t ns-foo "..."` (always `-t`) |
| Python script outside procd | `syslog.openlog("ns-foo")` then `syslog.syslog(...)` |

- No private log files.
- Don't touch the rsyslog line or timestamp format: several APIs parse `/var/log/messages`.
- Per-package rsyslog rules only when the user asks for routing, like `victoria-logs/files/35_victoria-logs`.
- Never log secrets.

## Controller and my

Read `packages/ns-plug/README.md` for the config keys that say whether the unit is connected to a controller, subscribed to my, both, or neither. Anything remote must exit 0 silently when its keys are missing.

- **APIs**: a new `ns.*` API is reachable from the controller as-is. Nothing to add.
- **Inventory**: add a `fact_<name>(uci)` to `packages/python3-nethsec/src/nethsec/inventory/__init__.py` (`fact_hotspot` is the pattern) with a test in `tests/test_inventory.py`. Wrap identifiers in `anonymize()`. Never change an existing fact's shape.
- **Register/unregister reactions**: an executable in `/usr/share/ns-plug/hooks/register/` or `hooks/unregister/`, with a two-digit prefix and `+ns-plug` in `DEPENDS`.
- **Pushing data to the controller**: a `dump-*` method in `packages/ns-api/files/ns.controller` and in `ns-plug/files/ns-push-reports`, plus a matching endpoint in `nethsecurity-controller`. Cross-repo: ask before starting it.
- Remote jobs on a cluster run on the master only.

## Don't copy

The integration files living in `ns-ha`, `telegraf` and `ns-plug` are the old central layout. Don't parse `/var/log/messages` for metrics, log without a tag, or pass secrets on the command line, even where existing scripts do.

## Verify on a device

```sh
ubus call service list '{"name":"ns-foo"}'     # HA: running on master, absent on backup
crontab -l | grep ns-foo                       # HA: commented out on backup
/usr/libexec/telegraf-ns-foo                   # valid JSON
api-cli ns.telegraf list-alerts
grep ns-foo /var/log/messages | tail
```

## Sources

- `packages/ns-ha/README.md`, `packages/telegraf/README.md`, `packages/victoria-metrics/README.md`, `packages/victoria-logs/README.md`, `packages/ns-plug/README.md`, `packages/ns-api-server/README.md` in this repo
- `packages/keepalived/files/lib/functions/keepalived/hotplug.sh`
- `config/rsyslog.conf` and `packages/rsyslog` for logging
