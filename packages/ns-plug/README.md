# ns-plug

ns-plug is the client connecting the firewall to a remote [NextSecurity controller](https://github.com/NethServer/nextsecurity-controller).

The client is composed by 3 main parts:

- `/usr/sbin/ns-plug`: sh script to register the firewall and start the VPN
- `/etc/init.d/ns-plug`: start `ns-plug` script as a daemon, it automatically restarts the service if the configuration changes
- `/etc/config/ns-plug`: UCI configuration file

The `ns-plug` service needs only the `server` configuration option. Example:
```
uci set ns-plug.config.server=https://controller.nethserver.org
uci commit
``` 

As default, `ns-plug`will identify itself using the MAC address of the LAN network interface without separators: given a MAC address like `52:54:00:6b:8a:cf`, the default `system_id` will be `5254006b8acf`.
The system id can also be overridden using the `system_id` option. Example:
```
uci set ns-plug.config.system_id=392e068e-8557-4b1e-ba15-a1dfba1d59f0
uci commit
```

On first run, `ns-plug` will create an administrator user for Luci, the user is saved inside UCI config `rpcd.controller`. The user will have a random name and a random password.
At start-up, the service will try to register to the remote controller. If the system has been already approved, `ns-plug` will download the VPN configuration and connect to the controller. Otherwise, it will poll the controller every 10 seconds waiting for approval.
The password of controller user will be regenerated and sent to the controller on each restart.

`ns-plug` uses the HTTPS certificate to validate the controller identity.
On development environments, if a valid certificate is not available, it is possible to disable TLS verification:
```
uci set ns-plug.config.tls_verify='0'
uci commit
```

To reset ns-plug configuration use:
```
uci delete rpcd.controller
uci set ns-plug.config.server=''
uci set ns-plug.config.system_id=''
uci commit
rm -f /usr/share/ns-plug/client.conf
```
