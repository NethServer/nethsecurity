#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Victoria Logs

## Overview

This package provides **Victoria Logs** for centralized log storage and aggregation in NethSecurity. All system logs are collected from rsyslog and stored in Victoria Logs, which can be queried and visualized.

**Key Components:**
- **victoria-logs**: Log database on port 9428
- **rsyslog integration**: All syslog messages are forwarded to Victoria Logs on port 5514 (localhost)
- **Retention management**: Automatic retention policy based on available storage
- **Storage flexibility**: Uses external storage (`ns_data` mount) when available, falls back to internal `/var/lib`

## Installation

This package is **not installed by default**. To enable Victoria Logs:

```bash
# Install the package
apk add victoria-logs
```

The package depends on rsyslog. This service will automatically start on installation.

To enable the service to start on boot:

```bash
/etc/init.d/victoria-logs enable
```

## Configuration

Configuration is managed via UCI. View current settings:

```bash
uci show victoria-logs
```

**Available options:**
- `http_listen_addr`: Address and port for the HTTP server (default: `127.0.0.1:9428`)

**Auto-detected options (not set in default config):**
- `storage_path`: Where to store log data
  - **With external storage** (`ns_data` mount): `<mount_point>/victoria-logs-data`
  - **Without external storage**: `/var/lib/victoria-logs-data`
  
- `retention_period`: How long to keep logs
  - **With external storage**: `1y` (one year)
  - **Without external storage**: `7d` (seven days, due to tmpfs size limits)

- `max_disk_usage`: Maximum disk space before pruning old logs
  - **With external storage**: No limit (relies on retention period)
  - **Without external storage**: `50MB` (protects the tmpfs from filling up)

### Modifying Configuration

Use `uci` to modify settings. Examples:

```bash
# Change the listen address to localhost only (secure default)
uci set victoria-logs.main.http_listen_addr='127.0.0.1:9428'

# Expose to all interfaces
uci set victoria-logs.main.http_listen_addr='0.0.0.0:9428'

# Expose to a specific IP and port
uci set victoria-logs.main.http_listen_addr='192.168.1.100:9428'

# Expose to a specific interface on custom port
uci set victoria-logs.main.http_listen_addr=':8080'

# Override retention period
uci set victoria-logs.main.retention_period='90d'

# Override storage location
uci set victoria-logs.main.storage_path='/mnt/custom/logs'

# Override max disk usage
uci set victoria-logs.main.max_disk_usage='5GB'
```

After making changes, commit and reload:

```bash
uci commit victoria-logs
/etc/init.d/victoria-logs restart
```

## Web UI

Victoria Logs exposes a Web UI at `/select/vmui` on port 9428.

### Via SSH Port Forwarding (Recommended)

For secure remote access without exposing the service:

```bash
ssh -L 9428:127.0.0.1:9428 root@remote_host
```

Then open `http://127.0.0.1:9428/select/vmui` in your browser.

### Expose to a Specific Network

Allow access from a specific network (e.g., `192.168.1.0/24`):

```bash
uci set victoria-logs.main.http_listen_addr='192.168.1.100:9428'
uci commit victoria-logs
/etc/init.d/victoria-logs restart
```

Then access from any machine on that network: `http://192.168.1.100:9428`

### Expose to Everyone

Allow access from any network interface:

```bash
uci set victoria-logs.main.http_listen_addr='0.0.0.0:9428'
uci commit victoria-logs
/etc/init.d/victoria-logs restart
```

Access from anywhere: `http://<firewall_ip>:9428`

**Note:** This exposes your logs without authentication. It is your responsibility to add firewall rules, VPN requirements, or network-level security to protect access.

## Storage and Retention

### Understanding Storage Paths

**Case 1: External storage is mounted** (`ns_data` detected)
- Logs are stored at `<mount>/victoria-logs-data`
- Retention is set to **1 year**
- No disk usage limit is applied (space is expected to be plentiful)
- Old logs are gradually deleted as the 1-year window slides

**Case 2: No external storage** (default setup)
- Logs are stored at `/var/lib/victoria-logs-data`
- Retention is limited to **7 days** (due to tmpfs constraints)
- Disk usage is capped at **50MB** to prevent OOM
- The oldest logs are deleted to make room for new ones when either limit is reached

### Checking Storage Usage

```bash
# View current storage usage
df -h /var/lib/victoria-logs-data

# If external storage is present:
df -h /mnt/data/victoria-logs-data

# View logs retained by Victoria Logs
curl 'http://127.0.0.1:9428/api/v1/status' | jq '.data | {storageDataPath, retentionDays, totalDiskUsage}'
```

## See Also

- [Victoria Metrics](../victoria-metrics/) — Companion time-series database for metrics
- OpenWrt [rsyslog documentation](https://www.rsyslog.com/) — For advanced syslog configuration
