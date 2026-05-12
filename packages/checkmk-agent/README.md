# checkmk-agent

Official Check_MK monitoring agent for OpenWrt-based systems.

## Description

This package provides the official Check_MK agent binary along with service management for NethSecurity. The agent is exposed via TCP port 6556 using socat, enabling remote monitoring server connections.

For NethSecurity-specific plugins and utilities, install the complementary `ns-checkmk-utils` package.

## Features

- Official Check_MK agent binary from upstream project
- Procd-managed service with automatic restart on failure
- TCP listener on port 6556 via socat
- Starts automatically on boot (START=98)
- Low dependency footprint

## Dependencies

- `socat`: Used to expose the agent via TCP socket and manage keepalive connections

## Installation

```bash
# Install the package
apk add checkmk-agent

# Start the service
/etc/init.d/check_mk_agent start

# Enable on boot
/etc/init.d/check_mk_agent enable
```

## Service Management

The agent is managed by procd and monitored for failures.

```bash
# Start/stop the service
/etc/init.d/check_mk_agent start
/etc/init.d/check_mk_agent stop

# Restart the service
/etc/init.d/check_mk_agent restart

# Enable/disable on boot
/etc/init.d/check_mk_agent enable
/etc/init.d/check_mk_agent disable

# View service status
/etc/init.d/check_mk_agent status
```

## Testing

Test the agent locally or remotely:

```bash
# Run agent directly to verify it works
/usr/sbin/check_mk_agent

# Test via TCP from the monitoring server
echo "" | nc <firewall-ip> 6556

```

## Firewall Rules

Port 6656 is open only from LAN by default. To allow monitoring server access, add a firewall rule to permit incoming connections on TCP port 6556 from the monitoring server's IP address or subnet.
Ensure your Check_MK monitoring server can reach the firewall on TCP port 6556:

```bash
# Allow connections from monitoring server (example)
uci add firewall rule
uci set firewall.@rule[-1].name='Allow Check_MK'
uci set firewall.@rule[-1].src='wan'
uci set firewall.@rule[-1].proto='tcp'
uci set firewall.@rule[-1].dest_port='6556'
uci set firewall.@rule[-1].target='ACCEPT'
uci commit firewall
```

## Extending with Plugins

To add NethSecurity-specific plugins and utilities, install the `ns-checkmk-utils` package:

```bash
apk add ns-checkmk-utils
```

Plugins are stored in `/usr/lib/check_mk_agent/local` and are automatically executed by the agent.

## Troubleshooting

**Agent not responding on port 6556:**
- Verify the service is running: `/etc/init.d/check_mk_agent status`
- Check firewall rules allow inbound traffic on port 6556
- Test locally: `/usr/sbin/check_mk_agent`

## See Also

- [ns-checkmk-utils](../ns-checkmk-utils/): NethSecurity-specific plugins and utilities
- [Checkmk Documentation](https://docs.checkmk.com/): Official Checkmk documentation
- [Checkmk GitHub](https://github.com/Checkmk/checkmk): Checkmk project repository
