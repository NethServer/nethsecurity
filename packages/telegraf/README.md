# Telegraf

## Overview

Telegraf is the metrics collection agent that gathers host and service metrics and forwards them to Victoria Metrics for storage, alerting, and visualization.

## Architecture

```
/usr/libexec/telegraf-services       ← service status via ubus
/var/run/mwan3/iface_state/          ← WAN interface status via mwan3 state files
/proc filesystem                     ← CPU, memory, disk, network
     │
     ▼
  Telegraf (inputs.exec, inputs.cpu, inputs.mem, …)
     │
     ▼
Victoria Metrics (http://127.0.0.1:8428)
     │
     └─▶ vmalert  (alert rules evaluation)
```

## Configuration Files

| Path | Description |
|------|-------------|
| `/etc/telegraf.conf` | Main Telegraf agent config and InfluxDB output |
| `/etc/telegraf.conf.d/*.conf` | Additional Telegraf input configurations for plugins |


## Collected Metrics

To see the list of metrics collected by Telegraf, use:
```bash
/usr/bin/telegraf --config /etc/telegraf.conf --config-directory /etc/telegraf.conf.d --test
```

### Service Health Monitoring (services.conf)

**How it works**: Every 60 seconds, Telegraf executes `/usr/libexec/telegraf-services`, which queries procd via `ubus call service list`, filters the fixed monitored service whitelist, and converts the matching configured instances to metrics.

**Metric format**:
```
procd_service_running{service="nginx", instance="instance1"} = 1 (running) or 0 (down)
procd_service_pid{service="nginx", instance="instance1"} = process_id
procd_service_exit_code{service="nginx", instance="instance1"} = last_exit_code
```

Only these services are monitored:

```text
banip
conntrackd
cron
dedalo
dedalo_users_auth
dnsmasq
dropbear
keepalived
mwan3
netifyd
nginx
ns-api-server
ns-clm
ns-flashstart
ns-flows
ns-plug
ns-plug-alert-proxy
ns-stats
ns-ui
odhcpd
openvpn
qosify
rpcd
rsyslog
snort
swanctl
sysntpd
telegraf
victoria-metrics
vmalert
```

Services with no instances are skipped.

Notable skipped services:
- `adblock`: excluded because ubus info is not reliable (always shows 1 instance even when disabled)

##### Querying Service Status

```bash
# All services and their running state
curl -s 'http://127.0.0.1:8428/api/v1/query?query=procd_service_running'

# Run collection script manually to preview output
/usr/libexec/telegraf-services
```

### Multi-WAN Monitoring (mwan.conf)

**How it works**: Every 60 seconds, Telegraf executes `/usr/libexec/telegraf-mwan`, which reads `/var/run/mwan3/iface_state/` to determine each WAN interface's online/offline state (maintained by mwan3 in real-time).

**Metric format**:
```
mwan_interface_online{interface="wan"} = 1 (online) or 0 (offline)
```

#### Querying WAN Status

```bash
# All WAN interfaces and current state
curl -s 'http://127.0.0.1:8428/api/v1/query?query=mwan_interface_online'

# Run collection script manually
/usr/libexec/telegraf-mwan
```

### Storage Status Monitoring (storage.conf)

**How it works**: Every 60 seconds, Telegraf executes `/usr/libexec/telegraf-storage-status`, which runs `storage-status` and exports the current storage health as a metric.

**Metric format**:
```
storage_status_error = 1 (error) or 0 (ok / not configured)
```

## Advanced Configuration

To add custom metrics or modify collection intervals, edit the `/etc/telegraf.conf.d/` files following [Telegraf documentation](https://docs.influxdata.com/telegraf/). Common customizations:

- Modify collection intervals: change `interval` in main config
- Add new input plugins: append `[[inputs.plugin_name]]` sections

After changes, restart Telegraf:
```bash
/etc/init.d/telegraf restart
```

## References

- [Telegraf documentation](https://docs.influxdata.com/telegraf/)
- [Telegraf exec plugin](https://github.com/influxdata/telegraf/tree/master/plugins/inputs/exec)
- [OpenWrt procd init scripts](https://openwrt.org/docs/guide-developer/procd-init-scripts)
- [OpenWrt ubus reference](https://openwrt.org/docs/techref/ubus)
- [Victoria Metrics integration](../victoria-metrics/README.md)
