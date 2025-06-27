# ns-flashstart

ns-flashstart is the client configuration for [FlashStart](https://flashstart.com) DNS filter.

The client is composed in three main parts:

- `/usr/sbin/ns-flashstart`: script manage flashstart
- `/usr/share/ns-flashstart/flashtart-auth`: authentication script called by apply and crontab
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
reload_config
```

If some source IPs should not be redirected to the filter, just add them to the `bypass` list:

```
uci add_list flashstart.bypass="1.2.3.4"
uci commit flashstart
reload_config
```

If you need a specific domain to be resolved through a specific DNS server, you can add it to the `custom_servers`:

```
uci add_list flashstart.custom_servers="/example.com/1.1.1.1"
uci commit flashstart
reload_config
```

## DNS server customization

You can disable `rebind_protection` or enable `logqueries` options for the DNS servers by setting the variables in the
`flashstart.global` section:

```
uci set flashstart.global.rebind_protection="0"
uci set flashstart.global.logqueries="1"
uci commit flashstart
reload_config
```

## Debug mode

The daemon can be run in various logging levels, to set the levels you can:

```
uci set flashstart.global.log_level="debug"
uci commit flashstart
reload_config
```

To check for the logging levels available, please refer to the CLI utility help:

```
ns-flashstart --help
```

## CLI utility

The script `/usr/sbin/ns-flashstart` can be used to manage the client from command line. To see the
available options, run:

```
ns-flashstart --help
```
