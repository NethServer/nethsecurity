# UCI reference

Covers OpenWrt v25.12 (`OWRT_VERSION` in `build.conf.defaults`). Facts come from the sources below. Re-read them at the new tag when the version changes.

Sources:

- `package/base-files/files/lib/functions.sh` (`config_*` shell API, `get_bool`): https://github.com/openwrt/openwrt/blob/v25.12.5/package/base-files/files/lib/functions.sh
- `package/system/uci/files/lib/config/uci.sh` (`uci_*` shell helpers): https://github.com/openwrt/openwrt/blob/v25.12.5/package/system/uci/files/lib/config/uci.sh
- `uci` CLI usage: run `uci` with no arguments on the device
- Wiki, UCI system (file syntax, CLI): https://openwrt.org/docs/guide-user/base-system/uci
- Wiki, configuration in scripts: https://openwrt.org/docs/guide-developer/config-scripting
- Python: `EUci` (python3-euci), see the `python-nethsecurity` skill

## File syntax

```
config <type> ['<name>']
	option <key> '<value>'
	list <key> '<value1>'
	list <key> '<value2>'
```

- Named sections (`config main 'config'`) are addressed as `pkg.config.opt`. Unnamed sections get generated ids (`@type[0]` in CLI, `cfgXXXXXX` internally). Use named sections for anything code addresses directly.
- Section and option names: `[A-Za-z0-9_]`. NethSecurity-generated ids start with `ns_` (`nethsec.utils.get_id`, `get_random_id`).
- Values are strings. Booleans are `'0'`/`'1'`. The shell `get_bool` also accepts `on/off`, `true/false`, `yes/no`, `enabled/disabled`.

## CLI (`uci`)

| Command | Use |
|---|---|
| `uci show <pkg>[.<sec>[.<opt>]]` | dump in `pkg.sec.opt='val'` form |
| `uci -q get <pkg>.<sec>[.<opt>]` | read; exit 1 if missing (`-q` silences the error) |
| `uci set <pkg>.<sec>=<type>` | create a named section |
| `uci set <pkg>.<sec>.<opt>=<val>` | set an option |
| `uci add <pkg> <type>` | create an unnamed section, prints its id |
| `uci add_list` / `uci del_list` `<pkg>.<sec>.<opt>=<val>` | edit lists |
| `uci delete <pkg>.<sec>[.<opt>]` | remove |
| `uci rename <pkg>.<sec>[.<opt>]=<new>` | rename |
| `uci reorder <pkg>.<sec>=<pos>` | change section order (matters for firewall rules) |
| `uci changes [<pkg>]` / `uci revert <pkg>...` | staged changes |
| `uci commit [<pkg>]` | write staged changes to `/etc/config/<pkg>` |
| `uci import <pkg>` / `uci export <pkg>` | whole-file in/out in config syntax (`-m` merges on import) |
| `uci batch` | many commands from stdin in one process |

Options: `-c <dir>` config dir, `-t <dir>` save dir for staged changes, `-P <dir>` state dir (use `/var/state` for runtime state), `-q` quiet.

Changes are staged in `/tmp/.uci` until commit. `uci commit` alone does **not** reload services. `reload_config` (`ubus call uci reload_config`, run by `ns.commit`) emits `config.change` and fires procd reload triggers.

## Shell API (`. /lib/functions.sh`)

| Function | Notes |
|---|---|
| `config_load <pkg>` | parse the whole package into shell variables. One global namespace: loading another package **replaces** the previous one, so reload the first one if you need it again (see `vmalert.initd`). No-op at image build (`IPKG_INSTROOT` set). |
| `config_get <var> <section> <option> [default]` | `<var>` gets the value or default. The 3-arg form `config_get <section> <option> <default>` prints instead of assigning. |
| `config_get_bool <var> <section> <option> [default]` | normalizes to `0`/`1` via `get_bool` |
| `config_set <section> <option> <value>` | in-memory only, never written |
| `config_foreach <func> [type] [args...]` | calls `func <section> [args...]` for every section (of `type`) |
| `config_list_foreach <section> <option> <func> [args...]` | calls `func <value> [args...]` for each list item |
| `config_unset` | |
| `config_cb`, `option_cb`, `list_cb`, `reset_cb` | parser callbacks, define before `config_load` |
| `append <var> <value> [sep]`, `list_contains <var> <value>` | string list helpers |

## Shell helpers (`. /lib/config/uci.sh`, sourced by `functions.sh`)

| Function | Wraps |
|---|---|
| `uci_get <pkg> [sec] [opt] [default] [state_dir]` | `uci -q get` with a default |
| `uci_set <pkg> <sec> <opt> <val>` | `uci set` |
| `uci_add <pkg> <type> [name]` | `uci add` or named `uci set`; unnamed id in `$CONFIG_SECTION` |
| `uci_add_list`, `uci_remove`, `uci_remove_list`, `uci_rename`, `uci_revert` | as the CLI |
| `uci_commit [pkg]` | `uci commit` |
| `uci_set_default <pkg>` | `uci import` + commit **only if** `<pkg>` doesn't exist yet, reading the default config from stdin |
| `uci_set_state`, `uci_get_state`, `uci_revert_state`, `uci_toggle_state` | same against `/var/state` (runtime state, lost on reboot) |

## Persistence machinery

For which files survive what, see the main skill. Authoritative code:

- `package/base-files/files/sbin/sysupgrade` (`list_static_conffiles`, `list_changed_conffiles`, `build_list_of_backup_config_files`): https://github.com/openwrt/openwrt/blob/v25.12.5/package/base-files/files/sbin/sysupgrade
- `include/package-pack.mk` (`conffiles` → `conffiles_static` checksums and generated `keep.d`): https://github.com/openwrt/openwrt/blob/v25.12.5/include/package-pack.mk
- Wiki, backup and restore: https://openwrt.org/docs/guide-user/troubleshooting/backup_restore
