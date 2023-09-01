# ns-ui

ns-ui is the stand-alone UI (User Interface) built from [NethSecurity controller](https://github.com/NethServer/nethsecurity-controller).

## Management UI

By default, the ns-ui management UI along with LuCI is available on standard HTTPS port 443
at the following URL:
- ns-ui: `/`
- LuCI: `/cgi-bin/luci`

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
- `luci_enable`: it can be `0` or `1`; if set to `1` LuCI is enabled on port 443
- `nsui_enable`: it can be `0` or `1`; if set to `1` ns-ui is enabled on port 443
- `nsui_extra_port`: listen port for ns-ui extra instance, it must be a valid TCP port
- `nsui_extra_enable`: it can be `0` or `1`; if set to `1` ns-ui is enabled on port set with `nsui_extra_port` option

## UI development

The UI can be started on developer local machine and connected to the remote firewall.
This setup requires CORS headers enabled on the server.

To enable CORS on the server, just apply the below patch:
```diff
--- /etc/init.d/ns-api-server       2023-09-01 12:57:19.510000000 +0000
+++ /etc/init.d/ns-api-server.develop       2023-09-01 12:57:07.030000000 +0000
@@ -22,7 +22,7 @@
     mkdir -m 0700 -p ${TOKENS_DIR}
     mkdir -m 0700 -p ${SECRETS_DIR}
 
-    procd_set_param env GIN_MODE=release \
+    procd_set_param env GIN_MODE=debug \
         LISTEN_ADDRESS=127.0.0.1:8090 \
         SECRET_JWT="$(uuidgen | sha256sum | awk '{print $1}')" \
         ISSUER_2FA=${issuer_2fa} \
```

Then, restart the API server:
```
/etc/init.d ns-api-server restart
```
