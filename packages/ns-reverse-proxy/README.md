# ns-reverse-proxy

Use nginx to act as a reverse proxy.
The reverse proxy forwards web requests to another HTTP server and serves responses in behalf of it. 

The reverse proxy supports the following rules:

- path based: matches the given path when requested to the default virtual host (`_lan`)
- host based: matches the given host name

## Configuration

This package introduces a new object of type `location` inside UCI config `/etc/config/nginx`.

The `location` object can contain any `nginx` directive, plus the following special options:

- `location`: URI of the location, it accepts [nginx syntax](http://nginx.org/en/docs/http/ngx_http_core_module.html#location)
- `uci_server`: it binds the location to a `server` object with the same name; if set to `_lan`,  the location will be added inside the default virtual host
- `uci_description`: (optional) description of the rule, it's converted to a comment inside the configuration file
- `allow`: (optional) an array of allowed IP addresses; if present, all other addresses will be automatically denied

If a directive can be used multiple times, it's represented as a UCI list.

The `nginx-proxy` utility reads all the location objects from UCI config and creates the nginx configuration
inside `/etc/nginx/conf.d/<server>.proxy` files, like `/etc/nginx/conf.d/_lan.proxy`.
Then, the generated files must be explicitly added to the `include` option of the server object.

When the `proxy_pass` option points to a hostname, the hostname *must* be resolvable during
nginx startup, otherwise nginx will fail.
To make sure the target server is always resolvable, use the following hack:
```
option resolver '127.0.0.1'
option set '$upstream server.nethserver.org'
option proxy_pass 'https://$upstream'
```

### Path rules

Example of a path rule for the default virtual host:
```
config location 'ns_location1'
	option uci_server '_lan'
	option proxy_pass 'https://192.168.100.234'
	option uci_description 'Reverse proxy with path'
	option proxy_ssl_verify 'off'
	option location '/test'
```

To enable the rule:
```
nginx-proxy
uci add_list nginx._lan.include='conf.d/_lan.proxy'
uci commit nginx
/etc/init.d/nginx restart
```

Example of a path rule for a WebSocket inside the `ns_server2` virtual host:
```
config location 'ns_server2_location1'
	option uci_server 'ns_server2'
	option location '/ws'
	option proxy_pass 'http://192.168.0.100/ws'
	option proxy_http_version '1.1'
	list proxy_set_header 'Upgrade $http_upgrade'
	list proxy_set_header 'Connection "Upgrade"'
``` 

To enable the rule:
```
nginx-proxy
uci add_list nginx.ns_server2.include='conf.d/ns_server2.proxy'
uci commit nginx
/etc/init.d/nginx restart
```

### Host rules

Host rules use host configuration from [official OpenWrt documentation for nginx](https://openwrt.org/docs/guide-user/services/webserver/nginx).
Each host must include it's `.proxy` configuration file containing the locations.

Example for host `test.example.org`:
```
config location 'ns_server1_location2'
	option uci_server 'ns_server1'
	option location '/'
	option proxy_pass 'http://192.168.100.200'

config server 'ns_server1'
	option ssl_certificate '/etc/nginx/conf.d/ns_server1.crt'
	option ssl_certificate_key '/etc/nginx/conf.d/ns_server1.key'
	option uci_description 'Proxy pass host'
	option ssl_session_timeout '64m'
	option ssl_session_cache 'shared:SSL:32k'
	option proxy_ssl_verify 'on'
	option server_name 'test.example.org'
	list proxy_set_header 'Host $http_host'
	list listen '443 ssl'
	list listen '[::]:443 ssl'
	list allow '192.168.100.0/24'
    list include 'conf.d/ns_server1.proxy'
```

To enable the rule:
```
nginx-proxy
/etc/init.d/nginx restart
```
