# ns-openvpn

This is a partial porting of [nethserver-openvpn](https://github.com/NethServer/nethserver-openvpn/).

Changes since NS7:

- IP reservation is enforced
- support for multiple server instances
- SQLite connection database is volatile

Not supported:

- authentication based on certificate + otp
- authentication based on password + certificate
- authentication based on password
- mail notification about connect/disconnect events

## OpenVPN configuration

Upon installation, the `ns-openvpnrw-setup`:

- create a default OpenVPN roadwarrior server instance named `ns_roadwarrior`
- open the default `ns_roadwarrior` port (`1194/udp`) from the WAN zone
- create a `openvpnrw` trusted firewall zone which has access to LAN and WAN
- setup the PKI (Public Key Infrastructure) inside `/etc/openvpn/<instance>/pki` with `ns-openvpnrw-init-pki`

On client connect, the server will execute all scripts inside `/usr/libexec/ns-openvpn/connect-scripts/` directory in lexicographical order.
On client disconnect, the server will execute all scripts inside `/usr/libexec/ns-openvpn/disconnect-scripts/` directory in lexicographical order.
Each script takes 2 arguments: the server instance name and the client cn.

A client can connect to the server if:

- there is a valid certificate inside with the same CN
- the user belongs to the `ns_roadwarrior` server instance and is marked as enabled inside `openvpn` database

Database example of a user:
```
config user 'giacomo'
	option instance 'ns_roadwarrior'
	option ipaddr '10.9.9.70'
	option enabled '1'
```

### First configuration

Execute:
```
ns-openvpnrw-setup
uci set openvpn.ns_roadwarrior.enabled=1
uci commit openvpn
service openvpn start
```

## Manage users

Certificates are saved inside

### Add user

The `ns-openvpnrw-add` script will:

- create certificate and key of the user
- create a user entry inside the `openvpn` UCI database

Newly created user are automatically enabled.

Execute:
```
ns-openvpnrw-add <instance> <user>
```

Example:
```
ns-openvpnrw-add ns_roadwarrior giacomo
```

### IP static lease

Execute:
```
uci set openvpn.<user>.ipaddr=0
uci commit openvpn
```

### Disable a user

Execute:
```
uci set openvpn.<user>.enabled=0
uci commit openvpn
```
### Remove a user

The `ns-openvpnrw-revoke` script will:

- revoke the certificate and delete the user key
- remove entry from `openvpn` UCI database

Execute:
```
ns-openvpnrw-revoke <instance> <user>
```

Example:
```
ns-openvpnrw-revoke ns_roadwarrior giacomo
```

## Client configuration

The `ns-openvpnrw-print-client` can generate a valid `.ovpn` file with embedded certificates.
The generated configuratio can be copied to any compatibile client.

Execute:
```
ns-openvpnrw-print-client <instance> <user>
```

Example:
```
ns-openvpnrw-print-client ns_roadwarrior giacomo > giacomo.ovpn
```

## Accounting

Every client connection is tracked inside a SQLite database saved inside `/var/openvpn/<instance>/connections.db`.
The databse is initialized as soon as the `instance` is up using the `init-connections-db` script.

As default, all logs are sent to `/var/log/messages`.
