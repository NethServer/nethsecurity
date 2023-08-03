# ns-ui

ns-ui is the stand-alone UI (User Interface) built from [NethSecurity controller](https://github.com/NethServer/nethsecurity-controller).

## Management UI

As default, the ns-ui management UI along with LuCi are available on standard HTTPS port 443
at the following URL:
- ns-ui: `/`
- LuCi: `/cgi-bin/luci`

You can:
- selectively disable or enable both UIs
- add an extra ns-ui instance on a different port

Example: disable both UIs on port 443, enable ns-ui only port 9090:
```
uci set ns-ui.config.nsui_extra_enable=1
uci set ns-ui.config.nsui_extra_port=9090
uci set ns-ui.config.nsui_enable=0
uci set ns-ui.config.luci_enable=0
uci commit ns-ui
ns-ui
```

## Configuration

The package provides a configuration named `/etc/config/ns-ui`.
It must contain a section named `config` of type `main`.

Database example:
```
config main 'config'
	option luci_enable '1'
	option nsui_enable '1'
	option nsui_extra_port '9090'
	option nsui_extra_enable '0'
```

Available options:
- `luci_enable`: it can be `0` or `1`; if set to `1` LuCi is enabled on port 443
- `nsui_enable`: it can be `0` or `1`; if set to `1` ns-ui is enabled on port 443
- `nsui_extra_port`: listen port for ns-ui extra instance, it must be a valid TCP port
- `nsui_extra_enable`: it can be `0` or `1`; if set to `1` ns-ui is enabled on port set with `nsui_extra_port` option

## UI development

The UI can be started on developer local machine and connected to the remote firewall.
This setup requires CORS headers enabled on the server.

To enable CORS on the server, just apply the below patch:
```diff
# diff -u /etc/nginx/conf.d/luci.locations.ori /etc/nginx/conf.d/luci.locations
--- /etc/nginx/conf.d/luci.locations.ori    2022-04-20 15:54:21.000000000 +0000
+++ /etc/nginx/conf.d/luci.locations    2022-04-20 15:52:31.000000000 +0000
@@ -1,4 +1,6 @@
 location /cgi-bin/luci {
+        add_header 'Access-Control-Allow-Origin' '*' always;
+        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
+        add_header 'Access-Control-Allow-Headers' 'content-type' always;
+
         index  index.html;
         include uwsgi_params;
         uwsgi_param SERVER_ADDR $server_addr;
@@ -6,6 +8,8 @@
         uwsgi_pass unix:////var/run/luci-webui.socket;
 }
 location ~ /cgi-bin/cgi-(backup|download|upload|exec) {
+        add_header 'Access-Control-Allow-Origin' '*' always;
+
         include uwsgi_params;
         uwsgi_param SERVER_ADDR $server_addr;
         uwsgi_modifier1 9;
@@ -17,6 +21,8 @@
 }
 
 location /ubus {
+        add_header 'Access-Control-Allow-Origin' '*' always;
+
         ubus_interpreter;
         ubus_socket_path /var/run/ubus/ubus.sock;
         ubus_parallel_req 2;
```
