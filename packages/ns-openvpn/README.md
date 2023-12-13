# ns-openvpn

This is a partial porting of [nethserver-openvpn](https://github.com/NethServer/nethserver-openvpn/).

## OpenVPN road warrior

Changes since NS7:

- IP reservation is enforced
- support for multiple server instances
- SQLite connection database is volatile

Supported authentications:

- certificate only
- user name and password
- user name, password and certificate

Not supported:

- mail notification about connect/disconnect events

Supported authentication methods:

- local users with certificate only
- local users with password
- local users with password and certificate
- remote LDAP users with password
- remote LDAP users with password and certificate
- authentication based on certificate + otp

Network and firewall configuration:

- the network device is named `tunrw`
- the default zone for the device is named `rwopenvpn`: this is a trusted zone,
  it will have access to `lan` and `wan` zones, it will be also accessible from `lan` zone

### First configuration

After installation, the OpenVPN roadwarrior instance is not configured.

You can create an instance using the API: `/usr/libexec/rpcd/ns.ovpnrw call add-instance`.

The API will:

- create a default OpenVPN roadwarrior server instance named `ns_roadwarrior1`
- open the default `ns_roadwarrior` port (`1194/udp`) from the WAN zone
- create a `rwopenvpn` trusted firewall zone which has access to LAN and WAN
- setup the PKI (Public Key Infrastructure) inside `/etc/openvpn/<instance>/pki` with `ns-openvpnrw-init-pki`
- create default firewall rules to access the `ns_roadwarrior1` server from the WAN

On client connect, the server will execute all scripts inside `/usr/libexec/ns-openvpn/connect-scripts/` directory in lexicographical order.
On client disconnect, the server will execute all scripts inside `/usr/libexec/ns-openvpn/disconnect-scripts/` directory in lexicographical order.
Each script takes 2 arguments: the server instance name and the client CN.

Changes from API are not commited.
To start the OpenVPN execute:
```
uci commit openvpn firewall network
service openvpn start
service network restart
service firewall restart
```

All APIs are documented inside the [ns-api](../ns-api/#nsovpnrw) page.

### Authentications methods

Each user must have an entry of type `user` or `local-user` inside `users` UCI configuration file
and must have at least the following fields:
- `openvpn_enabled`: can be `0` or `1`, if set to `0` the user can't authenticate itself

Each user can have also the following options:

- `openvpn_ipaddr`: IP address reserved for the user
- `openvpn_2fa`: OTP secret

See [ns-objects](../ns-objects/) for more info.

#### Local users with certificate only

A client can connect to the server if:

- there is a valid certificate inside the certificate directory: the certificate CN must match the user name
- the user belongs to the database associated to the RoadWarrior instance
- the user `openvpn_enabled` field is set to `1` inside `users` database

Certificates are saved inside `/etc/openvpn/<instance>/pki/` directory.

Default `certificate_expiration` is `3650` days (1 year).

To enable this authentication the `user_pass_verify` option must be empty or not set.

#### Local user with password

A client can connect to the server if:

- the user belongs to the database associated to the RoadWarrior instance
- the user `openvpn_enabled` field is set to `1` inside `users` database
- the provided user password matches the one saved inside `password` option

To enable this authentication the `user_pass_verify` option must be set to `/usr/libexec/ns-openvpn/openvpn-local-auth via-env`.

#### Local users with password and certificate

A client can connect to the server if:

- there is a valid certificate inside the certificate directory: the certificate CN must match the user name
- the user belongs to the database associated to the RoadWarrior instance
- the user `openvpn_enabled` field is set to `1` inside `users` database

#### Local users with certificate + OTP

A client can connect to the server if:

- the user belongs to the database associated to the RoadWarrior instance
- there is a valid certificate inside the certificate directory: the certificate CN must match the user name
- the user belongs to the database associated to the RoadWarrior instance
- the provided user OTP matches the one generated using `oathtool` from the 2FA secret saved inside `openvpn_2fa` field

To enable this authentication the `user_pass_verify` option must be set to `/usr/libexec/ns-openvpn/openvpn-otp-auth via-env`.

#### Remote LDAP users with password

A client can connect to the server if:

- the user belongs to the database associated to the RoadWarrior instance
- the user `openvpn_enabled` field is set to `1` inside `users` database
- the user password can authenticate against remote LDAP server with provided password

To enable this authentication the `user_pass_verify` option must be set to `/usr/libexec/ns-openvpn/openvpn-remote-auth via-env`.

#### Remote LDAP users with password and certificate

A client can connect to the server if:

- there is a valid certificate inside the certificate directory: the certificate CN must match the user name
- the user belongs to the database associated to the RoadWarrior instance
- the user `openvpn_enabled` field is set to `1` inside `users` database
- the user password can authenticate against remote LDAP server with provided password

To enable this authentication the `user_pass_verify` option must be set to `/usr/libexec/ns-openvpn/openvpn-remote-auth via-env`.

### IP static lease

The IP lease is saved inside the `openvpn_ipaddr` field, in the `users` database.

See the `add-user` and `edit-user` APIs inside the [ns-api](../ns-api/#nsovpnrw) page.

### Disable a user

To disable a user, the `openvpn_enabled` fiels must be set to `0`.

See the `enable-user` and `disable-user` APIs inside the [ns-api](../ns-api/#nsovpnrw) page.

### Remove a user

See the `delete-user` API inside the [ns-api](../ns-api/#nsovpnrw) page.

### Accounting

Every client connection is tracked inside a SQLite database saved inside `/var/openvpn/<instance>/connections.db`.
The database is initialized as soon as the `instance` is up using the `init-connections-db` script.

As default, all logs are sent to `/var/log/messages`.

### Client configuration

The `ns-openvpnrw-print-client` can generate a valid `.ovpn` file with embedded certificates.
The generated configuration can be copied to any compatible client.

Execute:
```
ns-openvpnrw-print-client <instance> <user>
```

Example:
```
ns-openvpnrw-print-client ns_roadwarrior giacomo > giacomo.ovpn
```

To regenerate the user certificate:
```
ns-openvpnrw-regenerate <instance> <user> <expiration>
```

## OpenVPN tunnels

Tunnels are normal `openvpn` sections inside `/etc/config/openvpn`.

Network and firewall configuration:

- the network device is named `tun<tunnel_name>`
- the default zone for tunnel devices is named `openvpn`: this is a trusted zone,
  it will have access to `lan` and `wan` zones, it will be also accessible from `lan` zone

### Servers

Each tunnel server requires to configure an iroute for every local network which should be exposed to tunnel client.
The iroute is configured upon client connection using `/usr/libexec/ns-openvpn/connect-scripts/10-tunnel-iroute` script.

Each tunnel server must have the following configuration options:
```
option client_connect '"/usr/libexec/ns-openvpn/openvpn-connect <tunnel_name>"'
option client_disconnect '"/usr/libexec/ns-openvpn/openvpn-disconnect <tunnel_name>"'
```
