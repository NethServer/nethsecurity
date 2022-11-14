# ns-openvpn

This is a partial porting of [nethserver-openvpn](https://github.com/NethServer/nethserver-openvpn/).

Changes since NS7:

- IP reservation is enforced
- support for multiple server instances
- SQLite connection database is volatile

Supported authentications:

- certificate only
- username and password
- username, password and certificate

Not supported:

- authentication based on certificate + otp
- mail notification about connect/disconnect events

## OpenVPN Road Warrior configuration

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

## Manage Road Warrior users

Certificates are saved inside `/etc/openvpn/<instance>/pki/` directory.

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

### Set user password

User passwords are saved inside UCI in passwd format `$<hash_method>$<salt>$<hash>`:
- `hash_method` is always set to `6`, which is `sha512`
- `salt` is a random ASCII string of 16 characters
- `hash` is a 86 characters hash calcultated using `mkpasswd` command

Generate the user password:
```
salt=$(uuidgen | md5sum | cut -c 0-15)
echo -e '<password>' | mkpasswd -m sha512 -S "$salt"
```

Example: set password `nethesis` for user `test`:
```
uci set openvpn.test.password=$(echo -e 'nethesis' | mkpasswd -m sha512 -S "$(uuidgen | md5sum | cut -c 0-15)")
uci commit openvpn
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

## Roadwarrior client configuration

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

## Tunnels

Tunnels are normal `openvpn` sections inside `/etc/config/openvpn`.
All tunnels are addedd the `openvpntun` trusted zone.

### Servers

Each tunnel server requires to configure an iroute for every local network which should be exposed to tunnel client.
The iroute is configured upon client connection using `/usr/libexec/ns-openvpn/connect-scripts/10-tunnel-iroute` script.

Each tunnel server must have the following configuration options:
```
option client_connect '"/usr/libexec/ns-openvpn/openvpn-connect <tunnel_name>"'
option client_disconnect '"/usr/libexec/ns-openvpn/openvpn-disconnect <tunnel_name>"'
```
