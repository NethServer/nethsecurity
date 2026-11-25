---
name: ns-background-work
description: Pick and write the right mechanism for code that runs on its own on a NethSecurity device — a procd daemon, a procd one-shot job, a cron job, a hotplug handler or a uci-default. Use whenever a task needs something to run periodically, at boot, on a config change, on an interface event, persistently in the background, or once after install/upgrade, even when the user just says "schedule", "keep running", "every N minutes", "on startup", "when the WAN comes up" or "service". Also use it when editing any `/etc/init.d` procd script or `/etc/hotplug.d` handler. Covers the decision, which in-tree files to model on, package install/upgrade/remove behavior, procd and hotplug gotchas, and on-device checks.
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

When unsure between cron-direct and one-shot: if the job ever needs to run outside its schedule (boot, config change, API trigger), it's a one-shot. Going through procd also gives syslog output and no overlapping runs.

Keepalived/HA events are not covered here, see `ns-platform-integration`.

## References

- `references/procd-init.md`: procd gotchas and the upstream sources for every `procd_*` helper and trigger.
- `references/hotplug.md`: hotplug gotchas and where the per-subsystem variables are documented.

## Package lifecycle

Read `default_postinst`/`default_prerm` in `package/base-files/files/lib/functions.sh` at the tag `OWRT_VERSION` in `build.conf.defaults` names. What follows from it:

- Uci-defaults run on install, every package upgrade and first boot after sysupgrade: make them idempotent.
- An init script added in a new version isn't enabled on upgrade: enable it from a uci-default.
- An upgrade doesn't restart a running daemon: restart it in `postinst` under the `IPKG_INSTROOT` guard.
- Anything the package adds outside its own files (cron lines) gets removed in `prerm`.

## procd daemon

Model on `packages/ns-monitoring/files/ns-flows.init`, and `packages/victoria-metrics/files/vmalert.initd` when it handles a secret.

- On/off is a UCI `enabled` option checked in `start_service`; the init script itself stays enabled.
- Define `reload_service() { stop; start; }`, or use `procd_set_param reload_signal HUP` when the daemon re-reads config on a signal (see `references/procd-init.md`).
- Add every config the daemon reads to `procd_add_reload_trigger`.
- `START`: 99 unless something depends on it starting earlier.
- Never put secrets on the command line. See `ns-state-and-persistence`.

## procd one-shot (optionally periodic)

Model on `packages/ns-dpi/files/dpi-data-update.init`.

- No `respawn`.
- The script exits 0 quickly when there's nothing to do (feature disabled, no subscription), since it runs on every boot, upgrade and config change.
- When periodic, cron calls `/etc/init.d/ns-foo-update start`, not the script.

## Cron

- Add the line from its own package uci-default, remove it in `prerm`.
- Always write through `crontab -`; crond doesn't notice direct edits to `/etc/crontabs/root`.
- Jitter with `sleep $(( RANDOM % N ))` when the job contacts a remote endpoint. Local housekeeping runs at a fixed time.
- Match the line by the command path, not the whole line, so a schedule change in a later release replaces the old line.

uci-default:

```sh
(crontab -l | grep -v '/etc/init.d/ns-foo-update'; echo '8 4 * * * sleep $(( RANDOM % 3600 )); /etc/init.d/ns-foo-update start') | crontab -
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

## hotplug handler (interface events)

- Install to `/etc/hotplug.d/iface/NN-ns-foo` with `$(INSTALL_DATA)`.
- Filter on `ACTION` and `INTERFACE` first, then read config.
- Hand real work to a one-shot (`/etc/init.d/X start`); a slow handler delays every later one.
- Log with `logger -t ns-foo`.

## uci-default

For UCI seeding, migrations and the cron/enable lines above, never recurring work. Guard every change (check with `uci -q get` before importing or setting).

## Don't copy

Older uci-defaults that `echo >>` into the crontab or mix cron into config imports, and plain `rc.common` init scripts without procd. `mwan3`, `keepalived`, `adblock`, `banip` are upstream forks: keep upstream style when editing them, but don't use them as templates for `ns-*` packages.

## Verify on a device

```sh
ubus call service list '{"name":"ns-foo"}'   # instance, running, command line
grep ns-foo /var/log/messages | tail         # procd stdout/stderr
crontab -l | grep ns-foo
```

Install the package, upgrade it over itself, then remove it, and check the cron line and service state after each step.
