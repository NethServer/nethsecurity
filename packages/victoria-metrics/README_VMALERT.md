# Victoria Metrics Alerting with vmalert

## Overview

This package includes **vmalert** for generating alerts based on metrics collected by Victoria Metrics. vmalert evaluates alerting rules periodically and can send notifications to Alertmanager or other webhook receivers.

## Configuration

### vmalert Configuration File

The main configuration is located at:
```
/etc/config/vmalert
```

Key parameters:
- `datasource_url`: URL to Victoria Metrics (default: `http://localhost:8428`)
- `http_listen_addr`: HTTP address for vmalert API (default: `127.0.0.1:8081`)

### Alert Rules

Alert rules are stored as YAML files in:
```
/etc/vmalert/rules/
```

Rules follow the Prometheus alerting rules format. Each rule defines:
- Alert name
- PromQL/MetricsQL expression
- Duration threshold (how long the condition must be true)
- Labels (severity, service, etc.)
- Annotations (summary, description in multiple languages)

## Metric Names Mapping

NethSecurity uses **Telegraf** to collect metrics and send them to Victoria Metrics. Telegraf metric names differ from standard Prometheus names:

| Category | Telegraf Metric | Description |
|----------|-----------------|-------------|
| CPU | `cpu_usage_idle`, `cpu_usage_user`, etc. | CPU usage by category |
| Memory | `mem_used`, `mem_total`, `mem_free`, `mem_swap_*` | Memory and swap usage |
| Disk | `disk_used`, `disk_total`, `disk_free`, `disk_inodes_*` | Disk space and inodes |
| Network | `net_bytes_sent`, `net_bytes_recv`, `net_err_in`, `net_drop_out` | Network interface stats |
| Process | `processes_running`, `processes_zombies`, `processes_blocked` | Process states |
| System | `system_load1`, `system_load5`, `system_load15`, `system_uptime` | System metrics |

### Discovering Available Metrics

To see all available metrics in Victoria Metrics:
```bash
curl -s 'http://127.0.0.1:8428/api/v1/label/__name__/values' | jq -r '.data[]' | sort
```

## Starting vmalert

Enable and start the vmalert service:
```bash
/etc/init.d/vmalert enable
/etc/init.d/vmalert start
```

Check status:
```bash
/etc/init.d/vmalert status
```

## Monitoring vmalert

The vmalert HTTP API is available at `http://127.0.0.1:8081`:

### View all alerts
```bash
curl http://127.0.0.1:8081/api/v1/alerts
```

### View all rules
```bash
curl http://127.0.0.1:8081/api/v1/rules
```

### Check specific rule status
```bash
curl 'http://127.0.0.1:8081/api/v1/rules?type=alert' | jq '.data.groups[0].rules[] | select(.name == "DiskSpaceWarning")'
```

## Alert Rules

### Included Rules (host.yaml)

The default rules monitor:

1. **CPU Usage**
   - HighCpuUsage: CPU > 70% for 5 minutes (warning) — suppressed when CriticalCpuUsage fires
   - CriticalCpuUsage: CPU > 85% for 2 minutes (critical)

2. **Memory Usage**
   - HighMemoryUsage: RAM > 80% (warning) — suppressed when CriticalMemoryUsage fires
   - CriticalMemoryUsage: RAM > 90% (critical)
   - HighSwapUsage: Swap > 50% (warning)

3. **Disk Space**
   - DiskSpaceWarning: Usage > 80% (warning) — suppressed when DiskSpaceCritical fires
   - DiskSpaceCritical: Usage > 90% (critical)
   - DiskInodesWarning: Inodes > 80% (warning) — suppressed when DiskInodesCritical fires
   - DiskInodesCritical: Inodes > 90% (critical)

4. **System Load**
   - HighSystemLoad: Load > 2x CPU count (warning)

5. **Network**
   - HighNetworkErrorsIn/Out: Errors > 100 in 5 minutes (warning)
   - HighNetworkDropsIn/Out: Drops > 100 in 5 minutes (warning)

6. **Processes**
   - ProcessesZombiesAlert: Zombie processes > 5 (warning)
   - ProcessesBlockedAlert: Blocked processes > 10 (warning)

> **Alert suppression**: Warning alerts use `unless` clauses so they are automatically silenced when their corresponding critical alert is already firing, reducing notification noise.

### Included Rules (services.yaml)

Service health monitoring via procd/ubus:

7. **Service Status**
   - ServiceDown: A persistent procd service (with respawn configured) has been down for more than 2 minutes (critical)

See the [Telegraf README](../telegraf/README.md) for the full list of monitored services and query examples.

## Integration with ns-plug (Mimir)

When Mimir alerting is configured via ns-plug, vmalert **automatically** detects the configuration and forwards alerts to Mimir. No manual configuration of vmalert is required.

### Automatic Configuration

vmalert checks for these ns-plug UCI configuration values on startup:
- `ns-plug.config.my_url` - Mimir base URL
- `ns-plug.config.my_system_key` - API key (HTTP Basic Auth username)
- `ns-plug.config.my_system_secret` - API secret (HTTP Basic Auth password)

If all three are present, vmalert automatically configures alert forwarding to Mimir.

### Enabling Mimir Integration

1. Configure ns-plug:
```bash
uci set ns-plug.config.my_url='https://mimir.example.com'
uci set ns-plug.config.my_system_key='your_api_key'
uci set ns-plug.config.my_system_secret='your_api_secret'
uci commit ns-plug
```

2. Restart vmalert:
```bash
/etc/init.d/vmalert restart
```

3. Verify forwarding is working:
```bash
tail -f /var/log/messages | grep vmalert
```

### Alert Forwarding Details

When Mimir is configured, vmalert:
- Sends fired alerts to Mimir's alertmanager API endpoint
- Uses HTTP basic authentication with the provided credentials
- Continues to evaluate rules every 30 seconds
- Automatically handles alert state transitions (firing → resolved)

### Blackhole Mode (Default)

If ns-plug Mimir credentials are not configured:
- vmalert runs in blackhole mode
- Alerts are evaluated but not forwarded anywhere
- Useful for local testing and validation

To revert to blackhole mode:
```bash
uci delete ns-plug.config.my_url
uci delete ns-plug.config.my_system_key
uci delete ns-plug.config.my_system_secret
uci commit ns-plug
/etc/init.d/vmalert restart
```

## Testing Alerts

To test if alerts are being evaluated, you can:

1. Check rule evaluation status:
   ```bash
   curl 'http://127.0.0.1:8081/api/v1/rules?type=alert' | jq '.data.groups[0].rules[] | .{name,state,lastEvaluation}'
   ```

2. Query the metric that triggers an alert:
   ```bash
   curl 'http://127.0.0.1:8428/api/v1/query?query=disk_used_percent'
   ```

3. Monitor vmalert logs:
   ```bash
   tail -f /var/log/messages | grep vmalert
   ```

## References

- **Victoria Metrics vmalert documentation**: https://docs.victoriametrics.com/vmalert/
- **Prometheus alert rules**: https://samber.github.io/awesome-prometheus-alerts/
- **Host and hardware monitoring rules**: https://samber.github.io/awesome-prometheus-alerts/rules/basic-resource-monitoring/host-and-hardware/

## Troubleshooting

### Telegraf Errors in Logs

#### ethtool errors: "operation not supported"

**Issue**: Telegraf reports repeated errors like:
```
telegraf: error: [inputs.ethtool] "br-lan" stats: operation not supported
```

**Root Cause**: Bridge interfaces (e.g., `br-lan`) don't support ethtool statistics collection.

**Solution**: Add bridge interface pattern to ethtool's interface exclusion list in `/etc/telegraf.conf.d/os.conf`:
```ini
[[inputs.ethtool]]
  interface_exclude = ["wg*", "ipsec*", "tun*", "br*"]
```

#### sensors errors: "failed to run command"

**Issue**: Telegraf reports repeated errors like:
```
telegraf: error: [inputs.sensors] failed to run command "/usr/sbin/sensors -A -u": exit status 1
```

**Root Cause**: The `lm-sensors` package or `/usr/sbin/sensors` utility is not available on the system.

**Solution**: Disable the sensors input plugin by commenting it out in `/etc/telegraf.conf.d/os.conf`:
```ini
# [[inputs.sensors]]
#   # Configuration disabled - sensors utility not available
```

### vmalert Errors in Logs

#### unsupported path "/stats"

**Issue**: vmalert logs repeated errors like:
```
vmalert: error: unsupported path requested: "/stats"
```

**Root Cause**: The netifyd daemon is configured to collect network statistics from vmalert's HTTP server, but vmalert only exposes `/api/v1/*` endpoints and doesn't provide a `/stats` endpoint.

**Solution**: Configure netifyd to exclude vmalert's port (8081) from statistics collection. Edit `/etc/config/netifyd` and add a BPF filter to the internal interface configuration:
```uci
config netifyd
    list internal_if 'br-lan -F "not (tcp and port 8081)"'
```

Then restart netifyd:
```bash
/etc/init.d/netifyd restart
```

**Note**: These are non-critical errors that don't affect functionality. Metrics are still collected, alerts are still evaluated, and all services operate normally. The errors only increase log verbosity.
