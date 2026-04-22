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
    option storage_path '/var/lib/victoriametrics'
    option retention_period '1y'
    option http_listen_addr '127.0.0.1:8428'
```

**Options:**
- `storage_path`: Where to store metrics data
- `retention_period`: How long to keep metrics (`1d`, `7d`, `30d`, `1y`, etc.)
- `http_listen_addr`: Address and port for the HTTP server

### Accessing the Web UI

By default the server is accessible only on localhost for security.
The service also exposes a Web UI on port 8428 for browsing metrics and testing queries.

To access the Web UI, you can change the `http_listen_addr` to `0.0.0.0:8428` to allow external access, but this is not recommended for production environments without proper security measures.
A safer approach is to use SSH port forwarding:
```bash
ssh -L 8428:127.0.0.1:8428 root@remote_host
```

Then open `http://127.0.0.1:8428` in your web browser to see all exposed endpoints.
The UI to query metrics is available at `http://127.0.0.1:8428/vmui

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
Example `my_alerts.yaml`:

```yaml
groups:
  - name: "my_alerts"
    interval: "30s"
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

## Mimir Integration (ns-plug)

Mimir is a multi-tenant Prometheus-compatible long-term storage and alerting system used by nextgen [my](https://github.com/NethServer/my/) monitoring
platform.
When Mimir is configured via ns-plug, vmalert automatically forwards alerts. No manual vmalert configuration needed.

**Enable Mimir forwarding:**
```bash
uci set ns-plug.config.my_url='https://mimir.example.com'
uci set ns-plug.config.my_system_key='your_api_key'
uci set ns-plug.config.my_system_secret='your_api_secret'
uci commit ns-plug
/etc/init.d/vmalert restart
```

**Disable (alert-proxy only mode):**
```bash
uci delete ns-plug.config.my_url
uci delete ns-plug.config.my_system_key
uci delete ns-plug.config.my_system_secret
uci commit ns-plug
/etc/init.d/vmalert restart
```

## References

- [Victoria Metrics vmalert docs](https://docs.victoriametrics.com/vmalert/)
- [MetricsQL documentation](https://docs.victoriametrics.com/metricsql/)
- [Prometheus alerting rules](https://samber.github.io/awesome-prometheus-alerts/)
- [vmalert documentation](https://docs.victoriametrics.com/vmalert/)
- [Telegraf metrics collection](../telegraf/README.md)
