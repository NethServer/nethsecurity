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

- authentication based on certificate + otp
- mail notification about connect/disconnect events

Supported authentication methods:

- local users with certificate only
- local users with password
- local users with password and certificate
- remote LDAP users with password
- remote LDAP users with password and certificate

### First configuration

After installation, the OpenVPN roadwarrior instance is not configured.

You can enable it by invoking the `ns.ovpnrw`.`add-default-instance` API.
The API will:

- create a default OpenVPN roadwarrior server instance named `ns_roadwarrior`
- open the default `ns_roadwarrior` port (`1194/udp`) from the WAN zone
- create a `openvpnrw` trusted firewall zone which has access to LAN and WAN
- setup the PKI (Public Key Infrastructure) inside `/etc/openvpn/<instance>/pki` with `ns-openvpnrw-init-pki`
- create default firewall rules to access the `ns_roadwarrior` server from the WAN

On client connect, the server will execute all scripts inside `/usr/libexec/ns-openvpn/connect-scripts/` directory in lexicographical order.
On client disconnect, the server will execute all scripts inside `/usr/libexec/ns-openvpn/disconnect-scripts/` directory in lexicographical order.
Each script takes 2 arguments: the server instance name and the client CN.

Change from API are not commited.
To start the OpenVPN execute:
```
uci commit openvpn firewall network
service openvpn start
service network restart
service firewall restart
```

### Authentications methods

Each user must have an entry of type `user` inside `openvpn` UCI configuration file.
The entry name is also the name of the user. The name must be unique.

Database example of a user:
```
config user 'giacomo'
	option instance 'ns_roadwarrior'
	option ipaddr '10.9.9.70'
	option enabled '1'
```

Each user has the following options:

- `instance`: name of the OpenVPN instance, a user always belong to a single instance
- `enabled`: can be `0` or `1`, if set to `0` the user can't authenticate itself
- `ipaddr`: (optional) IP address reserved for the user
- `password`: (optional) password hash for local authenticated users

#### Local users with certificate only

A client can connect to the server if:

- there is a valid certificate inside with the same CN
- the user belongs to the `ns_roadwarrior` server instance and is marked as enabled inside `openvpn` database

Certificates are saved inside `/etc/openvpn/<instance>/pki/` directory.

Enable certificate authentication:
```
uci delete openvpn.ns_roadwarrior.auth_user_pass_verify
uci delete openvpn.ns_roadwarrior.verify_client_cert
uci delete openvpn.ns_roadwarrior.username_as_common_name
uci delete openvpn.ns_roadwarrior.script_security
uci commit openvpn
/etc/init.d/openvpn restart
```

To add a local user for certificate-only authentication use the `ns-openvpnrw-add` script.
The script will:

- create certificate and key of the user
- create a user entry inside the `openvpn` UCI database
- enable the user

Execute:
```
ns-openvpnrw-add <instance> <user>
```

Example:
```
ns-openvpnrw-add ns_roadwarrior giacomo
```

#### Local user with password

A client can connect to the server if:

- the user belongs to the `ns_roadwarrior` server instance and is marked as enabled inside `openvpn` database
- the provided user password matches the one saved inside `password` option

Enable user and password authentication:
```
uci set openvpn.ns_roadwarrior.auth_user_pass_verify='/usr/libexec/ns-openvpn/openvpn-local-auth via-env'
uci set openvpn.ns_roadwarrior.verify_client_cert=none
uci set openvpn.ns_roadwarrior.username_as_common_name=1
uci set openvpn.ns_roadwarrior.script_security=3
uci commit openvpn
/etc/init.d/openvpn restart
```

User passwords are saved inside UCI in passwd format `$<hash_method>$<salt>$<hash>`:
- `hash_method` is always set to `6`, which is `sha512`
- `salt` is a random ASCII string of 16 characters
- `hash` is a 86 characters hash calculated using `mkpasswd` command

Generate the user password:
```
salt=$(uuidgen | md5sum | cut -c 0-15)
echo -e '<password>' | mkpasswd -m sha512 -S "$salt"
```

Create a local user named `giacomo` with password `nethesis`:
```
ns-openvpnrw-add ns_roadwarrior giacomo
uci set openvpn.giacomo=user
uci set openvpn.giacomo.enabled=1
uci set openvpn.giacomo.instance=ns_roadwarrior
uci set openvpn.giacomo.password=$(echo -e 'nethesis' | mkpasswd -m sha512 -S "$(uuidgen | md5sum | cut -c 0-15)")
uci commit openvpn
```

#### Local users with password and certificate

A client can connect to the server if:

- there is a valid certificate inside with the same CN
- the user belongs to the `ns_roadwarrior` server instance and is marked as enabled inside `openvpn` database
- the provided user password matches the one saved inside `password` option

Enable user and password authentication:
```
uci set openvpn.ns_roadwarrior.auth_user_pass_verify='/usr/libexec/ns-openvpn/openvpn-local-auth via-env'
uci delete openvpn.ns_roadwarrior.verify_client_cert
uci delete openvpn.ns_roadwarrior.username_as_common_name
uci set openvpn.ns_roadwarrior.script_security=3
uci commit openvpn
/etc/init.d/openvpn restart
```

Create a local user named `giacomo` with password `nethesis` and certificate:
```
ns-openvpnrw-add ns_roadwarrior giacomo
uci set openvpn.giacomo.password=$(echo -e 'nethesis' | mkpasswd -m sha512 -S "$(uuidgen | md5sum | cut -c 0-15)")
uci commit openvpn
```

#### Remote LDAP users with password

A client can connect to the server if:

- the user belongs to the `ns_roadwarrior` server instance and is marked as enabled inside `openvpn` database
- the user password can authenticate against remote LDAP server with provided password

The LDAP configuration is saved to a `ldap` object inside `openvpn` UCI database with the following
options:
- `uri`: LDAP URI
- `tls_reqcert`: enable or disable certificate validation, see valid values for `TLS_REQCERT` inside [OpenLDAP documentation](https://www.openldap.org/doc/admin21/tls.html)
- `base_dn`: LDAP base DN
- `user_dn`: LDAP user DN; if not present, default is equal as `base_dn`
- `user_attr`: user attribute to identify the user; usually is `cn` for Active Directory and `uid` for OpenLDAP
- `starttls`: can be `0` or `1`, if set to `1` enable StartTLS
- `instance`: the name of OpenVPN instance associated to this configuration

Setup the connection to a remote NS7 LDAP and associate it to `ns_roadwarrior` instance:
```
uci set openvpn.ns_ldap1=ldap
uci set openvpn.ns_ldap1.uri=ldaps://192.168.100.234
uci set openvpn.ns_ldap1.tls_reqcert=never
uci set openvpn.ns_ldap1.base_dn=dc=directory,dc=nh
uci set openvpn.ns_ldap1.user_dn=ou=People,dc=directory,dc=nh
uci set openvpn.ns_ldap1.user_attr=uid
uci set openvpn.ns_ldap1.instance=ns_roadwarrior
uci commit openvpn
```

If the remote server is an Active Directory, use the following:
```
uci set openvpn.ns_ldap1=ldap
uci set openvpn.ns_ldap1.uri=ldaps://ad.nethserver.org
uci set openvpn.ns_ldap1.tls_reqcert=never
uci set openvpn.ns_ldap1.base_dn=dc=ad,dc=nethserver,dc=org
uci set openvpn.ns_ldap1.user_dn=cn=users,dc=ad,dc=nethserver,dc=org
uci set openvpn.ns_ldap1.user_attr=cn
uci set openvpn.ns_ldap1.instance=ns_roadwarrior
uci commit openvpn
```

Enable authentication against remote LDAP/AD:
```
uci set openvpn.ns_roadwarrior.auth_user_pass_verify='/usr/libexec/ns-openvpn/openvpn-remote-auth via-env'
uci set openvpn.ns_roadwarrior.verify_client_cert=none
uci set openvpn.ns_roadwarrior.username_as_common_name=1
uci set openvpn.ns_roadwarrior.script_security=3
uci commit openvpn
/etc/init.d/openvpn restart
```

Create and enable the user inside the local database:
```
uci set openvpn.giacomo=user
uci set openvpn.giacomo.enabled=1
uci set openvpn.giacomo.instance=ns_roadwarrior
uci commit openvpn
```

#### Remote LDAP users with password and certificate

A client can connect to the server if:

- there is a valid certificate inside with the same CN
- the user belongs to the `ns_roadwarrior` server instance and is marked as enabled inside `openvpn` database
- the user password can authenticate against remote LDAP server with provided password

First setup LDAP connection (see previous chapter), then enable authentication against remote LDAP/AD:
```
uci set openvpn.ns_roadwarrior.auth_user_pass_verify='/usr/libexec/ns-openvpn/openvpn-remote-auth via-env'
uci delete openvpn.ns_roadwarrior.verify_client_cert
uci delete openvpn.ns_roadwarrior.username_as_common_name
uci set openvpn.ns_roadwarrior.script_security=3
uci commit openvpn
/etc/init.d/openvpn restart
```

Create and enable the user inside the local database:
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

## OpenVPN tunnels

Tunnels are normal `openvpn` sections inside `/etc/config/openvpn`.
All tunnels are added the `openvpntun` trusted zone.

### Servers

Each tunnel server requires to configure an iroute for every local network which should be exposed to tunnel client.
The iroute is configured upon client connection using `/usr/libexec/ns-openvpn/connect-scripts/10-tunnel-iroute` script.

Each tunnel server must have the following configuration options:
```
option client_connect '"/usr/libexec/ns-openvpn/openvpn-connect <tunnel_name>"'
option client_disconnect '"/usr/libexec/ns-openvpn/openvpn-disconnect <tunnel_name>"'
```
