---
name: ns-state-and-persistence
description: Decide where a NethSecurity package keeps configuration, secrets, runtime state, caches and historical data, and make it survive (or not) reboot, package upgrade, sysupgrade, backup/restore and HA sync. Use whenever a task adds a config file or UCI option, writes any file on the device, stores a token or password, keeps a database/history/log, touches `/etc/config`, `conffiles`, `/lib/upgrade/keep.d`, `/etc/sysupgrade.conf`, `/var`, `/tmp`, `/mnt/data`, `ns-storage`, `sync-data`, or when the user asks "where should this live", "will it survive an upgrade", "is it in the backup", even if persistence isn't mentioned explicitly.
metadata:
  domain: nethsecurity-packages
  type: runtime
---

## The filesystem you're writing to

| Path | Backed by | Reboot | Package upgrade | sysupgrade / backup / HA sync |
|---|---|---|---|---|
| `/etc/config/*` (UCI) | root overlay | kept | kept (see conffiles) | kept |
| other files under `/etc`, `/usr`, `/opt` | root overlay | kept | overwritten if shipped by the package, unless a conffile | kept only if declared in `conffiles` |
| `/var/*` (symlink to `/tmp`) | tmpfs (RAM) | **lost** | kept | not kept |
| `/mnt/data/*` | optional disk (`ns-storage`) | kept | kept | not kept |

The root overlay is small and shared with packages. Anything that grows over time doesn't belong there.

sysupgrade, backup and HA sync share one keep list, fed by the Makefile `conffiles`. One `conffiles` line makes a path survive all three; check with `sysupgrade -l`.

## Pick the location

| What | Where |
|---|---|
| User-facing configuration, anything the API/UI reads or writes | UCI: `/etc/config/<pkg>` |
| Secrets (tokens, passwords, keys) | UCI option in the package's config |
| File generated from UCI (daemon config, nft snippet, JSON) | regenerate it from UCI at service start; don't persist it |
| Non-UCI file that's genuinely user data (certificates, an uploaded list) | `/etc/<pkg>/...` declared in the Makefile `conffiles` |
| Runtime state: pid, socket, lock, cache, last-run marker | `/var/run/<pkg>/` |
| Small runtime values shell scripts share | UCI state: `uci -P /var/state set <pkg>.<section>.<opt>=...` |
| Data that grows (DB, history, metrics, logs) | storage when available, else `/var/lib/<pkg>/` with a size/retention cap |

The test for "UCI or file": if a human or the API would ever edit it, it's UCI. Files that are a function of UCI are build artifacts; persisting them creates two sources of truth that drift after a restore or HA sync.

## UCI configuration

- Ship the default config as `/etc/config/ns-foo` with `$(INSTALL_CONF)` and list it in `Package/ns-foo/conffiles`, using the package's own name.
- Use named sections (`config main 'config'`) for singletons so code can address `ns-foo.config.enabled` directly.
- Add or rename options with a uci-default that sets them only when missing, not by changing the shipped file: a user-modified conffile isn't replaced on upgrade (the new one lands as `*.apk-new`). See `ns-background-work` for uci-default rules.
- APIs don't commit, `ns.commit` does. Shell scripts outside the API commit their own package and reload what they changed.
- Shell reads config with `/lib/functions.sh`; Python uses `EUci` (see `python-nethsecurity`).

## Secrets

Keep them as an option in the package's UCI config, like `ns-plug.config.secret`, so they follow backup, sysupgrade and HA with no extra work. Treat the backup as potentially plaintext.

When handing a secret to a process:

- never on the command line;
- write it to a `umask 077` file under `/var/run/<pkg>/` and pass the path, as `victoria-metrics/files/vmalert.initd` does;
- or pass it through `procd_set_param env` when the program only reads env.

Never log a secret, and keep it out of API responses: return a boolean like `has_secret` instead.

## Runtime state

- Create directories at service start, never at package install: `/var` is empty after every reboot.
- Anything under `/var` must be rebuildable. If losing it on reboot is a bug, it belongs in UCI or on storage.

## Persistent data and ns-storage

Storage is optional. Pick the path from `storage-status` printing `ok`, not from `fstab.ns_data` being set: a configured but unmounted disk would make you fill the root filesystem. Fall back to `/var/lib/<pkg>`.

- On tmpfs, always cap the data: retention, max size, or row count.
- Let the user override the path with a UCI option, and only auto-detect when it's empty.
- React to storage being added or removed from `ns-storage/files/add-storage` and `remove-storage`, next to the other consumers, not from block hotplug events.
- To flush tmpfs data to disk periodically, drop an executable in `/usr/libexec/sync-data/`.

Read `packages/ns-storage/README.md` before wiring a new consumer.

## Non-UCI files that must persist

Declare them in the Makefile `conffiles`, next to the UCI config (directories with a trailing `/`). Don't ship a separate `.keep` file. Read `include/package-pack.mk` for how shipped and runtime-created entries differ.

Don't add generated files, caches or anything large: everything listed goes into the backup and to the HA peer.

## Don't copy

Configs created with `uci import` from a uci-default instead of a shipped conffile, hand-installed `*.keep` files, storage detection by polling `/proc/mounts` or by reading `fstab.ns_data.target` alone.

## Verify on a device

```sh
sysupgrade -l | grep ns-foo          # in backup, sysupgrade and HA sync?
find /etc -name '*.apk-new'          # conffiles skipped on upgrade
storage-status
df -h / /tmp /mnt/data
```

## Sources

Read the OpenWrt files at the tag `OWRT_VERSION` in `build.conf.defaults` names:

- `package/base-files/files/sbin/sysupgrade` (keep list, conffile checksums)
- `include/package-pack.mk` (`conffiles` handling)
- `package/base-files/files/lib/functions.sh` (`config_*` shell API)
- `package/system/uci/files/lib/config/uci.sh` (`uci_*` shell helpers, state helpers)
- Wiki, UCI: https://openwrt.org/docs/guide-user/base-system/uci
- Wiki, configuration in scripts: https://openwrt.org/docs/guide-developer/config-scripting
- Wiki, backup and restore: https://openwrt.org/docs/guide-user/troubleshooting/backup_restore
- `packages/ns-storage/README.md`, `packages/ns-ha/README.md` in this repo
