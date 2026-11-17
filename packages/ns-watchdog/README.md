# ns-watchdog

Hardware watchdog support for NethSecurity on x86.

procd opens `/dev/watchdog` at boot, sets a 30 seconds timeout and pings it every 5 seconds.
If the kernel or procd hangs, the pings stop and the watchdog resets the machine.
This package ships the watchdog drivers and picks the one that matches the hardware,
so `/dev/watchdog` is a device that can actually reset the system.

## Supported hardware

| Module | Hardware |
|---|---|
| `i6300esb` | Intel 6300ESB; virtual watchdog on QEMU/KVM/Proxmox |
| `iTCO_wdt` | Intel chipsets and SoCs served by `lpc_ich` (ICH, older PCH, many Atom/Celeron) |
| `sp5100_tco` | AMD chipsets (SP5100/SB800 and newer), e.g. PC Engines APU |
| `softdog` | Software watchdog, used only when configured |

## How the driver is selected

The first device that registers gets `/dev/watchdog`, so the result would depend on load order.
For this reason kmodloader must not load watchdog modules on its own.
The package adds a `blacklist` block between `# BEGIN ns-watchdog` and `# END ns-watchdog` to `/etc/modules.conf`.
kmodloader honours it both before preinit (`/etc/modules-boot.d`) and later in `/etc/init.d/boot` (`/etc/modules.d`);
`insmod` ignores it.

Before preinit kmodloader reads the copy in the read-only image, which always has the block.
`/etc/init.d/boot` reads the overlay copy, which sysupgrade and backups save and restore,
so a restored file may miss the block or carry an old one.
The preinit hook writes the block again when it differs and logs it.

The preinit hook `/lib/preinit/83_ns_watchdog` runs before procd opens the device and:

1. writes the blacklist block again if it is missing or outdated;
2. unloads any watchdog module loaded anyway (a module whose watchdog is already running cannot be unloaded and is kept,
   and it owns `/dev/watchdog`);
3. stops if the watchdog is disabled (see below);
4. if `watchdog_module` is set, loads only that module;
5. otherwise loads the modules in this order:
   `i6300esb`, `iTCO_wdt`, `sp5100_tco`.
   A module that registers no device is unloaded again.
   The first one that registers a device owns `/dev/watchdog`.
   Other devices found stay loaded as `watchdog1`, `watchdog2`, ...;
   if the BIOS armed one of them, the kernel keeps pinging it.

The choice is logged to the kernel log:

```
dmesg | grep ns-watchdog
```

Check the status:

```
ubus call system watchdog
ls -l /dev/watchdog*
```

## Configuration

Options in the `system` section of `/etc/config/system`:

| Option | Default | Description |
|---|---|---|
| `watchdog` | `1` | `0` disables the watchdog at next boot |
| `watchdog_module` | empty | load only this module, e.g. `softdog` |

Disable the watchdog:

```
uci set system.@system[0].watchdog=0
uci commit system
reboot
```

Use the software watchdog when the hardware has none:

```
uci set system.@system[0].watchdog_module=softdog
uci commit system
reboot
```

Stop the watchdog until next reboot:

```
ubus call system watchdog '{"magicclose":true,"stop":true}'
```

If the system resets in a loop before the configuration can be changed,
edit the boot entry in the GRUB menu and append `ns.watchdog=0` to the kernel command line.

Disabling only keeps the hook from loading drivers: it does not stop a watchdog that is already running
(see Limitations).

## Limitations

- `iTCO_wdt` on Intel 100-series and newer PCH needs `i2c-i801`, which is not in the image.
- Super I/O watchdogs (`w83627hf_wdt`, `it87_wdt`, `f71808e_wdt`), `ib700wdt` and `mlx_wdt`
  are not shipped. Super I/O drivers poke shared configuration ports on any board,
  and `ib700wdt` always registers a device without probing the hardware.
  If one of them is installed manually, the preinit hook unloads it unless `watchdog_module` names it.
- A watchdog armed by the BIOS through an unsupported chip (e.g. the NCT6102 Super I/O on PC Engines APU)
  is not pinged by anyone: disable it in the BIOS, or the board resets after its timeout.
- When the watchdog is disabled, and in failsafe mode, no driver is loaded.
  A watchdog armed by the BIOS then has nobody pinging it and resets the board after its timeout,
  as it did before this package: disable it in the BIOS.
- A watchdog driver built into the kernel, such as `xen_wdt` on Xen guests, is opened by procd
  before preinit runs: `watchdog=0` and `ns.watchdog=0` do not disable it.
  Use `ubus call system watchdog '{"magicclose":true,"stop":true}'` after each boot.
- `softdog` runs inside the kernel: it does not catch hard kernel lockups.
- VMware and Hyper-V have no supported virtual watchdog.
  On Proxmox, add a watchdog device to the VM, e.g. `watchdog: model=i6300esb,action=reset`.
- The kernel is built without `CONFIG_WATCHDOG_SYSFS`, so `/sys/class/watchdog/*` has no attributes.
