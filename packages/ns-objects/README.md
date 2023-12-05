# ns-objects

This package manages the firewall objects.

Supported object types:
- `user`
- `group`
- `host`

All objects are saved inside the `/etc/config/objects` UCI database.

## Host

Objects of type `host` are used only as labels inside the UI to display details on firewall rules source and destinations.
If the user changes the IP address of an host object, such change is not propagated to any configuration file.

Example of `/etc/config/objects`:
```
config host 'myhost'
	option description 'Myhost'
	list ipaddr '192.168.100.24'
```
## Users

The `/etc/config/users` UCI configuration manage manages the configuration of user databases.
It implements 2 kind of database:

- local UCI database
- remote LDAP (OpenLDAP or Active Directory) database

## Local users and groups

A local user is a dynamic entity representing a user with all physical and virtual devices belonging to a person like PCs, mobile phones or VPN road warrior accesses.
The user can connect to local services like VPNs.

A local group is a dynamic entity representing a list of users.

Local users and groups are saved inside the `/etc/config/users` UCI configuration file with the following types:
- `local_user` for users
- `local_group` for groups

Usser and group objects are identified by a random section name, but they both contain a special field named `name`.

The `name` field is mandatory and must:

- be unique inside the local database
- be a valid UCI id (it may contain only the characters `a-z`, `0-9` and `_`)
- have a maximum length of 12 characters (nft set name must be 16 characters or less, 4 chars are reserved for future use)

The `local_user` object can have the following non-mandatory options:

- `description`: a longer label for the user, like "Name Surname"
- `macaddr`: list of MAC addresses belonging to the user's devices
- `ipaddr`: list of IP addresses
- `domain`: list of DNS names resolved to IP address, each DNS name is a `domain` record inside the [`dhcp` database](https://openwrt.org/docs/guide-user/base-system/dhcp_configuration#hostnames)
- `host`: list of DHCP reservations resolved to IP addresses, each reservation is a `host` record inside the [`dhcp` database](https://openwrt.org/docs/guide-user/base-system/dhcp#static_leases)
- `ovpn_ipaddr`: an OpenVPN Roadwarrior IP address reserved for the user
- `ovpn_enabled`: can be `0` or `1`, if set to `0` the user can't authenticate itself inside OpenVPN
- `password`: shadow password hash, shadow format: `$<alg>$<salt>$<hash>`

The `local_group` object can have the following non-mandatory options:

- `description`: a longer label for the group, like "Tech people"
- `user`: a list of `user` objects

Example of local users:
```
config local_user 'ns_rand123'
	option name "goofy"
	option description 'Goofy Doe'
	list macaddr '52:54:00:9d:3d:e5'
	list ipaddr '192.168.100.23'
	list domain 'ns_goofy_name'
	list host 'ns_goofy_pc'

config local_user
	option name "Daisy"
	option label "Daisy White"
	list ipaddr '192.168.100.22'
	list ipaddr '2001:db8:3333:4444:5555:6666:7777:8888'
```

Example of local user with OpenVPN access and a reserved IP:
```
config local_user
	option name "john"
	option label "John Doe"
	option ovpn_ipaddr "10.10.10.22"
	option ovpn_enabled "1"
	option password "$6$o5l7kWSclhvn5HM5$hRN60ONxiKnb1RZJP14M1oTXYICFS4G998tCasf04j7Gm60p5G9Jkmewqa0LKAcdWwiIijPwowSlA78wx/kP3Q=="
```

Example of a local group:
```
config local_group
	option name 'vip'
	option description 'Very Important People'
	list user 'goofy'
	list user 'daisy'```
```

## Remote LDAP database

The LDAP configuration is saved to a `ldap` object inside `/etc/config/users` UCI configuration file with the following
options:
- `uri`: LDAP URI
- `tls_reqcert`: enable or disable certificate validation, see valid values for `TLS_REQCERT` inside [OpenLDAP documentation](https://www.openldap.org/doc/admin21/tls.html)
- `base_dn`: LDAP base DN
- `user_dn`: LDAP user DN; if not present, default is equal as `base_dn`
- `user_attr`: user attribute to identify the user; usually is `cn` for Active Directory and `uid` for OpenLDAP
- `starttls`: can be `0` or `1`, if set to `1` enable StartTLS

Setup the connection to a remote NethServer 7 LDAP:
```
uci set users.ns_ldap1=ldap
uci set users.ns_ldap1.uri=ldaps://192.168.100.234
uci set users.ns_ldap1.tls_reqcert=never
uci set users.ns_ldap1.base_dn=dc=directory,dc=nh
uci set users.ns_ldap1.user_dn=ou=People,dc=directory,dc=nh
uci set users.ns_ldap1.user_attr=uid
uci commit users
```

If the remote server is an Active Directory, use the following:
```
uci set users.ns_ldap1=ldap
uci set users.ns_ldap1.uri=ldaps://ad.nethserver.org
uci set users.ns_ldap1.tls_reqcert=never
uci set users.ns_ldap1.base_dn=dc=ad,dc=nethserver,dc=org
uci set users.ns_ldap1.user_dn=cn=users,dc=ad,dc=nethserver,dc=org
uci set users.ns_ldap1.user_attr=cn
uci commit users
```

## Remote users

Remote users are saved inside the `/etc/config/users` UCI configuration file with the `remote_user` type.
Each user represent a users inside a remote LDAP database.

The following fields are mandatory for remote users:
- `ldap`: the name of the remote LDAP database
- `name`: the username of the remote user

The `remote_user` object can have the following non-mandatory options:

- `macaddr`: list of MAC addresses belonging to the user's devices
- `ipaddr`: list of IP addresses
- `domain`: list of DNS names resolved to IP address, each DNS name is a `domain` record inside the [`dhcp` database](https://openwrt.org/docs/guide-user/base-system/dhcp_configuration#hostnames)
- `host`: list of DHCP reservations resolved to IP addresses, each reservation is a `host` record inside the [`dhcp` database](https://openwrt.org/docs/guide-user/base-system/dhcp#static_leases)
- `ovpn_ipaddr`: an OpenVPN Roadwarrior IP address reserved for the user
- `ovpn_enabled`: can be `0` or `1`, if set to `0` the user can't authenticate itself inside OpenVPN


Example of a remote user with OpenVPN access and a reserved IP:
```
config remote_user
	option name "john"
	option ovpn_ipaddr "10.10.10.22"
	option ovpn_enabled "1"
	option ldap "ns_ldap1"
```
