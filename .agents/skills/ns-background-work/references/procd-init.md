# procd init scripts

Read the sources at the tag `OWRT_VERSION` in `build.conf.defaults` names instead of guessing a helper or param:

- `package/base-files/files/etc/rc.common`: actions and default handlers
- `package/system/procd/files/procd.sh`: every `procd_*` helper, param and trigger
- procd daemon, `service/instance.c` decides restart vs no-op: https://github.com/openwrt/procd
- Wiki: https://openwrt.org/docs/guide-developer/procd-init-scripts

## Gotchas

- Run the process in the **foreground**; procd treats a self-forking daemon as exited.
- `start` on a running instance only restarts it when procd's view changed (command line, env, `file`, `netdev`, `data`), not when the UCI config the daemon reads changed. Hence `reload_service() { stop; start; }`.
- To stop a daemon when disabled, don't declare the instance in `start_service` (`return 0`).
- One function argument per command-line argument: `procd_append_param command "-addr" "$addr"`, never `"-addr $addr"`.
- Reload triggers fire on `reload_config`, which `ns.commit` runs. After a manual `uci commit`, run `reload_config` yourself.
- Mount triggers need the path under a mount defined in `/etc/config/fstab` (`ns-storage` uses `ns_data`).
- `exec` the real binary at the end of any wrapper script, or its children survive `stop`.
- Init scripts also run on the build host for `enable` (`IPKG_INSTROOT` set). Keep file-scope code to variable assignments.
- `INIT_TRACE=1` traces the rc.common run; `PROCD_DEBUG=1` dumps the JSON sent to procd.
