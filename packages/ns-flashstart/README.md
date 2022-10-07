# ns-flashstart

ns-flashstart is the client configuration for [FlashStart](https://flashstart.com) DNS filter.

The client is composed by 3 main parts:

- `/usr/sbin/flashstart-apply`: script to enable and disable flashstart
- `/usr/share/ns-flashstart/flashtart-auth`: authentication script called by apply and crontab
- `/usr/share/ns-flashstart/flashtart-intercept`: create firewall rules
- `/etc/config/flashstart`: UCI configuration file

## Configuration

The `ns-flashstart` service needs the `username` and `password` options.
Below example will register the client and start dsndist with Flashstart forwarders:
```
uci set flashstart.global.username="myuser@nethserver.org"
uci set flashstart.global.password="mypassword"
uci set flashstart.global.enabled="1"
uci commit flashstart
flashstart-apply
```

Set dnsdist as forwarder:
```
uci add_list dhcp.@dnsmasq[0].server='127.0.0.1#5300'
uci commit dhcp
/etc/init.d/dhcp restart
```

Setup firewall intercept rules with bypass based on ipset:
```
/usr/share/ns-flashstart/flashstart-intercept <zone>
```
This will create the firewall rule named `ns_redirect_dns_<zone>` and the ipset for bypass named `ns_redirect_dns_<zone>_bypass`.

Example:
```
/usr/share/ns-flashstart/flashstart-intercept lan
```

To add a bypass for the `lan` zone, just add an IP address to the ipset:
uci add_list firewall.ns_redirect_dns_lan_bypass.entry="1.2.3.4"
uci commit firewall
/etc/init.d/firewall restart
```

Disable Flashstart:
```
uci set flashstart.global.enabled=0
uci commit flashstart
flashstart-apply
```

After disabling, remember to remove all redirection firewall rules.
