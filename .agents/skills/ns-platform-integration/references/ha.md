# HA

- Events and `set_*` helpers: `packages/keepalived/files/lib/functions/keepalived/hotplug.sh`.
- Cron toggling: `update_cron` in `packages/ns-ha/files/ns.sh`.
- Sync: `ns-rsync.sh` and `10-adjust` in `packages/ns-ha/files`, `02-rsync` in `packages/keepalived`.
- Naming: pick a prefix in the band of similar services already in `/etc/hotplug.d/keepalived/` (applications `800`, cloud/reporting `900`).
- `packages/ns-ha/README.md` for the user-facing behavior; where it disagrees with the code, the code wins.
