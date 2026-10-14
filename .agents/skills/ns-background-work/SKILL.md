---
name: ns-background-work
description: Pick and write the right mechanism for code that runs on its own on a NethSecurity device — a procd daemon, a procd one-shot job, a cron job, a hotplug handler or a uci-default. Use whenever a task needs something to run periodically, at boot, on a config change, on an interface event, persistently in the background, or once after install/upgrade, even when the user just says "schedule", "keep running", "every N minutes", "on startup", "when the WAN comes up" or "service". Also use it when editing any `/etc/init.d` procd script or `/etc/hotplug.d` handler, or when looking up `procd_set_param` params, procd triggers, or hotplug `ACTION`/environment variables. Covers the decision, canonical templates, package install/upgrade/remove behavior, full procd and hotplug references, and on-device checks.
metadata:
  domain: nethsecurity-packages
  type: runtime
---

## Pick the mechanism

| Need | Mechanism |
|---|---|
| Process that stays up (server, listener, forwarder) | procd daemon |
| Job that must run at boot and/or when a UCI config changes, maybe also periodically | procd one-shot, kicked by cron when periodic |
| Periodic housekeeping only (cleanup, rotation), no boot or config-change run | cron calling the script directly |
| React to an interface going up/down | hotplug handler in `/etc/hotplug.d/iface/` |
| One-time setup or migration after install, upgrade or first boot | uci-default |

When unsure between cron-direct and one-shot: if the job ever needs to run outside its schedule (boot, config change, API trigger), it's a one-shot.

Going through procd for periodic jobs gives syslog output for free and no overlapping runs: `/etc/init.d/X start` on a still-running instance with unchanged params is a no-op (procd `instance_update`).

Keepalived/HA events are not covered here.

## References

The templates below cover the common case. For anything they don't show, read the matching reference before writing code instead of guessing a `procd_*` helper or a hotplug variable:

- `references/procd-init.md` — every init action and what it really does, all `procd_set_param` params, all trigger helpers (UCI, interface, mount, data, raw), signals, extra commands, jails, debugging. Read it for multiple instances, reload via signal, interface- or mount-bound services, running as a non-root user, or custom actions.
- `references/hotplug.md` — how iface and other subsystems dispatch scripts, every `ACTION` and environment variable per subsystem, debugging. Read it for any event other than `iface` `ifup`/`ifdown`.

Both list the upstream sources (OpenWrt wiki and source files pinned to the release tag). Prefer those over memory when something isn't covered.

## Package lifecycle facts (OpenWrt v25.12, apk)

These come from `default_postinst`/`default_prerm` in `package/base-files/files/lib/functions.sh` and `include/package-pack.mk`. Re-check them if `OWRT_VERSION` in `build.conf.defaults` changes.

- **Fresh install**: package uci-defaults run (then `uci commit`), then every shipped init script is **enabled and started**, then the Makefile `postinst` body runs.
- **Upgrade**: same, with `PKG_UPGRADE=1`. Uci-defaults run again. Init scripts are **started but not enabled** — an init script that's new in this version stays disabled unless a uci-default enables it.
- **Image build**: init scripts get enabled in the rootfs; uci-defaults run at first boot (`/etc/init.d/boot`, `START=10`, before cron at 50).
- **Image upgrade (sysupgrade)**: `/etc/crontabs/` and `/etc/config/` are kept; uci-defaults run again on first boot.
- **Remove**: `default_prerm` stops and disables shipped init scripts, then the Makefile `prerm` body runs. Prerm does not run on upgrade.
- A running daemon is **not restarted** by an upgrade: `start` with unchanged params is a no-op, so the old binary keeps running. Restart it in `postinst`.

So every uci-default must be idempotent, and anything the package adds outside its own files (cron lines) must be removed in `prerm`.

## Cron rules

- Add the line from a package uci-default, remove it in `prerm`.
- Always write through `crontab -`. It drops `cron.update`, which busybox crond picks up within a minute. A plain `echo >> /etc/crontabs/root` is **ignored** until crond restarts (tested on a live device).
- Jitter with `sleep $(( RANDOM % N ))` when the job contacts a remote endpoint (controller, my, update servers, any public API). Local housekeeping runs at a fixed time, no jitter.
- Match the line by the command path, not the whole line, so a schedule change in a later release replaces the old line.

## Templates

All files carry the license header. Shell init and hotplug scripts use the procd helpers shown; don't hand-roll pid files or `start-stop-daemon`.

### procd daemon

`packages/ns-foo/files/ns-foo.init`, installed with `$(INSTALL_BIN)` to `/etc/init.d/ns-foo`:

```sh
#!/bin/sh /etc/rc.common

#
# Copyright (C) <YEAR> Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

USE_PROCD=1
START=99

start_service() {
	config_load ns-foo

	local enabled
	config_get_bool enabled daemon enabled 0
	[ "$enabled" -eq 0 ] && return 0

	local log_level
	config_get log_level daemon log_level "info"

	procd_open_instance
	procd_set_param command "/usr/sbin/ns-foo"
	procd_append_param command "-log-level"
	procd_append_param command "$log_level"
	procd_set_param stdout 1
	procd_set_param stderr 1
	procd_set_param respawn 3600 5 0
	procd_close_instance
}

service_triggers()
{
	procd_add_reload_trigger "ns-foo"
}

reload_service()
{
	stop
	start
}
```

- On/off is the UCI `enabled` option; the init script itself stays enabled. Turning it on or off is a UCI change, and the reload trigger applies it on `ns.commit`.
- `reload_service` is `stop; start` because the default reload is just `start`, which procd ignores while the command line is unchanged. A config value the daemon reads itself would never be applied. If the daemon re-reads config on a signal, use `procd_set_param reload_signal HUP` and drop `reload_service` instead.
- `START`: 99 unless something depends on it starting earlier.
- Add other configs the daemon reads to `procd_add_reload_trigger` (e.g. `"ns-foo" "ns-plug"`).
- Never put secrets on the command line (visible in `ps`). Write them to a `umask 077` file under `/var/run/ns-foo/` and pass the path, as `vmalert.initd` does.
- Makefile:

```makefile
define Package/ns-foo/postinst
#!/bin/sh
[ -z "$${IPKG_INSTROOT}" ] && /etc/init.d/ns-foo restart
exit 0
endef
```

### procd one-shot (optionally periodic)

`packages/ns-foo/files/ns-foo-update.init` → `/etc/init.d/ns-foo-update`:

```sh
#!/bin/sh /etc/rc.common

#
# Copyright (C) <YEAR> Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

USE_PROCD=1
START=50

start_service() {
	procd_open_instance
	procd_set_param command "/usr/sbin/ns-foo-update"
	procd_set_param stdout 1
	procd_set_param stderr 1
	procd_close_instance
}

reload_service()
{
	start
}

service_triggers() {
	procd_add_reload_trigger "ns-foo"
}
```

- No `respawn`: the command runs to completion and exits.
- The script (`/usr/sbin/ns-foo-update`) exits 0 quickly when there's nothing to do (feature disabled, no subscription), since it runs on every boot, upgrade and config change.
- When periodic, cron calls `/etc/init.d/ns-foo-update start`, not the script.

uci-default `packages/ns-foo/files/99-ns-foo-update-cron` → `/etc/uci-defaults/99-ns-foo-update-cron`:

```sh
#!/bin/sh

#
# Copyright (C) <YEAR> Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

(crontab -l | grep -v '/etc/init.d/ns-foo-update'; echo '8 4 * * * sleep $(( RANDOM % 3600 )); /etc/init.d/ns-foo-update start') | crontab -

# new init scripts are not enabled on package upgrade
/etc/init.d/ns-foo-update enabled || /etc/init.d/ns-foo-update enable
```

Makefile:

```makefile
define Package/ns-foo/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	crontab -l | grep -v '/etc/init.d/ns-foo-update' | crontab -
fi
exit 0
endef
```

### cron calling the script directly

Same uci-default and prerm as above, matching on the script path:

```sh
(crontab -l | grep -v '/usr/sbin/ns-foo-cleanup'; echo '4 0 * * * /usr/sbin/ns-foo-cleanup') | crontab -
```

No init script, no enable line.

### hotplug handler (interface events)

`packages/ns-foo/files/hotplug` → `/etc/hotplug.d/iface/90-ns-foo`, installed with `$(INSTALL_DATA)` (it's sourced, not executed):

```sh
#!/bin/sh

#
# Copyright (C) <YEAR> Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

[ "$ACTION" = "ifup" ] || exit 0

. /lib/functions/network.sh
network_flush_cache
network_find_wan wan_if
[ "$INTERFACE" = "$wan_if" ] || exit 0

config_load ns-foo
config_get_bool enabled config enabled 0
[ "$enabled" -eq 1 ] || exit 0

/etc/init.d/ns-foo-update start
```

- `hotplug-call` sources each script in a subshell, in name order, and netifd waits for the whole run before dispatching the next interface event. `exit` is fine, but anything slow delays mwan3, the firewall and every later handler. Hand real work to a one-shot (`/etc/init.d/X start`) instead of doing it inline.
- Filter on `ACTION` and `INTERFACE` first, then read config.
- Output goes nowhere useful; log with `logger -t ns-foo`.

### uci-default (one-time setup)

Use for UCI seeding, migrations and the cron/enable lines above. Never for recurring work. It runs on install, every package upgrade and first boot after sysupgrade, so guard every change:

```sh
if ! uci -q get ns-foo.config > /dev/null; then
	uci -q import ns-foo << EOI
config main 'config'
	option enabled '0'
EOI
fi
```

One concern per file: don't mix cron registration into a config-import uci-default.

## Don't copy

These exist in the tree but are not the current pattern:

- `packages/ns-dpi/files/99-dpi-*-cron.uci-defaults` — the "temporary fix" block deletes and re-adds the line on every run via `echo >>`, which crond ignores.
- `packages/ns-dpi/files/20_dpi` — cron line mixed into a config import (its own TODO says so).
- `packages/ns-plug/files/20_ns-plug`, `packages/ns-objects/files/20_ns_objects` — `echo >> /etc/crontabs/root`, no cleanup in `prerm`, mixed with other setup.
- `packages/ns-storage/files/ns-storage-check.init` — plain `rc.common` without procd, writes UCI and the crontab from the init script.
- `mwan3`, `keepalived`, `adblock`, `banip` — forks of upstream OpenWrt packages that follow upstream style. Keep upstream style when editing them, but don't use them as templates for `ns-*` packages.

Good references: `ns-monitoring/files/ns-flows.init` (daemon with enable flag), `victoria-metrics/files/vmalert.initd` (daemon with a secret), `ns-dpi/files/dpi-data-update.init` (one-shot).

## Verify on a device

```sh
/etc/init.d/ns-foo enabled && echo enabled
ubus call service list '{"name":"ns-foo"}'   # instance, running, command line
logread -e ns-foo                             # procd stdout/stderr
crontab -l | grep ns-foo
ls /etc/uci-defaults/                         # a leftover file means the uci-default exited non-zero
```

Install the package, upgrade it over itself, then remove it, and check after each step that the cron line and service state are what the lifecycle facts above predict.
