# ns-clm

Cloud Log Manager (CLM) forwarder for NethSecurity. Reads syslog messages from `/var/log/messages` and forwards them to the Nethesis CLM service.

## Requirements

- A CLM UUID provided manually by the user

## Configuration

UCI configuration is stored in `/etc/config/ns-clm`:

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | `0` | Enable/disable the forwarder |
| `uuid` | (empty) | Required CLM UUID used for registration and log forwarding |
| `address` | `https://nar.nethesis.it` | CLM server address |
| `tenant` | (empty) | CLM tenant identifier |
| `debug` | `0` | Enable debug output to stderr |

The forwarder will not start until `uuid` is configured.

Example setup:

```bash
uci set ns-clm.config.uuid="L$(uuidgen)"
uci set ns-clm.config.tenant='12345'
uci set ns-clm.config.enabled='1'
uci commit ns-clm
reload_config
```

## Service management

Only if the package is installed via apk, the service must be enabled and started via the init script. If the packages is already part of the base image, the forwarder is automatically enabled and started on first boot, so no manual action is required.

```bash
# Enable and start
/etc/init.d/ns-clm enable && /etc/init.d/ns-clm start

# Stop and disable
/etc/init.d/ns-clm stop && /etc/init.d/ns-clm disable
```

## How it works

1. On startup the daemon registers the appliance against the CLM `/adm/api/noauth_lmcheck/` endpoint using the configured UUID, tenant, hostname, and MAC address
2. It sends a startup event to the CLM syslog endpoint
3. It tails `/var/log/messages`, tracking its position via an offset file
4. New syslog lines are parsed and batched
5. Batches are sent as JSON to the CLM endpoint via HTTP POST
6. Log rotation is detected automatically (file shrinks → offset resets)
7. The daemon polls every 10 seconds for new lines
8. On shutdown (SIGTERM), the current offset is persisted for resume
