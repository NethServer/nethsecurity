---
layout: default
title: Hardware watchdog
parent: Design
---

# Hardware watchdog

On x86 the image includes the `ns-watchdog` package.
It ships the watchdog drivers and selects the one matching the hardware at boot.
procd then opens `/dev/watchdog`, sets a 30 seconds timeout and pings it every 5 seconds:
if the kernel or procd hangs, the machine resets.

The watchdog is enabled by default, also on systems upgraded from previous releases.

## Why a selector

OpenWrt kmod packages load watchdog drivers from `/etc/modules-boot.d`.
Only the first device that registers gets `/dev/watchdog` (misc minor 130);
the others get `/dev/watchdogN` only and procd ignores them.

Some drivers do not probe the hardware: `ib700wdt` always registers a device.
On a PC Engines APU with all upstream modules installed, `ib700wdt` took `/dev/watchdog`
and the real `sp5100_tco` and NCT6102 Super I/O watchdogs were left out:
procd was pinging a watchdog that could not reset the board.

## Shipped drivers

Only drivers that bind to a chipset or PCI device are shipped:
`i6300esb`, `iTCO_wdt`, `sp5100_tco`, plus `softdog` (used only when configured).
Super I/O drivers (`w83627hf_wdt`, `it87_wdt`, `f71808e_wdt`) are left out on purpose:
they probe shared configuration ports on every board, and the chipset watchdog covers
the same machines in most cases. `ib700wdt` and `mlx_wdt` are left out as well.

## Boot sequence

1. procd init loads `/etc/modules-boot.d`. Watchdog modules are skipped:
   the `ns-watchdog` postinst blacklists them in `/etc/modules.conf` (a file owned by `ubox`,
   edited inside a `# BEGIN ns-watchdog` / `# END ns-watchdog` block).
   At this point kmodloader reads the copy in the read-only image, written at build time.
2. `/etc/preinit` runs the hooks; `/lib/preinit/83_ns_watchdog` runs after the overlay is mounted,
   so it can read UCI. It first writes the blacklist block again in the overlay copy when it differs:
   `/etc/modules.conf` is a conffile, saved and restored by sysupgrade and backups,
   so a restore can bring back a file without the block or with an old module list.
3. The hook loads the modules with `insmod`, which ignores the blacklist, in priority order
   (`i6300esb`, `iTCO_wdt`, `sp5100_tco`), and unloads the ones that registered no device.
4. procd enters its early state and opens `/dev/watchdog`.
5. `/etc/init.d/boot` runs kmodloader again on `/etc/modules.d`; the blacklist keeps it from
   loading the watchdog modules that were left out.

Without the blacklist, the first test images showed both problems: modules loaded before preinit,
and `softdog`, `iTCO_wdt` and `i6300esb` loaded again in step 5 after the selection.
On a QEMU Q35 machine `iTCO_wdt` could not even be unloaded in step 3, because its watchdog
was already running and the kernel holds a reference to the module in that case.
The hook keeps such a module, logs it and reports it as the device in use,
since it registered before any module loaded by the hook.

Nothing has opened a watchdog device before step 4, so unloading modules in step 3 is safe.
The kernel is built with `CONFIG_WATCHDOG_HANDLE_BOOT_ENABLED=y`:
a watchdog armed by the BIOS is pinged by the kernel until a program opens it.

## Disabling

- UCI: `system.@system[0].watchdog='0'`, applied at next boot.
- Kernel command line: `ns.watchdog=0`, to recover from a reset loop via the GRUB menu.
- Runtime, until reboot: `ubus call system watchdog '{"magicclose":true,"stop":true}'`.

`system.@system[0].watchdog_module` forces a single module, e.g. `softdog`,
which is never selected automatically.

Disabling only skips loading drivers. It does not stop a watchdog that was already running:

- a watchdog armed by the BIOS has no driver, so the kernel cannot ping it and it resets the board;
  this was already the case before `ns-watchdog`, and the same happens in failsafe mode;
- a built-in driver such as `xen_wdt` registers before init, and procd opens it before preinit.

Loading the driver while keeping procd off it is not possible from preinit,
because procd opens `/dev/watchdog` right after it.

See `packages/ns-watchdog/README.md` for supported hardware and limitations.
