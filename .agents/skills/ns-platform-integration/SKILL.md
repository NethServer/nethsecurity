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
| Own alerts | one of its metrics needs an alert | `/etc/vmalert/rules/ns-foo.yaml` | `+victoria-metrics` (ships vmalert) |
| Logging | always (writing to syslog needs nothing) | an rsyslog include only if the user asks for routing | `+rsyslog` only with an include |
| Inventory | my or phonehome stats must know the feature is in use | `fact_<name>` in `python3-nethsec` (central) | none |
| Register/unregister hook | it must react to the unit joining or leaving my | `/usr/share/ns-plug/hooks/{register,unregister}/` | `+ns-plug` |
| Controller push | the controller needs data it can't get by calling the API | `dump-*` in `ns.controller` (central) | none |

Persistence, firewall, scheduling and code placement have their own skills (`ns-state-and-persistence`, `ns-firewall-integration`, `ns-background-work`, `ns-code-placement`). This one covers what's left.

**Ownership rule**: when a package does integrate, it ships its own files and declares the dependency from the table. Don't add them to `packages/ns-ha`, `packages/telegraf` or `packages/ns-plug` like the existing ones are: those are older layouts. The only central edits are `MONITORED_SERVICES`, inventory facts and controller dumps, which have no drop-in mechanism.

## HA

On a cluster both nodes boot every service normally. keepalived (`START=70`) then fires `/etc/hotplug.d/keepalived/*` on each state change, and the scripts there stop or restart services. Nothing disables init scripts.

Skip this section when the package runs nothing persistent: a one-shot that writes config gets its config synced like everything else and needs no hotplug. Anything that talks to the outside world, sends things, or owns a VIP-bound listener runs on the master only. Ship this from the package, with `+keepalived` in `DEPENDS`:

```makefile
define Package/ns-foo/install
	...
	$(INSTALL_DIR) $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/ns-foo.keepalived $(1)/etc/hotplug.d/keepalived/800-ns-foo
endef
```

```sh
#!/bin/sh

. /lib/functions/keepalived/hotplug.sh

set_service_name ns-foo

set_restart_if_master
set_stop_if_backup

keepalived_hotplug
```

- `INSTALL_DATA`, not `INSTALL_BIN`: `hotplug-call` sources the files.
- Keep `set_service_name` and `set_stop_if_backup` as literal lines. `ns-ha-disable --force` (run on FAULT/STOP) greps hotplug files for them to know what to stop; services stopped only inside callbacks are missed.
- Cron jobs: the backup receives the master's crontab on every sync, so disable them on `NOTIFY_BACKUP` **and** `NOTIFY_SYNC`, enable on `NOTIFY_MASTER`, with `update_cron` from `/lib/functions/keepalived/ns.sh`. `packages/ns-ha/files/900-ns-plug` is the example.
- Config reaches the backup through `conffiles` (see `ns-state-and-persistence`). Don't add paths to `ha_peer.sync_list` in `ns.ha`: it's written only when HA is first configured, so existing clusters never get it.
- Synced config is copied on the backup but not applied. Add `set_reload_if_sync` only when the service also runs on the backup and must follow config changes.
- Add the service to the list in `packages/ns-ha/README.md`.

`references/ha.md` has the events, every helper, the file-name ordering bands, how sync is applied, and what not to copy.

## Metrics and alerts

Pipeline: telegraf (inputs from `/etc/telegraf.conf.d/*.conf`) → local VictoriaMetrics `127.0.0.1:8428` → vmalert (`/etc/vmalert/rules/*.yaml`) → my.nethesis.it alertmanager when the unit is subscribed (`ns-plug.config.notifier_url`), otherwise discarded. The controller doesn't get alerts; it scrapes metrics over the VPN.

**Service down**: `packages/telegraf/files/telegraf-services` exports `procd_service_running` for the names in `MONITORED_SERVICES`, and `ns-plug/files/vmalert-rules/services.yaml` alerts on them. Add a long-running daemon's procd service name there. Skip one-shots.

**Own metric**: a collector that prints a JSON array, plus a drop-in, with `+telegraf` in `DEPENDS`. Only the plugins in `GO_PKG_TAGS` of `packages/telegraf/Makefile` exist; `inputs.exec` with `json_v2` covers almost everything. An unknown plugin breaks the whole telegraf config.

```toml
# /etc/telegraf.conf.d/ns-foo.conf
[[inputs.exec]]
  name_override = "ns_foo"
  commands = [["/usr/libexec/telegraf-ns-foo"]]
  interval = "60s"
  timeout = "5s"
  data_format = "json_v2"

  [[inputs.exec.json_v2]]
    [[inputs.exec.json_v2.object]]
      path = "@this"
      tags = ["instance"]

  [inputs.exec.tags]
    influxdb_db = "os-metrics"
```

The collector prints e.g. `[{"instance": "main", "queue_full": 0}]`, which becomes `ns_foo_queue_full{instance="main"}`. Keep it fast and side-effect free; it runs every interval. telegraf runs with `--watch-config`, so installing or removing the drop-in reloads it.

**Alert rule**, with `+victoria-metrics` in `DEPENDS`, same format as `ns-plug/files/vmalert-rules/storage.yaml`:

```yaml
# /etc/vmalert/rules/ns-foo.yaml
groups:
  - name: "ns-foo"
    interval: "5m"
    rules:
      - alert: NsFooQueueFull
        expr: 'ns_foo_queue_full == 1'
        for: "5m"
        labels:
          severity: "warning"
          service: "ns-foo"
        annotations:
          summary_en: "..."
          summary_it: "..."
          description_en: "..."
          description_it: "..."
```

- `severity` is `info`, `warning` or `critical`; use `service:`, not `alertgroup:` (`services.yaml` is the odd one out). English and Italian annotations are both required.
- vmalert doesn't watch the directory. Run `/etc/init.d/vmalert reload` in the package `postinst` and `postrm` (guarded by `IPKG_INSTROOT`, as `ns-plug`'s postinst does).
- The UI reads firing alerts through `ns.telegraf list-alerts` and the `/api/alerts` proxy; a new rule shows up there with no UI change.

## Logging

logd isn't built: there is no `logread`. rsyslog writes everything to `/var/log/messages` (size-capped, copied to `/mnt/data/log` when storage is present), and from there it's forwarded to VictoriaLogs when installed, to the controller's promtail when the unit is connected, and to any remote syslog the user configured. Writing to syslog is the whole integration.

| Code | How |
|---|---|
| procd daemon | print to stdout/stderr, `procd_set_param stdout 1` and `stderr 1`; the tag is the program name |
| Python daemon | `logging` with a `StreamHandler()` to stderr, under procd as above |
| shell script / cron job | `logger -t ns-foo "..."` (always `-t`) |
| Python script outside procd | `syslog.openlog("ns-foo")` then `syslog.syslog(...)` |

- No private log files (`/var/log/ns-foo.log`): they skip the size cap, the storage copy and every forwarder.
- Don't touch the rsyslog line or timestamp format: `ns.log`, `ns.report` and `ns.controller` parse `/var/log/messages` with regexes.
- No per-package rsyslog rules unless the user asks for routing. When needed, depend on `+rsyslog`, ship `/etc/rsyslog.d/ns-foo.conf` and add it to `rsyslog.syslog.includes` from a uci-default, like `victoria-logs/files/35_victoria-logs`.
- Never log secrets (see `ns-state-and-persistence`).

## Controller and my

The unit can be connected to a controller (`ns-plug.config.server`, `unit_id`, `token` set), subscribed to my (`ns-plug.config.system_id`, `secret` set, `type` is `enterprise` or `community`), both, or neither. Anything remote must exit 0 silently when its keys are missing.

- **APIs**: a new `ns.*` RPCD API is reachable from the controller as-is (VPN → nginx → ns-api-server → rpcd, as the `controller` rpcd user). Nothing to add.
- **Inventory**: to make the feature visible in my and in phonehome stats, add `fact_<name>(uci)` to `packages/python3-nethsec/src/nethsec/inventory/__init__.py` returning a small dict (`fact_hotspot` is the pattern), and a test in `tests/test_inventory.py`. Every `fact_*` is picked up automatically. Wrap identifiers (IPs, hostnames) in `anonymize()`. Never change an existing fact's shape.
- **Register/unregister reactions**: install an executable into `/usr/share/ns-plug/hooks/register/` or `hooks/unregister/` (name starts with a two-digit order, e.g. `60ns-foo`), with `+ns-plug` in `DEPENDS`. Exit codes are ignored.
- **Pushing data to the controller**: add a `dump-*` method to `packages/ns-api/files/ns.controller` and to the list in `ns-plug/files/ns-push-reports`. The controller needs a matching `/ingest/<name>` endpoint in `nethsecurity-controller`, so this is a cross-repo change: ask before starting it.
- Remote jobs on a cluster run on the master only (HA section, cron).

## Don't copy

- Hotplug scripts installed by hand in `packages/ns-ha/Makefile`, telegraf drop-ins inside `packages/telegraf` and rules inside `packages/ns-plug/files/vmalert-rules`: the old central layout.
- `packages/ns-ha/files/900-telegraf`: calls `set_service_name` with no flags, so the service part does nothing.
- `telegraf/files/telegraf.conf.d/banip.conf`: parses `/var/log/messages` with grok. Use a collector instead.
- `logger` without `-t` (`ns-ha/files/conntrackd.sh`), `SysLogHandler('/dev/log')` with a custom formatter (`ns-ha-enable`), `echo >> /etc/rsyslog.conf` (`ns-storage/files/30_ns-storage`).
- `ns-plug` shell scripts pass secrets on the curl command line and build JSON by string concatenation.

## Verify on a device

```sh
# HA (on both nodes; force a switch with /etc/init.d/keepalived restart on the master)
ls /etc/hotplug.d/keepalived/
ubus call service list '{"name":"ns-foo"}'     # running on master, absent on backup
crontab -l | grep ns-foo                       # commented out on backup

# Metrics and alerts
/usr/libexec/telegraf-ns-foo                   # valid JSON array
curl -s 'http://127.0.0.1:8428/api/v1/query?query=ns_foo_queue_full'
curl -s 'http://127.0.0.1:8428/api/v1/query?query=procd_service_running{service="ns-foo"}'
api-cli ns.telegraf list-alerts

# Logging
grep ns-foo /var/log/messages | tail

# Inventory
/usr/sbin/inventory | jq .features.foo
```

## Sources

- `packages/ns-ha/README.md`, `packages/telegraf/README.md`, `packages/victoria-metrics/README.md`, `packages/victoria-logs/README.md`, `packages/ns-plug/README.md`, `packages/ns-api-server/README.md` in this repo
- keepalived hotplug helpers: `packages/keepalived/files/lib/functions/keepalived/hotplug.sh`
- `hotplug-call`: https://github.com/openwrt/openwrt/blob/v25.12.5/package/base-files/files/sbin/hotplug-call
