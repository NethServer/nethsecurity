# hotplug reference

Covers OpenWrt v25.12 (`OWRT_VERSION` in `build.conf.defaults`). Re-check the sources when the version changes.

Sources:

- Wiki, hotplug (subsystems, variables, examples): https://openwrt.org/docs/guide-user/base-system/hotplug
- `/sbin/hotplug-call`: https://github.com/openwrt/openwrt/blob/v25.12.5/package/base-files/files/sbin/hotplug-call
- netifd interface events (`interface-event.c`): https://github.com/openwrt/netifd
- procd hotplug dispatcher (`hotplug-dispatch.c`) and kernel rules (`hotplug.json`): https://github.com/openwrt/procd, https://github.com/openwrt/openwrt/blob/v25.12.5/package/system/procd/files/hotplug.json

## How scripts get run

Scripts live in `/etc/hotplug.d/<subsystem>/`. Every file in the directory runs for every event of that subsystem, **in name order**, so use a two-digit prefix (`90-ns-foo`). The script has to filter `ACTION` and the other variables itself.

There are two dispatchers:

- **`iface`**: netifd runs `/sbin/hotplug-call iface` with the event in the environment. `hotplug-call` sources `/lib/functions.sh`, then sources each script in a subshell (`( . $script )`). netifd runs one hotplug call at a time and queues the next interface event until it finishes. A slow script delays every later handler **and** the next interface event (e.g. mwan3 and firewall reacting to a WAN change).
- **Everything else** (`net`, `block`, `usb`, `ntp`, `dhcp`, `neigh`, ...): procd's hotplug dispatcher runs each script as `/bin/sh -c '. /lib/functions.sh; . <script>'` with stdio on `/dev/null`, one after the other.

Consequences for scripts:

- They're sourced, so the file doesn't need the exec bit (install with `$(INSTALL_DATA)`), and `exit` only ends that script.
- stdout/stderr are lost or useless. Log with `logger -t ns-foo`.
- Filter first, then do work. Anything long-running goes to a one-shot procd job (`/etc/init.d/ns-foo-x start`) so the dispatcher isn't blocked.
- `/lib/functions.sh` is already loaded. Source `/lib/functions/network.sh` yourself if you need `network_find_wan`, `network_get_device`, etc.

## Subsystems

Directories present on a NethSecurity 8 device: `acme block dhcp iface ipsec keepalived leds neigh net ntp openvpn tftp tty`. Some are created by packages (`acme`, `ipsec`, `keepalived`, `openvpn`) rather than OpenWrt core. Their variables are documented in those packages, not here.

### iface (netifd logical interfaces)

| `ACTION` | When |
|---|---|
| `ifup` | interface came up |
| `ifdown` | interface went down |
| `ifupdate` | address/route/prefix/data changed on an up interface |
| `ifup-failed` | bring-up failed |
| `iflink` | link came up (before L3 is up) |
| `create` | interface object created |
| `reload` | interface config reloaded |
| `free` | interface object freed |

Variables: `INTERFACE` (logical name, e.g. `wan`), `DEVICE` (Linux device, e.g. `eth1`). On `ifupdate`, `IFUPDATE_ADDRESSES`, `IFUPDATE_ROUTES`, `IFUPDATE_PREFIXES` and `IFUPDATE_DATA` are set to `1` for what changed.

### net (kernel network devices)

`ACTION`: `add`, `remove`. Variables: `INTERFACE` (device name, not the logical one), `DEVICENAME`, `DEVTYPE`, `DEVPATH`, `IFINDEX`, `SUBSYSTEM=net`, `SEQNUM`.

### block (disks, partitions)

`ACTION`: `add`, `remove`, `change` (for example dm-crypt). Variables: `DEVNAME`, `DEVICENAME`, `DEVPATH`, `DEVTYPE` (`disk`/`partition`), `MAJOR`, `MINOR`, `SUBSYSTEM=block`, `SEQNUM`.

### ntp (sysntpd)

`ACTION`: `step`, `stratum`, `unsync`, `periodic`. Variables: `stratum`, `offset`, `freq_drift_ppm`, `poll_interval`. Without sync, a `periodic` event with `stratum=16` fires about every 11 minutes. Use `stratum` to run something once the clock is trustworthy (certificate checks, license validation).

### usb / tty / usbmisc

`ACTION`: `add`, `remove` (`usb` and `tty` also `bind`, `unbind`). Variables: `DEVNAME`, `DEVPATH`, `DEVICENAME`, `MAJOR`, `MINOR`, `SEQNUM`, plus `PRODUCT`, `TYPE`, `BUSNUM`, `DEVNUM`, `DEVTYPE` on `usb`. `bind` also fires at boot for already-plugged devices (coldplug).

### dhcp, neigh, tftp

Emitted by dnsmasq (`dhcp`, `tftp`) and the neighbor tracker (`neigh`). The wiki doesn't list their variables. Dump the environment (below) before relying on any.

## Debugging

Dump the environment of real events:

```sh
cat > /etc/hotplug.d/iface/00-debug <<'EOF'
logger -t hotplug "$(env | tr '\n' ' ')"
EOF
ifup wan          # or unplug/replug, or wait for the event
logread -e hotplug
rm /etc/hotplug.d/iface/00-debug
```

Fire a handler by hand with a fake event (iface only, since that path goes through `hotplug-call`):

```sh
ACTION=ifup INTERFACE=wan DEVICE=eth1 /sbin/hotplug-call iface
```

That runs **every** script in `/etc/hotplug.d/iface/`, not just yours. Do it only on a test device.
