# ns-flashstart

ns-flashstart is the client configuration for [FlashStart](https://flashstart.com) DNS filter.

The client is composed by 3 main parts:

- `/usr/sbin/flashstart-apply`: script to enable and disable flashstart
- `/usr/share/ns-flashstart/flashtart-auth`: authentication script called by apply and crontab
- `/usr/share/ns-flashstart/flashtart-setup-firewall`: create firewall rules
- `/etc/config/flashstart`: UCI configuration file

## Configuration

The `ns-flashstart` service needs the `username` and `password` options which can be obtained
only after a signup to Flashstart service.

Below example will register the client, start dsndist with Flashstart forwarders and setup DNS redirection on `lan`:
```
uci set flashstart.global.username="myuser@nethserver.org"
uci set flashstart.global.password="mypassword"
uci set flashstart.global.enabled="1"
uci add_list flashstart.global.zones="lan"
uci commit flashstart
flashstart-apply
```

Then, set dnsdist as forwarder for dnsmasq:
```
uci add_list dhcp.@dnsmasq[0].server='127.0.0.1#5300'
uci commit dhcp
/etc/init.d/dhcp restart
```

If some source IPs should not be redirect to the filter, just add them
to the `bypass` list:
```
uci add_list flashstart.bypass="1.2.3.4"
uci commit flashstart
flashstart-apply
```

## Disabling the service

To disable Flashstart:

1. Remove dnsdist configuration and firewall rules
   ```
   uci set flashstart.global.enabled=0
   uci commit flashstart
   flashstart-apply
   ```

2. Remove the forwarder from dnsmasq
   ```
   uci del_list dhcp.@dnsmasq[0].server='127.0.0.1#5300'
   uci commit dhcp
   /etc/init.d/dnsmasq restart
   ```
