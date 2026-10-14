# procd init scripts reference

Covers OpenWrt v25.12 (`OWRT_VERSION` in `build.conf.defaults`). Facts come from the sources below. When the version changes or something here looks off, re-read those files at the new tag rather than trusting this page.

Sources:

- `package/base-files/files/etc/rc.common` — actions and default handlers: https://github.com/openwrt/openwrt/blob/v25.12.5/package/base-files/files/etc/rc.common
- `package/system/procd/files/procd.sh` — every `procd_*` helper and the accepted params: https://github.com/openwrt/openwrt/blob/v25.12.5/package/system/procd/files/procd.sh
- procd daemon (`service/instance.c` decides restart vs no-op): https://github.com/openwrt/procd
- Wiki, procd init scripts: https://openwrt.org/docs/guide-developer/procd-init-scripts
- Wiki, init script example: https://openwrt.org/docs/guide-developer/procd-init-script-example
- Wiki, legacy init scripts: https://openwrt.org/docs/techref/initscripts

## Contents

1. Script skeleton
2. Actions and what they really do
3. Functions you can define
4. `procd_set_param` / `procd_append_param`
5. Triggers
6. Signals, status and helpers
7. Extra commands
8. Jails
9. Debugging

## 1. Script skeleton

```sh
#!/bin/sh /etc/rc.common
USE_PROCD=1
START=99        # boot order: /etc/rc.d/S99<name>
STOP=10         # optional: shutdown order, /etc/rc.d/K10<name>
```

The process must run in the **foreground**. procd supervises it directly, so a daemon that forks itself away is seen as exited.

## 2. Actions and what they really do

| Action | Behavior with `USE_PROCD=1` |
|---|---|
| `start` | Runs `start_service` inside `procd_open_service`/`procd_close_service` and sends the whole service definition to procd ("set"), then calls `service_started` if defined. |
| `stop` | Runs `stop_service`, asks procd to kill all instances (or the one named in `$1`), then calls `service_stopped` if defined. |
| `restart` | `stop` then `start`. |
| `reload` | Calls `reload_service` if defined. **Otherwise it calls `start`.** |
| `boot` | Same as `start`. Used by `/etc/rc.d/S*` at boot. |
| `enable` / `disable` | Create or remove the `/etc/rc.d/S<START><name>` (and `K<STOP>`) symlinks. |
| `enabled` | Exit 0 if those symlinks exist. |
| `running` | `service_running`, defaulting to `procd_running <name> [instance]`. |
| `status` | `status_service` if defined, else procd's status of the instances. |
| `info` | Dumps procd's view of the service (`ubus call service list` with verbose). |
| `trace` | Starts with syscall tracing (`TRACE_SYSCALLS=1`). |

What `start` does to a service that already exists, per instance (procd `instance_update`):

- **Not running**: started.
- **Running, definition unchanged**: nothing happens. This is what makes cron'd one-shot jobs safe from overlap.
- **Running, definition changed**: restarted.

"Definition" means what procd sees: command line, env, `file` checksums, `netdev`, `data`, limits, etc. A daemon that reads its UCI config itself (not through command-line args) looks unchanged to procd. That's why the default `reload` (which is `start`) won't restart it, and NethSecurity daemons define `reload_service() { stop; start; }`.

Because `start` sends the full service definition with method "set", an instance you stop declaring in `start_service` (for example `return 0` when disabled) gets removed. That's how the `enabled` UCI flag pattern stops a daemon on reload.

## 3. Functions you can define

| Function | When it runs |
|---|---|
| `start_service` | On `start`/`boot`/default `reload`. Declares instances. |
| `stop_service` | Before procd kills the instances. Use for cleanup that needs the process still alive or for side effects (removing nft rules). |
| `service_started` | After `start_service` was sent. |
| `service_stopped` | After the kill. |
| `reload_service` | On `reload` (including UCI reload triggers). Without it, reload is `start`. |
| `service_triggers` | Declares triggers (see 5). Called during `start`. |
| `service_running` | Override for `running`. |
| `status_service` | Override for `status`. |
| `service_data` | Adds service-level data. |

## 4. `procd_set_param` / `procd_append_param`

One function argument per command-line argument. No space splitting: `procd_append_param command "-addr" "$addr"`, never `"-addr $addr"`.

`procd_set_param` replaces the value. `procd_append_param` appends to arrays/tables.

| Param | Type | Meaning |
|---|---|---|
| `command` | array | argv of the process |
| `respawn` | array | `threshold timeout retry`: if the process dies within `threshold` seconds it counts as a failure; wait `timeout` seconds before restarting; give up after `retry` failures (`0` = never give up). With no values: `system.@service[0].respawn_*` or `3600 5 5`. Omit entirely for one-shot jobs. |
| `env` | table | `procd_set_param env KEY=val KEY2=val2` |
| `limits` | table | resource limits (ulimits) passed to the process, `name=value` pairs |
| `data` | table | arbitrary key=value; changes cause a restart on next `start` |
| `file` | array | files whose content changes cause a restart on next `start` (procd checksums them) |
| `netdev` | array | network devices; an ifindex change causes a restart |
| `stdout` / `stderr` | bool | `1` relays the stream to syslog (`logread`) |
| `facility` | string | syslog facility for the above (default `daemon`) |
| `user` / `group` | string | run as that user/group instead of root |
| `pidfile` | string | procd writes the pid there (only for tools that expect it) |
| `term_timeout` | int | seconds between SIGTERM and SIGKILL on stop (default 5) |
| `reload_signal` | signal name | on `reload`, send this signal instead of restarting (e.g. `HUP`) |
| `nice` | int | -20..19 |
| `error` | string | mark the instance as failed with this message and don't start it (shown in `ubus call service list`) |
| `watch` | array | ubus namespaces to watch for JSON triggers |
| `watchdog` | array | procd instance watchdog settings; read procd's `service/instance.c` before using |
| `seccomp` | string | path to a seccomp JSON policy |
| `capabilities` | string | path to a capabilities JSON policy |
| `no_new_privs` | bool | set `PR_SET_NO_NEW_PRIVS` |
| `extroot` / `overlaydir` / `tmpoverlaysize` | string | jail rootfs options |

Multiple instances: call `procd_open_instance <name>` ... `procd_close_instance` more than once. Unnamed instances get `instance1`, `instance2`, ...

## 5. Triggers

Declared inside `service_triggers()`. All of them run with a delay of `PROCD_RELOAD_DELAY` (1000 ms by default), so a burst of events collapses into one reload.

| Helper | Fires on | Runs |
|---|---|---|
| `procd_add_reload_trigger cfg1 [cfg2...]` | `config.change` for those UCI packages | `/etc/init.d/<name> reload` |
| `procd_add_reload_interface_trigger <iface>` | netifd `interface.*` event for that logical interface | `/etc/init.d/<name> reload` |
| `procd_add_reload_data_trigger <name>` | `service.data.update` for that service | `/etc/init.d/<name> reload` |
| `procd_add_reload_mount_trigger <path...>` | `mount.add` for the fstab mount that holds the path | `reload` |
| `procd_add_restart_mount_trigger <path...>` | same | `restart` |
| `procd_add_config_trigger <event> <cfg> <cmd...>` | custom: arbitrary command on a config change | `<cmd...>` |
| `procd_add_interface_trigger <event> <iface> <cmd...>` | custom: arbitrary command on an interface event | `<cmd...>` |
| `procd_add_raw_trigger <event> <timeout_ms> <cmd...>` | any procd event, no filter | `<cmd...>` |
| `procd_add_validation <func>` | — | registers the `uci_validate_section` rules `<func>` declares for the service's config |

`config.change` is emitted by `reload_config` (`ubus call uci reload_config`), which `ns.commit` runs after committing. A bare `uci commit` from a shell does **not** emit it. After manual edits, run `reload_config` or reload the service yourself.

Mount triggers depend on `blockd` and the path being under a mount defined in `/etc/config/fstab` (`ns-storage` uses `ns_data`).

## 6. Signals, status and helpers

- `procd_send_signal <service> [instance] [SIGNAL]` sends a signal without knowing the pid (default SIGHUP). Use `'*'` for all instances.
- `procd_kill <service> [instance]` removes instances.
- `procd_running <service> [instance]` returns 0 if running.
- `procd_set_config_changed <cfg>` emits `config.change` for a package, which fires every reload trigger watching it.
- `procd_add_mdns <service> <proto> <port> [txt...]` advertises via umdns.
- `uci_load_validate <pkg> <type> <section> <callback> 'opt:type:default' ...` loads and validates a section, then calls `<callback> <section> <result>`.

## 7. Extra commands

```sh
extra_command "check" "Run a consistency check"

check() {
	...
}
```

`extra_command` adds the action to `help` and to the accepted commands. The old `EXTRA_COMMANDS`/`EXTRA_HELP` variables still work but are legacy.

## 8. Jails

`procd_add_jail <name> [log] [ubus] [udebug] [procfs] [sysfs] [ronly] [requirejail] [netns] [userns] [cgroupsns]` runs the instance in a ujail. `procd_add_jail_mount <path...>` and `procd_add_jail_mount_rw <path...>` bind paths into it. Nothing in NethSecurity uses jails today; check the procd source before relying on the flag list.

## 9. Debugging

```sh
INIT_TRACE=1 /etc/init.d/ns-foo start        # set -x the whole rc.common run
PROCD_DEBUG=1 /etc/init.d/ns-foo start       # dump the JSON sent to procd on stderr
/etc/init.d/ns-foo info                      # procd's view of the service
ubus call service list '{"name":"ns-foo","verbose":true}'
logread -e ns-foo                            # stdout/stderr when stdout/stderr=1
```

procd only tracks the main process. Children started by a shell wrapper (pipes, `&`) survive `stop` unless the wrapper traps TERM and kills them, so `exec` the real binary at the end of any wrapper script.

Init scripts are also executed on the build host with `enable`/`disable` during image creation (`IPKG_INSTROOT` set). Code at file scope (outside functions) runs there too, so keep top-level code limited to variable assignments.
