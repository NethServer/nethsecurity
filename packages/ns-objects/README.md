# ns-objects

This package manages the firewall objects and users.

# Users

## Databases

The `/etc/config/users` UCI configuration manage manages the configuration of user databases.
It implements 2 kind of database:

- local UCI database
- remote LDAP (OpenLDAP or Active Directory) database

A local database has:
- a name which is the UCI section name
- type set to `local`
- an optional `description` field

Example:
```
config local 'main'
	option description 'Local users database'
```

A remote ldap database has:
- a name which is the UCI section name
- type set to `ldap`
- an optional `description` field

It also has the following fields:
- `uri`: LDAP URI
- `tls_reqcert`: enable or disable certificate validation, see valid values for `TLS_REQCERT` inside [OpenLDAP documentation](https://www.openldap.org/doc/admin21/tls.html)
- `base_dn`: LDAP base DN
- `user_dn`: LDAP user DN; if not present, default is equal as `base_dn`
- `user_attr`: user attribute to identify the user; usually is `cn` for Active Directory and `uid` for OpenLDAP
- `user_cn`: user attribute that contains the user complete name
- `starttls`: can be `0` or `1`, if set to `1` enable StartTLS

OpenLDAP example:
```
config ldap 'ldap1'
	option description 'Remote OpenLDAP server'
	option uri 'ldaps://192.168.100.234'
	option tls_reqcert 'never'
	option base_dn 'dc=directory,dc=nh'
	option user_dn 'ou=People,dc=directory,dc=nh'
	option user_attr 'uid'
	option user_cn 'cn'
	option starttls '0'
	option schema 'rfc2307'
```

Active Directory example:
```
config ldap 'ad1'
	option description 'Remote AD server'
	option uri 'ldap://ad.nethserver.org'
	option tls_reqcert 'always'
	option base_dn 'dc=ad,dc=nethserver,dc=org'
	option user_dn 'cn=users,dc=ad,dc=nethserver,dc=org'
	option user_attr 'cn'
	option user_cn 'cn'
	option starttls '0'
	option schema 'ad'
```

## Users and groups

A user is a dynamic entity representing a user with all physical and virtual devices belonging to a person like PCs, mobile phones or VPN road warrior accesses.
The user can connect to local services like VPNs.

A group is a dynamic entity representing a list of users.

Users and groups are saved inside the `/etc/config/users` UCI configuration file with the following types:
- `user` for users
- `group` for groups

User and group objects are identified by a random section name, but they both contain:
- a field named `database` which is a reference to the associated database, like `main`
- a special field named `name` which must be unique inside the associated database

## Local users and groups

Local users and groups are the ones associated to a database of type `local`.

For local users, the `name` field must also meet the following requirements

- have a maximum length of 12 characters (nft set name must be 16 characters or less, 4 chars are reserved for future use)

The local `user` object can have the following non-mandatory options:

- `description`: a longer label for the user, like "Name Surname"
- `macaddr`: list of MAC addresses belonging to the user's devices
- `ipaddr`: list of IP addresses
- `domain`: list of DNS names resolved to IP address, each DNS name is a `domain` record inside the [`dhcp` database](https://openwrt.org/docs/guide-user/base-system/dhcp_configuration#hostnames)
- `host`: list of DHCP reservations resolved to IP addresses, each reservation is a `host` record inside the [`dhcp` database](https://openwrt.org/docs/guide-user/base-system/dhcp#static_leases)
- `password`: shadow password hash, shadow format: `$<alg>$<salt>$<hash>`, where `alg` is always set to `6` (SHA-512)
- `openvpn_ipaddr`: an OpenVPN RoadWarrior IP address reserved for the user
- `openvpn_enabled`: can be `0` or `1`, if set to `0` the user can't authenticate itself inside OpenVPN
- `openvpn_2fa`: it's a string containing the secret for OpenVPN OTP authentication

The local `group` object can have the following non-mandatory options:

- `description`: a longer label for the group, like "Tech people"
- `user`: a list of `user` objects

Example of local users:
```
config user 'ns_rand123'
	option name "goofy"
	option database "main"
	option description 'Goofy Doe'
	list macaddr '52:54:00:9d:3d:e5'
	list ipaddr '192.168.100.23'
	list domain 'ns_goofy_name'
	list host 'ns_goofy_pc'

config user 'ns_rand456'
	option name "Daisy"
	option database "main"
	option label "Daisy White"
	list ipaddr '192.168.100.22'
	list ipaddr '2001:db8:3333:4444:5555:6666:7777:8888'
```

Example of local user with OpenVPN access and a reserved IP:
```
config user
	option name "john"
	option database "main"
	option label "John Doe"
	option openvpn_ipaddr "10.10.10.22"
	option openvpn_enabled "1"
	option openvpn_2fa "3PGEK5B7RBSODTUW6KAQUMED7ZAJ4ZEJ"
	option password "$6$o5l7kWSclhvn5HM5$hRN60ONxiKnb1RZJP14M1oTXYICFS4G998tCasf04j7Gm60p5G9Jkmewqa0LKAcdWwiIijPwowSlA78wx/kP3Q=="
```

Example of a local group:
```
config group
	option name 'vip'
	option database "main"
	option description 'Very Important People'
	list user 'goofy'
	list user 'daisy'
```

## Remote users

Remote users and groups are the ones associated to a database of type `ldap`.
Each user represent a users inside a remote LDAP database.

The remote `user` object can have the following non-mandatory options:

- `macaddr`: list of MAC addresses belonging to the user's devices
- `ipaddr`: list of IP addresses
- `domain`: list of DNS names resolved to IP address, each DNS name is a `domain` record inside the [`dhcp` database](https://openwrt.org/docs/guide-user/base-system/dhcp_configuration#hostnames)
- `host`: list of DHCP reservations resolved to IP addresses, each reservation is a `host` record inside the [`dhcp` database](https://openwrt.org/docs/guide-user/base-system/dhcp#static_leases)
- `openvpn_ipaddr`: an OpenVPN RoadWarrior IP address reserved for the user
- `openvpn_enabled`: can be `0` or `1`, if set to `0` the user can't authenticate itself inside OpenVPN
- `openvpn_2fa`: it's a string containing the secret for OpenVPN OTP authentication

Example of a remote user with OpenVPN access and a reserved IP:
```
config user
	option name "john"
	option database "ldap1"
	option openvpn_ipaddr "10.10.10.22"
	option openvpn_enabled "1"
	option openvpn_2fa "3PGEK5B7RBSODTUW6KAQUMED7ZAJ4ZEJ"
```

# Hosts

Objects of type `host` are used only as labels inside the UI to display details on firewall rules source and destinations.
If the user changes the IP address of an host object, such change is not propagated to any configuration file.

Example of `/etc/config/objects`:
```
config host 'myhost'
	option description 'Myhost'
	list ipaddr '192.168.100.24'
```
