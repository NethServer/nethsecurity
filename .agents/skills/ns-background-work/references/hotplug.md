# hotplug

Sources, read at the tag `OWRT_VERSION` in `build.conf.defaults` names:

- Wiki, hotplug (subsystems, `ACTION` values, variables): https://openwrt.org/docs/guide-user/base-system/hotplug
- `package/base-files/files/sbin/hotplug-call`
- netifd `interface-event.c` (iface events): https://github.com/openwrt/netifd
- procd `hotplug-dispatch.c` and `package/system/procd/files/hotplug.json` (other subsystems): https://github.com/openwrt/procd

## Gotchas

- Every script in the directory runs for every event: use a two-digit prefix and filter `ACTION` yourself.
- Scripts are sourced: install with `$(INSTALL_DATA)`. Source `/lib/functions/network.sh` yourself for `network_find_wan` and friends.
- Keep iface handlers fast; events are handled one at a time, so a slow script delays mwan3 and the firewall.
- stdout/stderr are lost. Log with `logger -t ns-foo`.
- For package-provided directories (`acme`, `ipsec`, `keepalived`, `openvpn`) read that package for the variables. For `dhcp`, `neigh`, `tftp`, dump the environment with a temporary `logger -t hotplug "$(env)"` handler before relying on any variable.
- `ACTION=ifup INTERFACE=wan DEVICE=eth1 /sbin/hotplug-call iface` fires a fake event, but runs **every** iface script. Test devices only.
