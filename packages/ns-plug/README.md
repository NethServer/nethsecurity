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

The `ns-plug` service needs only the `server` configuration option. Example:
```
uci set ns-plug.config.server=https://controller.nethserver.org
uci commit ns-plug
``` 

As default, `ns-plug`will identify itself using the MAC address of the LAN network interface without separators: given a MAC address like `52:54:00:6b:8a:cf`, the default `system_id` will be `5254006b8acf`.
The system id can also be overridden using the `system_id` option. Example:
```
uci set ns-plug.config.system_id=392e068e-8557-4b1e-ba15-a1dfba1d59f0
uci commit ns-plug
```

On first run, `ns-plug` will create an administrator user for Luci, the user is saved inside UCI config `rpcd.controller`. The user will have a random name and a random password.
At start-up, the service will try to register to the remote controller. If the system has been already approved, `ns-plug` will download the VPN configuration and connect to the controller. Otherwise, it will poll the controller every 10 seconds waiting for approval.
The password of controller user will be regenerated and sent to the controller on each restart.

`ns-plug` uses the HTTPS certificate to validate the controller identity.
On development environments, if a valid certificate is not available, it is possible to disable TLS verification:
```
uci set ns-plug.config.tls_verify='0'
uci commit ns-plug
```

To reset ns-plug configuration use:
```
uci delete rpcd.controller
uci set ns-plug.config.server=''
uci set ns-plug.config.system_id=''
uci commit
rm -f /usr/share/ns-plug/client.conf
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

All system alerts are handled by netdata, including those from the multiwan monitoring.
Alerts are disabled by default and enabled only if the machine has a valid subscription.
In this case, alerts are automatically sent to the remote server (either my.nethesis.it or my.nethserver.com) using a
custom sender (`/etc/netdata/health_alarm_notify.conf`).
Alerts are also logged to `/var/log/messages` and are visible within the netdata UI.

Only the following alerts are sent to the remote system:

- disk space occupation
- WAN down events

When an alert is resolved, netdata will also send a clear command to remote server.

## mwan3 netdata plugin

The `/usr/lib/netdata/python.d/mwan.chart.py` file implements a netdata plugin for mwan3.
The plugin tracks the score of each WAN using mwan3track status directory.
When a WAN reaches a score equal to 1, an alert is triggered.

Please note that mwan3track minumum score is `0` which is mapped to `1` inside netdata,
otherwise the `0` value is not plotted within the chart.
