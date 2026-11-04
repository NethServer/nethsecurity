---
name: ns-state-and-persistence
description: Decide where a NethSecurity package keeps configuration, secrets, runtime state, caches and historical data, and make it survive (or not) reboot, package upgrade, sysupgrade, backup/restore and HA sync. Use whenever a task adds a config file or UCI option, writes any file on the device, stores a token or password, keeps a database/history/log, touches `/etc/config`, `conffiles`, `/lib/upgrade/keep.d`, `/etc/sysupgrade.conf`, `/var`, `/tmp`, `/mnt/data`, `ns-storage`, `sync-data`, or when the user asks "where should this live", "will it survive an upgrade", "is it in the backup", even if persistence isn't mentioned explicitly.
metadata:
  domain: nethsecurity-packages
  type: runtime
---

## The filesystem you're writing to

Checked on a NethSecurity 8.8 x86 device (OpenWrt 25.12, apk):

| Path | Backed by | Reboot | Package upgrade | sysupgrade / backup / HA sync |
|---|---|---|---|---|
| `/etc/config/*` (UCI) | root overlay | kept | kept (see conffiles) | **kept**: `base-files-essential` keep.d lists `/etc/config/` |
| other files under `/etc`, `/usr`, `/opt` | root overlay | kept | overwritten if shipped by the package, unless a conffile | kept only if declared in a package's `conffiles` (or listed in keep.d) |
| `/var/*` (symlink to `/tmp`) | tmpfs (RAM) | **lost** | kept | not kept |
| `/mnt/data/*` | optional ext4 disk (`ns-storage`, `fstab.ns_data`) | kept | kept | not kept (not part of the backup) |

The root overlay is small (222M with 82% used on the test box) and shared with packages. Anything that grows over time doesn't belong there.

sysupgrade, the backup archive (`ns.backup` runs `sysupgrade -k -b`) and HA sync (`ns-rsync.sh` iterates `sysupgrade -l`) all use **the same list**:

1. every path in `/etc/sysupgrade.conf` and `/lib/upgrade/keep.d/*`, unconditionally;
2. every package conffile whose content differs from the checksum shipped in the package (`/lib/apk/packages/*.conffiles_static`).

The Makefile's `conffiles` define feeds both. At build time (`include/package-pack.mk`), each entry the package ships as a regular file gets a checksum in `conffiles_static`. Every other entry (a file created at runtime, a directory) is written to a generated `/lib/upgrade/keep.d/<pkg>`.

So one `conffiles` line makes a path survive sysupgrade, land in backups and get synced to the HA backup node. Check the result with `sysupgrade -l`.

## Pick the location

| What | Where |
|---|---|
| User-facing configuration, anything the API/UI reads or writes | UCI: `/etc/config/<pkg>` |
| Secrets (tokens, passwords, keys) | UCI option in the package's config |
| File generated from UCI (daemon config, nft snippet, JSON) | regenerate it from UCI at service start; don't persist it |
| Non-UCI file that's genuinely user data (certificates, an uploaded list) | `/etc/<pkg>/...` declared in the Makefile `conffiles` |
| Runtime state: pid, socket, lock, cache, last-run marker | `/var/run/<pkg>/` |
| Small runtime values shell scripts share | UCI state: `uci -P /var/state set <pkg>.<section>.<opt>=...` |
| Data that grows (DB, history, metrics, logs) | `/mnt/data/<pkg>/` when storage is ok, else `/var/lib/<pkg>/` with a size/retention cap |

The test for "UCI or file": if a human or the API would ever edit it, it's UCI. Files that are a function of UCI are build artifacts. Persisting them creates two sources of truth that drift after a restore or HA sync.

## UCI configuration

Ship the default config in the package and declare it as a conffile:

```makefile
define Package/ns-foo/conffiles
/etc/config/ns-foo
endef

define Package/ns-foo/install
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) ./files/ns-foo.conf $(1)/etc/config/ns-foo
	...
endef
```

```
config main 'config'
	option enabled '0'
```

- Use named sections (`config main 'config'`) for singletons so code can address `ns-foo.config.enabled` directly.
- The `conffiles` define must use the package's own name (`Package/ns-foo/conffiles`). A typo there silently drops the declaration.
- **Adding or renaming options later is a migration, not a change to the shipped file.** apk keeps a conffile the user modified and writes the new version next to it as `*.apk-new`, which nothing reads (several are sitting in `/etc` on the test device). Write a uci-default that sets the new option only when missing:

  ```sh
  uci -q get ns-foo.config.new_opt > /dev/null || uci set ns-foo.config.new_opt='default'
  ```

  See the `ns-background-work` skill for uci-default rules (idempotent, runs on every upgrade).
- APIs don't commit; `ns.commit` commits and fires reload triggers. Shell scripts outside the API that change UCI commit their own package (`uci commit ns-foo`).

Reading config from shell uses `/lib/functions.sh`: `config_load`, `config_get <var> <section> <option> [default]`, `config_get_bool`, `config_foreach`, `config_list_foreach`. Python uses `EUci` (see the `python-nethsecurity` skill).

`references/uci.md` has the UCI file syntax, every `uci` CLI command, the full shell API (`config_*`, `uci_*`, state helpers) with its gotchas, and links to the sysupgrade/conffiles source. Read it before writing UCI-handling shell code instead of guessing a helper.

## Secrets

Keep them as an option in the package's UCI config, like `ns-plug.config.secret`. That way they're in the backup, survive sysupgrade and reach the HA peer with no extra work. The backup archive is encrypted only when `/etc/backup.pass` is set, so treat it as potentially plaintext.

When handing a secret to a process:

- never on the command line: argv is world-readable in `ps` and `/proc`;
- write it to a file under `/var/run/<pkg>/` created with `umask 077` and pass the path, as `victoria-metrics/files/vmalert.initd` does;
- or pass it through `procd_set_param env` when the program only reads env.

Never log a secret, and keep it out of API responses: return a boolean like `has_secret` instead.

## Runtime state

- Create directories at service start (`mkdir -p /var/run/ns-foo` in `start_service`), never at package install: `/var` is empty after every reboot.
- Anything under `/var` must be rebuildable. If losing it on reboot is a bug, it belongs in UCI or on storage.

## Persistent data and ns-storage

Data storage is optional. `storage-status` (from `ns-storage`) prints `ok` only when `fstab.ns_data` is configured **and** its label is actually mounted at the target. It prints `error` when configured but not mounted, and `not_configured` otherwise.

Decide the path from the real status, not from the fstab config. A configured-but-failed disk leaves an empty `/mnt/data` directory on the overlay, and writing there fills the root filesystem:

```sh
local data_dir max_size
if [ "$(storage-status 2>/dev/null)" = "ok" ]; then
	data_dir="$(uci -q get fstab.ns_data.target)/ns-foo"
else
	data_dir="/var/lib/ns-foo"
	max_size="50MB"
fi
mkdir -p "$data_dir"
```

- Without storage, data lives on tmpfs (RAM) and is lost on reboot. Always cap it there: retention, max size, or row count.
- Let the user override the path with a UCI option (e.g. `storage_path`), and only auto-detect when it's empty.

**Storage added or removed**: `ns-storage/files/add-storage` and `remove-storage` restart each consumer explicitly. A new consumer adds its own line to both:

```sh
# add-storage, after the mount and existing restarts
/etc/init.d/ns-foo restart

# remove-storage, stop before the unmount and start after it
/etc/init.d/ns-foo stop
...
/etc/init.d/ns-foo start
```

When the consumer keeps something in `/var` that should move to the disk on mount, put a merge step next to the restart in `add-storage` (as the OpenVPN connections DB does). Don't watch block hotplug events for it.

**Nightly flush**: `sync-data` runs from cron at 01:40 and executes every executable in `/usr/libexec/sync-data/`. Drop a script there to copy tmpfs data to the disk when the consumer can't write to storage directly.

## Non-UCI files that must persist

Declare them in the Makefile `conffiles`, next to the UCI config. Don't ship a separate `.keep` file:

```makefile
define Package/ns-foo/conffiles
/etc/config/ns-foo
/etc/ns-foo/certs/
/etc/ns-foo/token
endef
```

- Shipped files (`/etc/config/ns-foo`) are kept once they differ from the package version, and aren't overwritten on upgrade.
- Paths the package doesn't ship (`/etc/ns-foo/token` created at runtime, the `certs/` directory) land in the generated `/lib/upgrade/keep.d/ns-foo` and are kept unconditionally.
- Directories are listed with a trailing `/` by convention.

Everything listed is also copied to the HA backup node. Whether the backup node actually applies it is handled by `ns-ha` restore hooks, not by `conffiles`.

Don't add generated files, caches or anything large. On subscribed systems the backup archive is uploaded nightly by `ns-plug` (`send-backup`).

## Don't copy

- `packages/ns-dpi/files/20_dpi` creates `/etc/config/dpi` with `uci import` from a uci-default instead of shipping it as a conffile. The ns-dpi Makefile also declares the conffile under `Package/ns-plug/conffiles`. Its own TODO says so.
- `packages/ns-openvpn/files/20-openvpn-merge-connections-db` is a block hotplug handler that polls `/proc/mounts` in a sleep loop to detect storage. Use the explicit call from `add-storage` instead.
- `*.keep` files installed to `/lib/upgrade/keep.d` by hand (`ns-plug`, `ns-api`, `ns-api-server`, `ns-dedalo`). Put those paths in `conffiles` instead.
- `victoria-metrics/files/victoria-metrics.initd` and `victoria-logs/files/victoria-logs.initd` pick `/mnt/data` when `fstab.ns_data.target` is set, without checking it's mounted. Copy their tmpfs fallback and caps, not their detection.

## Verify on a device

```sh
sysupgrade -l | grep ns-foo          # in backup, sysupgrade and HA sync?
ls /lib/upgrade/keep.d/
find /etc -name '*.apk-new'          # conffiles skipped on upgrade
storage-status
df -h / /tmp /mnt/data               # overlay and RAM headroom
du -sh /var/lib/ns-foo /mnt/data/ns-foo
```

## Sources

Re-check against these when `OWRT_VERSION` changes:

- `sysupgrade` (keep list, conffile checksums): https://github.com/openwrt/openwrt/blob/v25.12.5/package/base-files/files/sbin/sysupgrade
- conffile packaging for apk (`conffiles_static`): https://github.com/openwrt/openwrt/blob/v25.12.5/include/package-pack.mk
- Wiki, UCI: https://openwrt.org/docs/guide-user/base-system/uci
- Wiki, configuration in scripts (`config_load`, `config_get`, ...): https://openwrt.org/docs/guide-developer/config-scripting
- Wiki, backup and restore: https://openwrt.org/docs/guide-user/troubleshooting/backup_restore
- `packages/ns-storage/README.md`, `packages/ns-ha/README.md` in this repo
