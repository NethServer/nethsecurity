# ns-ui

ns-ui is the stand-alone UI built from [NextSecurity controller](https://github.com/NethServer/nextsecurity-controller).

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
