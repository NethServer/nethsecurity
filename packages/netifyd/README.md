# netifyd

NethSecurity integration package for [Netify DPI](https://netify.ai/). The package ships
pre-built binaries (daemon + plugins + libraries) downloaded from the NethSecurity binary
distribution mirror and wires them into the OpenWrt build.

## How it works

Traffic inspection is performed via Linux netfilter queue (NFQUEUE). The nftables chains
defined in `/usr/share/nftables.d/table-pre/10-netifyd-nfqueue.nft` attach to the `input`,
`forward`, and `output` hooks and divert packets to queues 50–53 for DPI analysis. Netifyd
only inspects the first 32 packets of each connection; subsequent packets are accepted
directly by nftables.

The daemon is managed via procd and reads its configuration from:
- `/etc/netifyd.conf` — daemon-level settings (informatics, coredumps, etc.)
- `/etc/config/netifyd` — UCI configuration (enabled, autoconfig, interface lists)
- `/etc/netifyd/interfaces.d/10-nfqueue.conf` — nfqueue capture interface settings
- `/etc/netifyd/plugins.d/` — plugin loading configuration

## UCI configuration

### `/etc/config/netifyd`

```
config netifyd
    option enabled 1

    # Optional: supplementary daemon options
    #list options '-t'

config ns_config 'config'
    list bypassv4 '192.168.100.0/24'
    list bypassv6 '2001:db8::/32'
```

The `netifyd` section controls the daemon. The `ns_config 'config'` section is a
NethSecurity-specific extension that holds additional options managed by `ns.netifyd`.

### Options — `netifyd` section

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | `1` | Start the daemon at boot |
| `list options` | — | Extra command-line arguments passed to the daemon |

## DPI bypass

Traffic from or to addresses in the bypass lists is accepted immediately by nftables and
never queued to netifyd. This is useful to exclude high-volume or latency-sensitive hosts
from inspection.

### How it works

1. On every firewall reload, fw4 executes `/usr/share/netifyd/netify.user` (registered via
   the `ns_netifyd_include` firewall include in `/etc/config/firewall`).
2. The script reads `netifyd.config.bypassv4` and `netifyd.config.bypassv6` from UCI and
   populates the `nfq_bypass_v4` (IPv4) and `nfq_bypass_v6` (IPv6) nftables sets.
3. The nftables chains in `10-netifyd-nfqueue.nft` match source and destination addresses
   against those sets and accept matching packets before the NFQUEUE rule.

### Firewall include

The firewall include is created on first boot by the UCI default
`99-netify-ns-defaults` (only if not already present):

```
config include 'ns_netifyd_include'
    option path '/usr/share/netifyd/netify.user'
    option fw4_compatible '1'
```

### Managing bypass lists

Bypass lists are managed via the `ns.netifyd` API (see `packages/ns-api`):

```bash
# Read current bypass lists
api-cli ns.netifyd get-bypass

# Set bypass lists (replaces existing entries)
api-cli ns.netifyd set-bypass --data '{
  "bypassv4": ["192.168.100.0/24", "10.0.0.5"],
  "bypassv6": ["2001:db8::/32"]
}'
```

Or directly via UCI (requires a firewall reload to take effect):

```bash
uci set netifyd.config.bypassv4='192.168.100.0/24'
uci add_list netifyd.config.bypassv4='10.0.0.5'
uci commit netifyd
fw4 reload
```

## Netify informatics (cloud sink)

The daemon can optionally send anonymised DPI telemetry to the Netify cloud. This is
controlled via `netifyd --enable-informatics` / `netifyd --disable-informatics`, which
write to `/etc/netifyd.conf`. The current state is exposed by `ns.netifyd status`.

```bash
api-cli ns.netifyd status
api-cli ns.netifyd enable
api-cli ns.netifyd disable
```

## UCI defaults

| Script | Purpose |
|--------|---------|
| `99-netify-v4-migrate` | Migrates from the old `netify.d` directory layout; ensures the service is enabled |
| `99-netify-enable-nfqueue` | Removes deprecated `external_if` / `internal_if` UCI entries (nfqueue mode does not use them) |
| `99-netify-disable-autoconfig` | Sets `autoconfig = 0` so NethSecurity controls interface assignment |
| `99-netify-disable-coredumps` | Adds `enable_coredumps = no` to `netifyd.conf` if missing |
| `99-netify-ns-defaults` | Creates the `ns_config 'config'` UCI section and the `ns_netifyd_include` firewall include if absent |

## Key files

| Path | Description |
|------|-------------|
| `/etc/config/netifyd` | UCI configuration (daemon options + bypass lists) |
| `/etc/netifyd.conf` | Daemon configuration file |
| `/etc/netifyd/interfaces.d/10-nfqueue.conf` | nfqueue capture interface (queues 50–53, lan role) |
| `/usr/share/netifyd/netify.user` | fw4 include script: populates bypass nftables sets from UCI |
| `/usr/share/nftables.d/table-pre/10-netifyd-nfqueue.nft` | nftables chains for nfqueue + bypass sets |

## Version management

The package version (`PKG_VERSION`) tracks the upstream Netify release. Binaries are fetched
from:

```
https://updates.nethsecurity.nethserver.org/netifyd-dist/netifyd-<version>/<arch>/
```

To update: change `PKG_VERSION` and `PKG_RELEASE` in the `Makefile` and update all
`HASH` values to match the new binaries.
