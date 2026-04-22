# ns-plug

ns-plug handles:
- the connection to remote [NethSecurity controller](https://github.com/NethServer/nethsecurity-controller)
- the machine registration to monitoring services like [my.nethserver.com](https://my.nethserver.com) (community subscription)
  and [my.nethesis.it](https://my.nethesis.it) (enterprise subscription)
- the remote backup for enterprise subscriptions

## NethSecurity controller client

The client is composed by 3 main parts:

- `/usr/sbin/ns-plug`: sh script to register the firewall and start the VPN
- `/etc/init.d/ns-plug`: start `ns-plug` script as a daemon, it automatically restarts the service if the configuration changes
- `/etc/config/ns-plug`: UCI configuration file

The `ns-plug` service needs at least the following options:
- the `server`: an HTTPS URL of the controller
- the `unit_id`: a UUID identifier of the machine
- the `token`: the registration token available inside the controller

Example:
```
uci set ns-plug.config.server=https://controller.nethserver.org
uci set ns-plug.config.unit_id=$(34f15657-9fce-4e36-8046-6d116ef07b57)
uci set ns-plug.config.token=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
uci commit ns-plug
/etc/init.d/ns-plug restart
``` 

On first run, `ns-plug` will create an administrator user for Luci, the user is saved inside UCI config `rpcd.controller`. The user will have a random name and a random password.
At start-up, the service will try to register to the remote controller. If the system has been already approved, `ns-plug` will download the VPN configuration and connect to the controller. Otherwise, it will poll the controller every 10 seconds waiting for approval.
The password of controller user will be regenerated and sent to the controller on each restart.

`ns-plug` uses the HTTPS certificate to validate the controller identity.
On development environments, if a valid certificate is not available, it is possible to disable TLS verification:
```
uci set ns-plug.config.tls_verify='0'
uci commit ns-plug
/etc/init.d/ns-plug restart
```

To reset ns-plug configuration use:
```
uci delete rpcd.controller
uci commit rpcd
uci set ns-plug.config.server=''
uci set ns-plug.config.unit_id=''
uci set ns-plug.config.token=''
uci commit ns-plug
uci delete rsyslog.promtail
uci commit rsyslog
rm -f /usr/share/ns-plug/client.conf
```

### MTU management

In some cases the VPN connection may not work properly due to MTU issues.
You can custom set the MTU values by:
```
uci set ns-plug.config.tun_mtu=<value>
uci set ns-plug.config.mssfix=<value>
uci commit ns-plug
reload_config
```

## Machine registration

To register a machine:
- access [my.nethserver.com](https://my.nethserver.com) or [my.nethesis.it](https://my.nethesis.it)
  and create a new server
- copy the generated secret token

For enterprise subscription, execute:
```
register enterprise <secret>
```
For community subscription, execute:
```
register community <secret>
```

When the machine has been registered, the system will:
- send an heartbeat every 10 minutes using `send-heartbeat` script
- send the inventory every night using `send-inventory` script

To deregister the machine, execute:
```
unregister
```

### Hooks

The registration can be customized by adding scripts inside the `/usr/share/ns-plug/hooks/<command>` directory:
- `register` command will search for custom scripts inside the `/usr/share/ns-plug/hooks/register`
- `unregister` command will search for custom scripts inside the `/usr/share/ns-plug/hooks/unregister`

Custom scripts must be executable and will be executed in lexicographic order.
The execution will continue regardless of script exit codes.

## Remote backup

If the machine has a valid enterprise subscription, every night a cron job
will execute the backup and send it to a remote server.

### Backup encryption

If the file `/etc/backup.pass` exists, the backup will be encrypted using
the given passphrase: only the encrypted backup will be sent to the remote server.

To disable the encryption, just delete the file `/etc/backup.pass`.

Non-encrypted backups are not sent to the remote server for security reasons.
If the backup is not encrypted, an alert will be sent to the remote portal (my.nethesis.it or my.nethserver.com)
so the user can be aware of the risk and take action to secure the backup.

### Restore

Download the latest unencrypted backup and restore it:
```
remote-backup download $(remote-backup list | jq -r .[0].file) - | sysupgrade -r -
```

Download the latest encrypted backup and restore it:
```
echo <your_passphrase> > /etc/backup.pass
remote-backup download $(remote-backup list | jq -r .[0].file) - | gpg --batch --passphrase-file /etc/backup.pass -d | sysupgrade -r -
```

## Alerts

All system alerts, except MultiWAN ones, are handled by netdata, including those from the multiwan monitoring.
Alerts are disabled by default and enabled only if the machine has a valid subscription.
In this case, alerts are automatically sent to the remote server (either my.nethesis.it or my.nethserver.com) using a
custom sender (`/etc/netdata/health_alarm_notify.conf`).
Alerts are also logged to `/var/log/messages` and are visible within the netdata UI.

Only the following alerts are sent to the remote system:

| Alert | Condition | Legacy alert_id |
|---|---|---|
| `WanDown` | WAN interface offline for 2m | `wan:<interface>:down` |
| `DiskSpaceCritical` | Disk usage > 90% for 2m | `df:root:percent_bytes:free` or `df:boot:percent_bytes:free` |
| `BackupEncryptionDisabled` | Backup passphrase missing | `backup:config:notencrypted` |
| `StorageStatus` | Storage status is error | `storage:status` |

All other alert are silently dropped by the proxy.
If the machine is not registered, all alerts are silently dropped.

The proxy starts automatically at boot regardless of registration state.
Firing/resolved state is determined from the Alertmanager-standard `endsAt` field:
if `endsAt` is in the future (or zero/missing) a **FAILURE** is sent; if `endsAt` is in
the past an **OK** is sent.
