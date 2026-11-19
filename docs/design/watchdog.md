---
layout: default
title: Hardware watchdog
parent: Design
---

# Hardware watchdog

A hardware watchdog resets the machine when the kernel or procd hangs.
procd opens `/dev/watchdog` at boot, sets a 30 seconds timeout and pings it every 5 seconds:
if the pings stop, the watchdog resets the machine.

The x86 image ships no watchdog driver, so the watchdog is off by default.
The drivers are built as packages (`config/watchdog.conf`) and can be installed
from the NethSecurity package repository on the hardware that needs them.

## Pick the driver

Install **only one** driver: the one matching the hardware.
Only the first watchdog device that registers gets `/dev/watchdog`,
and each package loads its driver at boot on its own.
If more drivers are installed, the device that procd uses depends on load order.

| Package | Module | Hardware |
|---|---|---|
| `kmod-itco-wdt` | `iTCO_wdt` | Intel chipsets with an ICH or an older PCH, many Atom and Celeron SoCs |
| `kmod-sp5100-tco` | `sp5100_tco` | AMD chipsets (SP5100, SB800 and newer FCH), e.g. PC Engines APU |
| `kmod-i6300esb-wdt` | `i6300esb` | QEMU, KVM and Proxmox VE virtual machines with an `i6300esb` watchdog device |
| `kmod-w83627hf-wdt` | `w83627hf_wdt` | Winbond and Nuvoton Super I/O chips (W836xx, NCT6xxx) |
| `kmod-it87-wdt` | `it87_wdt` | ITE Super I/O chips (IT87xx) |
| `kmod-f71808e-wdt` | `f71808e_wdt` | Fintek Super I/O chips (F718xx, F81xxx) |
| `kmod-ib700-wdt` | `ib700wdt` | IB700 single board computers only |
| `kmod-softdog` | `softdog` | Any hardware: software watchdog |

Prefer the chipset driver (`iTCO_wdt`, `sp5100_tco`) when the hardware has one.
Use a Super I/O driver only when the board documentation says the watchdog is on that chip.

Identify the hardware:

```
lspci -nn | grep -iE 'isa bridge|lpc|smbus|watchdog'
cat /sys/class/dmi/id/sys_vendor /sys/class/dmi/id/product_name
```

- An Intel `LPC Interface Controller` or `ISA bridge`: `kmod-itco-wdt`.
- An AMD `FCH SMBus Controller` (`1022:780b`, `1022:790b`): `kmod-sp5100-tco`.
- `6300ESB Watchdog Timer` (`8086:25ab`): `kmod-i6300esb-wdt`.

Notes:

- `iTCO_wdt` on Intel 100-series and newer PCH needs `i2c-i801`, which is not in the image:
  on those systems the module loads but registers no device.
- `ib700wdt` does not check the hardware: it registers a device on any machine and takes `/dev/watchdog`.
  procd then pings a watchdog that cannot reset the machine. Never install it on other hardware.
- `softdog` runs inside the kernel: it does not catch hard kernel lockups.
- `kmod-it87-wdt` passes the `nogameport` and `nocir` parameters, which the current driver does not know:
  the kernel logs a warning and loads the module anyway.
- VMware and Hyper-V provide no supported virtual watchdog.
  On Proxmox VE, add the device to the virtual machine first:
  `qm set <vmid> --watchdog model=i6300esb,action=reset`.

## Enable the watchdog

Install the package, then reboot:

```
apk update
apk add kmod-sp5100-tco
reboot
```

The package loads the module right away, but procd opens `/dev/watchdog` only at boot.
To start the watchdog without a reboot:

```
ubus call system watchdog '{"stop":false}'
```

Check that it works:

```
ls -l /dev/watchdog*
ubus call system watchdog
dmesg | grep -iE 'wdt|watchdog|tco'
```

`status` is `running` when procd pings the watchdog.
To test the reset, stop the pings without closing the device:
`ubus call system watchdog '{"stop":true}'`. The machine resets after about 30 seconds.

## Disable the watchdog

Until the next reboot:

```
ubus call system watchdog '{"magicclose":true,"stop":true}'
```

Permanently, remove the package and reboot:

```
apk del kmod-sp5100-tco
reboot
```

## Upgrades

The driver is an extra package: after a system upgrade it is installed again by
`ns-restore-extra-packages`, as soon as the WAN is available.
The watchdog is off until then, and starts at the next reboot or with the `ubus` command above.

A watchdog started by the BIOS keeps running while no driver is loaded and resets the machine
after its timeout. Disable it in the BIOS, or install the matching driver: with a driver loaded
the kernel pings the watchdog until procd opens it (`CONFIG_WATCHDOG_HANDLE_BOOT_ENABLED=y`).
