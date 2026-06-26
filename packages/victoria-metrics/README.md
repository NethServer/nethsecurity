# Victoria Metrics

## Overview

This package provides **Victoria Metrics** and **vmalert** for time-series metrics storage and alerting in NethSecurity. Metrics are collected by Telegraf, stored in Victoria Metrics, and evaluated by vmalert according to alert rules.

**Key Components:**
- **victoria-metrics**: Time-series database on port 8428
- **vmalert**: Alert rule evaluator on port 8081
- **Telegraf integration**: Host metrics, service health, WAN status, storage status
- **Mimir integration**: Optional centralized alerting (via ns-plug)

## Quick Start

### View Active Alerts

```bash
# List all firing and pending alerts
curl http://127.0.0.1:8082/api/v1/alerts | jq

# Get a specific alert status
curl 'http://127.0.0.1:8082/api/v1/rules?type=alert' | \
  jq '.data.groups[].rules[] | select(.name == "HighCpuUsage") | {name, state, lastEvaluation}'
```

### List Available Metrics

```bash
# All metrics currently being stored
curl -s 'http://127.0.0.1:8428/api/v1/label/__name__/values' | jq -r '.data[]' | sort
```

## Configuration

Configuration is located at `/etc/config/victoria-metrics`:

```
config victoriametrics 'main'
    option http_listen_addr '127.0.0.1:8428'
```

**Required options:**
- `http_listen_addr`: Address and port for the HTTP server

**Optional options:**
- `storage_path`: Where to store metrics data (default: `/var/lib/victoriametrics`, auto-detects `/mnt/data/victoriametrics` if available)
- `retention_period`: How long to keep metrics (`1d`, `7d`, `30d`, `1y`, etc.) (default: `7d`, auto-detects `1y` if not set)

### Accessing the Web UI

By default the server is accessible only on localhost for security.
The service also exposes a Web UI on port 8428 for browsing metrics and testing queries.

To access the Web UI, you can change the `http_listen_addr` to `0.0.0.0:8428` to allow external access, but this is not recommended for production environments without proper security measures.
A safer approach is to use SSH port forwarding:
```bash
ssh -L 8428:127.0.0.1:8428 root@remote_host
```

Then open `http://127.0.0.1:8428` in your web browser to see all exposed endpoints.
The UI to query metrics is available at `http://127.0.0.1:8428/vmui`.

## Alerting Rules

All alert rules are defined as YAML files in `/etc/vmalert/rules/*.yaml`. Each file corresponds to a specific monitoring category.

Some alerts implement a two-tier severity model with `warning` and `critical` levels and are designed to suppress lower-severity alerts when higher-severity ones are firing.

Warning alerts use `unless` clauses to suppress them when their critical counterpart is already firing, reducing noise. For example, `HighCpuUsage` warning is silenced when `CriticalCpuUsage` is firing.

See rule files for specific thresholds and suppression logic.

An alert can be in one of three states:

1. **Pending**: Condition is true but hasn't met the required `for` duration
2. **Firing**: Condition has been true for at least the `for` duration
3. **Resolved**: Condition is no longer true

Example: An alert with `for: 5m` takes 5 minutes to transition from pending → firing.

### Custom Alert Rules

To add custom alerts, create a new YAML file in `/etc/vmalert/rules/`.
Example `custom.yaml`:

```yaml
groups:
  - name: "my_alerts"
    interval: "5m"
    rules:
      - alert: MyAlert
        expr: 'metric_name > threshold'
        for: "5m"
        labels:
          severity: "warning"
          service: "my_service"
        annotations:
          summary_en: "Alert summary"
          summary_it: "Riepilogo avviso"
          description_en: "Value is {{ $value }}"
```

Then restart vmalert:
```bash
/etc/init.d/vmalert restart
```

Make sure to store the alert inside the backup:
```
echo /etc/vmalert/rules/custom.yaml >> /etc/sysupgrade.conf
```

Here is the complete Markdown documentation explaining this specific alerting logic. You can drop this directly into your repository's `README.md`.

### Rule evaluation logic

Most alerts are configured with a 5-minute evaluation interval and a 5-minute alert duration (`for`).
This means that an alert must be continuously true for at least 5 minutes before it transitions from `Pending` to `Firing`.

Example:
```yaml
groups:
  - name: "host_and_hardware"
    interval: "5m"  # How often the engine checks the metrics
    rules:
      - alert: CriticalCpuUsage
        expr: 'round(100 - avg by(host) (cpu_usage_idle), 0.1) > 85'
        for: "5m"   # How long the threshold must be breached to fire
```

Because the rule engine evaluations happen at discrete 5-minute ticks, an alert **requires two consecutive failed checks** to transition from a normal state to an active notification.

The engine processes an active incident through three phases:

1. **Clear State:** Metrics are healthy; no alerts are tracked.
2. **Pending State:** The first evaluation tick catches a threshold breach. The engine records the timestamp and marks the alert as `Pending`.
3. **Firing State:** At the next evaluation tick (exactly 5 minutes later), if the threshold is still breached, the engine verifies that > 5
   minutes have passed since it entered `Pending`. The alert transitions to `Firing` and routes to notifications.

Because real-world server incidents do not align perfectly with the monitoring engine's internal execution clock, notifications feature a variable delay window of 5 to 10 minutes from the actual start of the incident.

## Forwarding alerts to my.nethesis.it

[my](https://github.com/NethServer/my/) uses Grafana Mimir as a multi-tenant
alertmanager for cloud-side alert processing. Enterprise systems forward their
alerts to it automatically, mirroring `send-heartbeat` / `send-inventory`:
vmalert POSTs alerts to the credential-translation proxy at
`https://my.nethesis.it/proxy/alerts` using the ns-plug credentials
(`system_id` / `secret`), which the proxy maps to the new my credentials before
forwarding them to the Mimir alertmanager. No manual configuration is needed —
it is enabled whenever `ns-plug.config.type` is `enterprise` and the system is
registered (`system_id` / `secret` set). vmalert always also notifies the local
ns-plug-alert-proxy (`http://127.0.0.1:9095`), which handles the legacy path and
unregistered machines.

By default, ns-plug-alert proxy logs only when an alert can't be forwarded to legacy my.nethesis.it.
To increase verbosity and debug all communications with the portal,
set `ns-plug.config.alert_proxy_loglevel` to `info` or `debug` and restart ns-plug-alert-proxy:
```bash
uci set ns-plug.config.alert_proxy_loglevel='debug'
uci commit ns-plug
/etc/init.d/ns-plug-alert-proxy restart
```

> Migration note: the my switch-off release will repoint this from
> `/proxy/alerts` to the native collect endpoint
> (`/collect/api/services/mimir/alertmanager`) with rotated credentials.

## Alert notifications

System alerts are handled by vmalert (Victoria Metrics alert evaluation engine) which evaluates
alert rules against metrics collected by telegraf.

When a rule transitions from `Pending` to `Firing`, vmalert sends an Alertmanager notification to the following endponts:
- ns-plug-alert-proxy, listening on port 9095, which forwards only some alerts to the legacy monitoring portal
- https://my.nethesis.it/proxy/alerts, wich forwards all alerts to the new Mimir alertmanager

vmalert sends a notification for firing alerts every `interval`, set to 5 minutes for most alerts, until the alert resolves.
When the alert resolves, vmalert sends 4 notifications at 5-minute intervals to ensure the resolution is received by the alertmanager (or the proxy) even if the first notification is lost.

**Migration note**

When legacy my.nethesis.it will be replaced with the new one:
- remove ns-plug-alert-proxy from the system (caveat: also my.nethserver.com will not receive alerts anymore)
- change vmalert configuration to send alerts directly to the new Mimir alertmanager endpoint: replace `/proxy/alerts`
  with the native collect endpoint `/collect/api/services/mimir/alertmanager` with rotated credentials.

### ns-plug-alert-proxy

The proxy forwards only the following legacy alerts:
| Alert | Condition | Legacy alert_id |
|---|---|---|
| `WanDown` | WAN interface offline for 2m | `wan:<interface>:down` |
| `DiskSpaceCritical` | Disk usage > 90% for 2m | `df:root:percent_bytes:free` or `df:boot:percent_bytes:free` |
| `StorageStatus` | Storage status is error | `storage:status` |
| `HaPrimaryFailed` | Backup node became master | `ha:primary:failed` |
| `HaSyncFailed` | HA sync failure detected on the primary node | `ha:sync:failed` |

All other alert are silently dropped by the proxy.
If the machine does not have a subscription, all alerts are silently dropped.

The proxy starts automatically at boot regardless of registration state.
By default, firing/resolved state is determined from the Alertmanager-standard `endsAt` field:
if `endsAt` is in the future (or zero/missing) a **FAILURE** is sent; if `endsAt` is in
the past an **OK** is sent. HA recovery/failover event alerts override this default mapping so
they can keep the legacy `ha:primary:failed` semantics.

## Alert history

The `vmalert` alerts keeps the state of all active alerts inside VictoriaMetrics using the remote-write protocol.
In case of vmalert restart, the alert state is restored from VictoriaMetrics and the alert evaluation continues without losing any information.

The state is stored using two specific time series:
* `ALERTS`
* `ALERTS_FOR_STATE`

Because these are standard time series, they can be queried from VictoriaMetrics just like any other metric and used
to retrieve the history of alerts and their state transitions.

Query examples with curl, retrieve alerts from the last 24 hours:
```
curl 'http://localhost:8428/prometheus/api/v1/query_range' --data-raw "query=ALERTS_FOR_STATE&start=$(( $(date +%s) - 86400 ))&end=$(date +%s)&step=30s" | jq
curl 'http://localhost:8428/prometheus/api/v1/query_range' --data-raw "query=ALERTS&start=$(( $(date +%s) - 86400 ))&end=$(date +%s)&step=30s" | jq
```

## References

- [Victoria Metrics vmalert docs](https://docs.victoriametrics.com/vmalert/)
- [MetricsQL documentation](https://docs.victoriametrics.com/metricsql/)
- [Prometheus alerting rules](https://samber.github.io/awesome-prometheus-alerts/)
- [vmalert documentation](https://docs.victoriametrics.com/vmalert/)
- [Telegraf metrics collection](../telegraf/README.md)
