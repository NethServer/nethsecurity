# ns-checkmk-agent

Check_MK monitoring agent integration for NethSecurity.

## Description

This package provides the Check_MK agent for monitoring NethSecurity firewalls. It includes:

- Main Check_MK agent from the official Checkmk repository
- Custom plugins for NethSecurity-specific monitoring
- Procd-managed service using socat to listen on TCP port 6556

## Features

- Automatic start on boot (START=98)
- Respawn on failure
- TCP listener on port 6556 using socat
- Plugin support at `/usr/lib/check_mk_agent/plugins/`

## Adding More Plugins

To add additional plugin files from the [checkmk-tools repository](https://github.com/Coverup20/checkmk-tools/tree/main/script-check-nsec8/full):

1. Browse the plugin directory on GitHub to find available plugins
2. Add the plugin name to the `PLUGIN_FILES` variable in the Makefile:

```makefile
PLUGIN_FILES:=nethsecurity openvpn ipsec mwan3 certificates <new_plugin_name>
```

3. The plugin will be automatically downloaded and installed to `/usr/lib/check_mk_agent/plugins/` during the build

## Testing

After installation on a NethSecurity firewall:

```bash
# Test agent locally
/usr/bin/check_mk_agent

# Test via network from monitoring server
echo "" | nc <firewall-ip> 6556

# Check service status
/etc/init.d/check_mk_agent status

# Start/stop service
/etc/init.d/check_mk_agent start
/etc/init.d/check_mk_agent stop
```

## Configuration

The service is configured via procd and requires no additional configuration files. To enable/disable the service:

```bash
/etc/init.d/check_mk_agent enable
/etc/init.d/check_mk_agent disable
```

## Dependencies

- socat: Used to expose the agent via TCP socket

## Firewall Rules

Remember to allow incoming connections on TCP port 6556 from your Check_MK monitoring server.
