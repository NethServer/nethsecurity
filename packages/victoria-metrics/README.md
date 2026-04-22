# Victoria Metrics

## Overview

This package includes **Victoria Metrics** with **vmalert** for time series data collection and alerting in NethSecurity. Victoria Metrics is a fast, cost-effective, and scalable time-series database that serves as the metrics storage backend for the system. vmalert provides alerting capabilities by evaluating rules against the collected metrics.

**Key Components:**
- **victoria-metrics**: Time-series database server listening on port 8428
- **vmalert**: Alert rule evaluator with HTTP API on port 8081
- **Telegraf integration**: Automatic metric collection from system resources
- **Mimir integration**: Alerts can be forwarded to Mimir for centralized alerting

## Installation & Setup

### Package Contents

The victoria-metrics package includes:
- `victoria-metrics` binary: Time-series database
- `vmalert` binary: Alert rule evaluator
- Init scripts for service management
- UCI configuration files
- Pre-configured alert rules for host monitoring

### Initial Configuration

#### Victoria Metrics Storage

Configuration is located at `/etc/config/victoria-metrics`:

```
config victoriametrics 'main'
    option storage_path '/var/lib/victoriametrics'
    option retention_period '1y'
```

**Key options:**
- `storage_path`: Directory for metric data storage (default: `/var/lib/victoriametrics`)
- `retention_period`: How long to keep metrics (default: `1y`). Use formats like `1d`, `7d`, `30d`, `365d`, `1y`

#### vmalert Configuration

Configuration is located at `/etc/config/vmalert`:

```
config vmalert
    option datasource_url 'http://localhost:8428'
    option http_listen_addr '127.0.0.1:8081'
```

**Key options:**
- `datasource_url`: URL to Victoria Metrics (default: `http://localhost:8428`)
- `http_listen_addr`: HTTP address for vmalert API (default: `127.0.0.1:8081`)

## Service Management

### Starting Services

Enable and start Victoria Metrics:
```bash
/etc/init.d/victoria-metrics enable
/etc/init.d/victoria-metrics start
```

Enable and start vmalert:
```bash
/etc/init.d/vmalert enable
/etc/init.d/vmalert start
```

### Checking Status

```bash
/etc/init.d/victoria-metrics status
/etc/init.d/vmalert status
```

### Monitoring

Victoria Metrics provides several endpoints for metrics and monitoring:

**Query interface:**
```bash
# Query metrics using MetricsQL
curl 'http://127.0.0.1:8428/api/v1/query?query=cpu_usage_idle'

# Query range of data
curl 'http://127.0.0.1:8428/api/v1/query_range?query=cpu_usage_idle&start=1609459200&end=1609545600&step=300'
```

**Available metrics:**
```bash
# List all metric names
curl -s 'http://127.0.0.1:8428/api/v1/label/__name__/values' | jq -r '.data[]' | sort
```

## vmalert: Alert Rule Evaluation

### Overview

vmalert evaluates alerting rules periodically and generates alerts when conditions are met. Rules are defined in YAML format following the Prometheus alerting rules specification.

### Alert Rules Configuration

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

### Metric Names Mapping

NethSecurity uses **Telegraf** to collect metrics and send them to Victoria Metrics. Telegraf metric names differ from standard Prometheus names:

| Category | Telegraf Metric | Description |
|----------|-----------------|-------------|
| CPU | `cpu_usage_idle`, `cpu_usage_user`, etc. | CPU usage by category |
| Memory | `mem_used`, `mem_total`, `mem_free`, `mem_swap_*` | Memory and swap usage |
| Disk | `disk_used`, `disk_total`, `disk_free`, `disk_inodes_*` | Disk space and inodes |
| Network | `net_bytes_sent`, `net_bytes_recv`, `net_err_in`, `net_drop_out` | Network interface stats |
| Process | `processes_running`, `processes_zombies`, `processes_blocked` | Process states |
| System | `system_load1`, `system_load5`, `system_load15`, `system_uptime` | System metrics |

#### Discovering Available Metrics

To see all available metrics in Victoria Metrics:
```bash
curl -s 'http://127.0.0.1:8428/api/v1/label/__name__/values' | jq -r '.data[]' | sort
```

### vmalert HTTP API

The vmalert HTTP API is available at `http://127.0.0.1:8081`:

#### View all alerts
```bash
curl http://127.0.0.1:8081/api/v1/alerts
```

#### View all rules
```bash
curl http://127.0.0.1:8081/api/v1/rules
```

#### Check specific rule status
```bash
curl 'http://127.0.0.1:8081/api/v1/rules?type=alert' | jq '.data.groups[0].rules[] | select(.name == "DiskSpaceWarning")'
```

#### View rule group
```bash
curl 'http://127.0.0.1:8081/api/v1/rules?type=alert' | jq '.data.groups[] | select(.name == "host_and_hardware")'
```

### Included Alert Rules

The default rules monitor critical host and hardware metrics. Rules are organized into categories:

#### 1. CPU Usage
- **HighCpuUsage**: CPU > 70% for 5 minutes (warning)
- **CriticalCpuUsage**: CPU > 85% for 2 minutes (critical)

#### 2. Memory Usage
- **HighMemoryUsage**: RAM > 80% (warning)
- **CriticalMemoryUsage**: RAM > 90% (critical)
- **HighSwapUsage**: Swap > 50% (warning)

#### 3. Disk Space
- **DiskSpaceWarning**: Usage > 80% (warning)
- **DiskSpaceCritical**: Usage > 90% (critical)
- **DiskInodesWarning**: Inodes > 80% (warning)
- **DiskInodesCritical**: Inodes > 90% (critical)

#### 4. System Load
- **HighSystemLoad**: Load > 2x CPU count (warning)

#### 5. Network
- **HighNetworkErrorsIn/Out**: Errors > 100 in 5 minutes (warning)
- **HighNetworkDropsIn/Out**: Drops > 100 in 5 minutes (warning)

#### 6. Processes
- **ProcessesZombiesAlert**: Zombie processes > 5 (warning)
- **ProcessesBlockedAlert**: Blocked processes > 10 (warning)

### Alert State Lifecycle

Alerts follow this state progression:

1. **Pending**: Condition is true but hasn't met the `for` duration threshold yet
2. **Firing**: Condition has been true for at least the `for` duration
3. **Resolved**: Condition is no longer true

Example: An alert with `for: 5m` will:
- Start in "pending" state when the condition first becomes true
- Transition to "firing" state after 5 minutes of the condition remaining true
- Return to "inactive" state when the condition becomes false

### Testing Alerts

To test if alerts are being evaluated properly:

1. Check rule evaluation status:
   ```bash
   curl 'http://127.0.0.1:8081/api/v1/rules?type=alert' | jq '.data.groups[0].rules[] | {name,state,lastEvaluation}'
   ```

2. Query the metric that triggers an alert:
   ```bash
   curl 'http://127.0.0.1:8428/api/v1/query?query=disk_used_percent'
   ```

3. Monitor vmalert logs:
   ```bash
   tail -f /var/log/messages | grep vmalert
   ```

4. Trigger an alert manually (for testing):
   ```bash
   # Stress CPU to trigger HighCpuUsage alert (needs CPU > 70% for 5 min)
   dd if=/dev/zero of=/dev/null &
   ```

## Integration with Mimir (ns-plug)

When Mimir alerting is configured via ns-plug, vmalert automatically detects the configuration and forwards alerts to Mimir. This is fully automatic and requires no manual configuration of vmalert.

### Automatic Mimir Detection

vmalert checks for the following ns-plug UCI configuration on startup:
```
ns-plug.config.my_url           # Mimir base URL
ns-plug.config.my_system_key    # HTTP Basic Auth username
ns-plug.config.my_system_secret # HTTP Basic Auth password
```

If all three values are present, vmalert automatically:
1. Constructs the Mimir alertmanager endpoint URL
2. Configures HTTP basic authentication
3. Starts forwarding alerts to Mimir

### Enabling Mimir Integration

1. **Configure ns-plug with Mimir credentials:**
   ```bash
   uci set ns-plug.config.my_url='https://mimir.example.com'
   uci set ns-plug.config.my_system_key='your_api_key'
   uci set ns-plug.config.my_system_secret='your_api_secret'
   uci commit ns-plug
   ```

2. **Restart vmalert to apply the configuration:**
   ```bash
   /etc/init.d/vmalert restart
   ```

3. **Verify alerts are being forwarded:**
   ```bash
   # Check vmalert logs for successful forwarding
   tail -f /var/log/messages | grep vmalert
   
   # Query vmalert to confirm rules are evaluating
   curl http://127.0.0.1:8081/api/v1/rules | jq '.data.groups[0].rules[0].alerts'
   ```

### Alert Flow to Mimir

When Mimir is configured:
```
Telegraf metrics
    ↓
Victoria Metrics (database)
    ↓
vmalert (rules evaluation every 30s)
    ↓
Mimir Alertmanager (if configured)
    ↓
Mimir UI / Alert routing / Integrations
```

The vmalert init script automatically handles the detection and forwarding without requiring manual intervention.

### Fallback: Blackhole Mode

If ns-plug is not configured with Mimir credentials:
- vmalert runs in **blackhole mode** (default)
- Alerts are evaluated correctly
- Alerts do NOT get forwarded anywhere
- This is useful for local testing and validation

To switch back to blackhole mode, simply clear the ns-plug configuration:
```bash
uci delete ns-plug.config.my_url
uci delete ns-plug.config.my_system_key
uci delete ns-plug.config.my_system_secret
uci commit ns-plug
/etc/init.d/vmalert restart
```

## Troubleshooting

### Victoria Metrics Issues

#### Database won't start

Check init script logs:
```bash
tail -f /var/log/messages | grep victoria-metrics
```

Verify storage path exists and is writable:
```bash
ls -la /var/lib/victoriametrics/
```

#### High disk usage

Consider reducing retention period in `/etc/config/victoria-metrics`:
```
option retention_period '30d'  # Instead of 1y
```

### Telegraf Integration Issues

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

### vmalert Issues

#### unsupported path "/stats" errors

**Issue**: vmalert logs repeated errors like:
```
vmalert: error: unsupported path requested: "/stats"
```

**Root Cause**: The netifyd daemon is configured to collect network statistics from vmalert's HTTP server, but vmalert only exposes `/api/v1/*` endpoints.

**Solution**: Configure netifyd to exclude vmalert's port (8081) from statistics collection. Edit `/etc/config/netifyd` and add a BPF filter:
```uci
config netifyd
    list internal_if 'br-lan -F "not (tcp and port 8081)"'
```

Then restart netifyd:
```bash
/etc/init.d/netifyd restart
```

#### No alerts firing

Check that vmalert service is running:
```bash
/etc/init.d/vmalert status
```

Verify datasource connection:
```bash
curl -I http://localhost:8428/api/v1/query
```

Check rule syntax in `/etc/vmalert/rules/*.yaml` (YAML must be valid)

#### Alerts always "pending"

This is normal if the condition hasn't been true for the required duration. For example:
- An alert with `for: 5m` takes 5 minutes to transition from "pending" to "firing"
- Check the `lastEvaluation` timestamp in the API response to see when it was last evaluated

### Performance Considerations

#### Memory Usage

Victoria Metrics can use significant memory. Monitor with:
```bash
free -h
ps aux | grep victoria-metrics
```

Adjust `-maxBytes` in the init script if needed to limit memory usage.

#### Storage Considerations

Default retention is 1 year. Monitor disk usage:
```bash
df -h /var/lib/victoriametrics/
du -sh /var/lib/victoriametrics/
```

Reduce retention if disk space is limited by modifying `/etc/config/victoria-metrics`.

#### Alert Evaluation

vmalert evaluates rules every 30 seconds. If you have many rules or complex queries, evaluation time may increase. Monitor with:
```bash
curl 'http://127.0.0.1:8081/api/v1/rules' | jq '.data.groups[0].rules[].evaluationTime'
```

## Advanced Configuration

### Custom Alert Rules

To add custom alert rules, create a new YAML file in `/etc/vmalert/rules/` following this format:

```yaml
groups:
  - name: "custom_alerts"
    interval: "30s"
    rules:
      - alert: CustomAlert
        expr: 'your_metric > threshold'
        for: "5m"
        labels:
          severity: "warning"
          service: "custom"
        annotations:
          summary_en: "Alert summary"
          summary_it: "Riepilogo avviso"
          description_en: "Alert description with {{ $value }}"
          description_it: "Descrizione avviso con {{ $value }}"
```

After adding rules, restart vmalert:
```bash
/etc/init.d/vmalert restart
```

### MetricsQL vs PromQL

Victoria Metrics uses **MetricsQL**, which is compatible with PromQL but includes additional features. See [MetricsQL documentation](https://docs.victoriametrics.com/metricsql/) for advanced query syntax.

Common MetricsQL functions:
- `rate()`: Rate of increase per second
- `increase()`: Absolute increase over time range
- `avg()`: Average value
- `sum()`: Sum of all values
- `max()`, `min()`: Maximum/minimum values
- `group_by()`: Group metrics by label

## References

- **Victoria Metrics Documentation**: https://docs.victoriametrics.com/
- **Victoria Metrics vmalert**: https://docs.victoriametrics.com/vmalert/
- **MetricsQL Documentation**: https://docs.victoriametrics.com/metricsql/
- **Prometheus Alert Rules**: https://samber.github.io/awesome-prometheus-alerts/
- **Host Monitoring Rules**: https://samber.github.io/awesome-prometheus-alerts/rules/basic-resource-monitoring/host-and-hardware/
- **Telegraf Documentation**: https://docs.influxdata.com/telegraf/

## License

Apache License 2.0 - See LICENSE file for details
