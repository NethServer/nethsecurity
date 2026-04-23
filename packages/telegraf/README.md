# Telegraf on NethSecurity

## Overview

This package provides **Telegraf**, the metrics collection agent. It collects host and service metrics and forwards them to Victoria Metrics for storage, visualization, and alerting.

## Architecture

```
procd / ubus
     │
     ▼
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
     ├─▶ vmalert  (alert rules evaluation)
     └─▶ Grafana  (dashboards)
```

## Configuration Files

| Path | Description |
|------|-------------|
| `/etc/telegraf.conf` | Main Telegraf agent configuration and InfluxDB output |
| `/etc/telegraf.conf.d/os.conf` | CPU, memory, disk, network, process metrics |
| `/etc/telegraf.conf.d/services.conf` | Procd service status via `inputs.exec` |
| `/etc/telegraf.conf.d/mwan.conf` | mwan3 WAN interface status via `inputs.exec` |

## Collected Metrics

### OS and Hardware (`os.conf`)

All metrics are tagged `influxdb_db=os-metrics`.

| Telegraf Measurement | Key Fields | Description |
|----------------------|------------|-------------|
| `cpu` | `usage_idle`, `usage_user`, `usage_system` | Per-CPU usage |
| `mem` | `used`, `total`, `free`, `swap_*` | Memory and swap |
| `disk` | `used`, `total`, `free`, `inodes_*` | Disk space per mount |
| `net` | `bytes_sent`, `bytes_recv`, `err_in`, `err_out`, `drop_*` | Network interfaces |
| `netstat` | `tcp_established`, `tcp_time_wait` | TCP connection states |
| `nstat` | kernel SNMP counters | Network kernel stats |
| `processes` | `running`, `zombies`, `blocked` | Process states |
| `system` | `load1`, `load5`, `load15`, `n_cpus`, `uptime` | System load |
| `bond` | `status`, `failed_count` | Bonding interface stats |
| `ethtool` | driver-specific counters | NIC hardware stats |

### Service Status (`services.conf`)

All metrics are tagged `influxdb_db=os-metrics`.

| Telegraf Measurement | Tags | Fields | Description |
|----------------------|------|--------|-------------|
| `procd_service` | `service`, `instance`, `has_respawn` | `running`, `pid`, `exit_code` | Procd service health |

See [Service Monitoring](#service-monitoring) below for full details.

### WAN Interface Status (`mwan.conf`)

All metrics are tagged `influxdb_db=os-metrics`.

| Telegraf Measurement | Tags | Fields | Description |
|----------------------|------|--------|-------------|
| `mwan_interface` | `interface` | `online` | mwan3 WAN link state |

See [WAN Monitoring](#wan-monitoring) below for full details.

## Service Monitoring

### How It Works

Every 60 seconds, `/usr/libexec/telegraf-services` queries `ubus call service list` to get the current state of all procd-managed services. The output is converted to InfluxDB line protocol and ingested by Telegraf.

```
procd_service,service=nginx,instance=instance1,has_respawn=true running=1i,pid=8001i,exit_code=0i
procd_service,service=nginx,instance=instance1,has_respawn=true running=0i,pid=0i,exit_code=1i  ← service down
```

In Victoria Metrics, the metric is stored as:
```
procd_service_running{service="nginx", instance="instance1", has_respawn="true", db="os-metrics"} = 1
```

### The `has_respawn` Tag

Procd distinguishes two kinds of services:

- **Persistent daemons** (`has_respawn=true`): configured with `procd_set_param respawn` in their init script. Procd keeps these running and restarts them if they crash. These are the services that **should always be running** and are the primary targets for alerting.

- **Oneshot / optional services** (`has_respawn=false`): run once and exit, or are manually started on demand (e.g., `adblock`, `ns-binding`). A `running=false` state for these is expected and normal.

### Monitored Services (Default)

The following persistent services are discovered automatically on a default NethSecurity installation:

| Service | Instance | Description |
|---------|----------|-------------|
| `blockd` | `instance1` | Block device manager |
| `cron` | `instance1` | Task scheduler |
| `dnsmasq` | `ns_dnsmasq` | DNS/DHCP server |
| `dpireport` | `instance1` | DPI reporting |
| `dropbear` | `instance1` | SSH server |
| `mwan3` | `rtmon_ipv4`, `rtmon_ipv6` | Multi-WAN route monitor |
| `netdata` | `instance1` | System monitoring agent |
| `netifyd` | `instance1` | Network interface daemon |
| `network` | `instance1` | Network manager |
| `nginx` | `instance1` | Reverse proxy / web server |
| `ns-api-server` | `instance1` | NethSecurity API server |
| `ns-flows` | `instance1` | Flow tracking |
| `ns-stats` | `instance1` | Statistics collector |
| `odhcpd` | `instance1` | DHCPv6 / RA daemon |
| `qosify` | `instance1` | QoS daemon |
| `rpcd` | `instance1` | RPC daemon |
| `swanctl` | `instance1` | IKEv2/IPsec daemon |
| `sysntpd` | `instance1` | NTP daemon |
| `telegraf` | `instance1` | Metrics collection agent |
| `ubus` | `instance1` | IPC bus daemon |
| `uwsgi` | `instance1` | WSGI application server |
| `victoria-logs` | `instance1` | Log storage |
| `victoria-metrics` | `instance1` | Metrics storage |
| `vmalert` | `instance1` | Alert rules engine |

New services that declare `procd_set_param respawn` in their init script are automatically included without any configuration change.

### Querying Service Metrics

Check all services and their running state:
```bash
curl -s 'http://127.0.0.1:8428/api/v1/query?query=procd_service_running' \
  | jq -r '.data.result[] | "\(.metric.service)/\(.metric.instance) has_respawn=\(.metric.has_respawn) running=\(.value[1])"' \
  | sort
```

Check only persistent services that are currently down:
```bash
curl -s 'http://127.0.0.1:8428/api/v1/query?query=procd_service_running{has_respawn="true"}==0' \
  | jq -r '.data.result[].metric | "\(.service)/\(.instance)"'
```

Check a specific service:
```bash
curl -s 'http://127.0.0.1:8428/api/v1/query?query=procd_service_running{service="nginx"}' | jq .
```

Run the collection script manually to preview its output:
```bash
/usr/libexec/telegraf-services
```

### Service Down Alert (`ServiceDown`)

Defined in `/etc/vmalert/rules/services.yaml`:

| Field | Value |
|-------|-------|
| Condition | `procd_service_running{has_respawn="true"} == 0` |
| For | 2 minutes |
| Severity | `critical` |
| alertgroup | `services` |

The 2-minute window allows procd time to attempt its configured respawn retries before the alert fires.

Check alert status:
```bash
curl -s http://127.0.0.1:8082/api/v1/alerts | jq '.data[] | select(.name=="ServiceDown")'
```

### Manual Testing

See [Testing Service Monitoring](#testing-service-monitoring) below for full test procedures.

## WAN Monitoring

### How It Works

Every 60 seconds, `/usr/libexec/telegraf-mwan` reads `/var/run/mwan3/iface_state/`. mwan3 maintains one file per configured WAN interface in that directory; the file content is the single word `online` or `offline`, updated in real time by mwan3's tracking probes.

```
/var/run/mwan3/iface_state/wan   → "online"
/var/run/mwan3/iface_state/wan2  → "offline"
```

The script emits one record per interface:

```
mwan_interface,interface=wan   online=1i
mwan_interface,interface=wan2  online=0i  ← WAN down
```

In Victoria Metrics the metric is stored as:
```
mwan_interface_online{interface="wan",  db="os-metrics"} = 1
mwan_interface_online{interface="wan2", db="os-metrics"} = 0
```

If mwan3 is not running, the state directory does not exist and the script outputs an empty array — no metrics, no alerts.

### Querying WAN Metrics

```bash
# All WAN interfaces and their current state
curl -s 'http://127.0.0.1:8428/api/v1/query?query=mwan_interface_online' \
  | jq -r '.data.result[] | "\(.metric.interface) status=\(.metric.status) online=\(.value[1])"'

# Interfaces currently offline
curl -s 'http://127.0.0.1:8428/api/v1/query?query=mwan_interface_online==0' \
  | jq -r '.data.result[].metric.interface'

# Run the collection script manually
/usr/libexec/telegraf-mwan
```

### WAN Down Alert (`WanDown`)

Defined in `/etc/vmalert/rules/mwan.yaml`:

| Field | Value |
|-------|-------|
| Condition | `mwan_interface_online == 0` |
| For | 2 minutes |
| Severity | `critical` |
| service | `network` |

The `interface` and `status` labels on the alert come directly from the metric, so each WAN interface fires its own distinct alert.

Check alert status:
```bash
curl -s http://127.0.0.1:8082/api/v1/alerts | jq '.data.alerts[] | select(.name=="WanDown")'
```

### Manual Testing

Simulate a WAN going offline by writing `offline` to its state file (mwan3 will overwrite this when it next evaluates the interface, so the window is short — use `--push` for an immediate metric update):

```bash
# 1. Check baseline — both WANs should be online
curl -s 'http://127.0.0.1:8428/api/v1/query?query=mwan_interface_online' \
  | jq -r '.data.result[] | "\(.metric.interface): \(.value[1])"'

# 2. Simulate wan2 going offline
echo "offline" > /var/run/mwan3/iface_state/wan2

# 3. Push the metric immediately (or wait up to 60s for telegraf)
/usr/libexec/telegraf-mwan --push

# 4. Verify metric dropped to 0
curl -s 'http://127.0.0.1:8428/api/v1/query?query=mwan_interface_online{interface="wan2"}' \
  | jq -r '.data.result[0].value[1]'
# Expected: 0

# 5. After 2 minutes: WANDown alert fires
curl -s http://127.0.0.1:8082/api/v1/alerts \
  | jq '.data.alerts[] | select(.name=="WanDown")'

# 6. Restore
echo "online" > /var/run/mwan3/iface_state/wan2
/usr/libexec/telegraf-mwan --push
```

## Starting and Managing Telegraf

```bash
# Enable at boot and start
/etc/init.d/telegraf enable
/etc/init.d/telegraf start

# Restart (after config changes)
/etc/init.d/telegraf restart

# Check status
/etc/init.d/telegraf status

# View logs
logread | grep telegraf | tail -20
```

## Verifying Metrics in Victoria Metrics

List all metric names being collected:
```bash
curl -s 'http://127.0.0.1:8428/api/v1/label/__name__/values' | jq -r '.data[]' | sort
```

Query a specific metric:
```bash
# CPU usage
curl -s 'http://127.0.0.1:8428/api/v1/query?query=round(100-avg(cpu_usage_idle)/100,0.1)' | jq .

# Memory usage %
curl -s 'http://127.0.0.1:8428/api/v1/query?query=round((mem_used/mem_total)*100,0.1)' | jq .

# All service states
curl -s 'http://127.0.0.1:8428/api/v1/query?query=procd_service_running' | jq .
```

## Testing Service Monitoring

### Quick Manual Test

Stop a service, verify the metric drops to 0, then restore it:

```bash
# 1. Check the baseline — nginx should be running (value=1)
curl -s 'http://127.0.0.1:8428/api/v1/query?query=procd_service_running{service="nginx"}' \
  | jq -r '.data.result[0].value[1]'

# 2. Stop the service
/etc/init.d/nginx stop

# 3. Wait for the next collection interval (up to 60s), then re-query
sleep 65
curl -s 'http://127.0.0.1:8428/api/v1/query?query=procd_service_running{service="nginx"}' \
  | jq -r '.data.result[0].value[1]'
# Expected output: 0

# 4. Check vmalert — after 2 minutes the alert will be in "pending" then "firing"
curl -s http://127.0.0.1:8082/api/v1/alerts \
  | jq '.data[] | select(.name=="ServiceDown") | {name,state,labels}'

# 5. Restore the service
/etc/init.d/nginx start

# 6. Verify recovery — metric returns to 1
sleep 65
curl -s 'http://127.0.0.1:8428/api/v1/query?query=procd_service_running{service="nginx"}' \
  | jq -r '.data.result[0].value[1]'
# Expected output: 1
```

### Using the Test Script

The repository includes a simulation script for automated testing:

```bash
# Stop nginx, observe metric drop and alert, then recover (default service: nginx)
scripts/test-service-monitor.sh

# Test a different service
scripts/test-service-monitor.sh dropbear

# Run in observe-only mode (no service restart)
scripts/test-service-monitor.sh nginx --no-recover
```

### Simulating a Crash (respawn exhaustion)

To simulate a service crash and exhaust procd's respawn retries:

```bash
# Get the PID of a running service
PID=$(ubus call service list '{"name":"nginx"}' | jq -r '.nginx.instances.instance1.pid')

# Kill it repeatedly to exhaust respawn retries (default: 5 retries in 3600s)
for i in $(seq 1 6); do
  kill -9 $PID 2>/dev/null
  sleep 2
  PID=$(ubus call service list '{"name":"nginx"}' | jq -r '.nginx.instances.instance1.pid // 0')
  echo "Attempt $i: pid=$PID"
done

# After retries are exhausted, procd marks the service as stopped
ubus call service list '{"name":"nginx"}' | jq '.nginx.instances.instance1.running'
# Expected: false
```

> **Note**: After exhausting respawn retries, restart with `/etc/init.d/nginx start`.

## Troubleshooting

### Script returns no output

```bash
# Test ubus access
ubus call service list | head -5

# Run script manually with verbose output
python3 /usr/libexec/telegraf-services

# Check Telegraf is ingesting the exec output
logread | grep 'telegraf' | grep -i 'exec\|error' | tail -20
```

### Metrics not appearing in Victoria Metrics

```bash
# Confirm Telegraf is sending data
curl -s 'http://127.0.0.1:8428/api/v1/label/__name__/values' | jq -r '.data[]' | grep procd

# Check Telegraf configuration is valid
telegraf --config /etc/telegraf.conf --config-directory /etc/telegraf.conf.d --test 2>&1 | head -30

# Verify output plugin connectivity
curl -s http://127.0.0.1:8428/metrics | grep vm_rows_total | head -5
```

### ServiceDown alert not firing

```bash
# Confirm the rule is loaded
curl -s http://127.0.0.1:8082/api/v1/rules \
  | jq '.data.groups[] | select(.name=="services") | .rules[] | {name, state, expr}'

# Check if any services are in pending/firing state
curl -s http://127.0.0.1:8082/api/v1/alerts | jq '.data'

# Manually evaluate the alert expression against Victoria Metrics
curl -s 'http://127.0.0.1:8428/api/v1/query?query=procd_service_running{has_respawn="true"}==0' | jq .
```

### WANDown alert not firing

```bash
# Confirm the rule is loaded
curl -s http://127.0.0.1:8082/api/v1/rules \
  | jq '.data.groups[] | select(.name=="mwan") | .rules[] | {name, state, expr}'

# Check if any WANs are in pending/firing state
curl -s http://127.0.0.1:8082/api/v1/alerts | jq '.data.alerts[] | select(.name=="WANDown")'

# Manually evaluate the alert expression
curl -s 'http://127.0.0.1:8428/api/v1/query?query=mwan_interface_online==0' | jq .

# Check mwan3 state files directly
ls -la /var/run/mwan3/iface_state/ && cat /var/run/mwan3/iface_state/*
```

### ethtool errors in logs

Bridge interfaces don't support ethtool stats. Add `br*` to the exclude list in `/etc/telegraf.conf.d/os.conf`:
```ini
[[inputs.ethtool]]
  interface_exclude = ["wg*", "ipsec*", "tun*", "br*"]
```

## References

- [Telegraf documentation](https://docs.influxdata.com/telegraf/)
- [Telegraf inputs.exec plugin](https://github.com/influxdata/telegraf/tree/master/plugins/inputs/exec)
- [OpenWrt procd init scripts](https://openwrt.org/docs/guide-developer/procd-init-scripts)
- [OpenWrt ubus reference](https://openwrt.org/docs/techref/ubus)
- [Victoria Metrics vmalert](https://docs.victoriametrics.com/vmalert/)
