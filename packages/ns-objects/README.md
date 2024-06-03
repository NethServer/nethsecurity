# ns-objects

This package manages the firewall objects and users.

# Users

## Databases

The `/etc/config/users` UCI configuration manages the configuration of user databases.
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
- `user_attr`: user attribute to identify the user; usually is `cn` for Active Directory and `uid` for OpenLDAP; the `user_attr` is used to calculate
  the Distinct Name (DN) of the user by concatenating the `user_attr` with the `user_dn`
- `user_display_attr`: user attribute that contains the user display name
- `user_bind_dn`: if set, it takes precedence over `user_attr` and it's used to bind the user to the LDAP server.
  This field is mainly used for OpenVPN road warrior authentication.
  It accepts the `%u` placeholder that will be replaced with the user name. Note that the user name must exists inside the `users` database
  to make it work with OpenVPN authentication.
  Example: if user_bind_dn is set to `%u@domain.local` and the user name is `john`, there should be entry of user type inside users database like this:
  ```
  config user 'ns_ee00e667'
	option database 'ns7ad'
	option name 'john'
	option openvpn_enabled '1'
	option openvpn_2fa 'HWBPSTBYCOBGNYI4RIJVJPG3CGPEHPCK'
  ```
  Usage example for Active Directory: `%u@mydomain.local` or `mydomain\%u`
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
	option user_display_attr 'cn'
	option user_bind_dn ''
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
	option user_display_attr 'cn'
	option user_bind_dn '%u@nethserver.org'
	option starttls '0'
	option schema 'ad'
```

## Users

A user is a dynamic entity representing a user with all physical and virtual devices belonging to a person like PCs, mobile phones or VPN road warrior accesses.
The user can connect to local services like VPNs.

Users are saved inside the `/etc/config/users` UCI configuration file with the following types:
- `user` for users

User objects are identified by a random section name, but they both contain:
- a field named `database` which is a reference to the associated database, like `main`
- a special field named `name` which must be unique inside the associated database

## Local users

Local users are the ones associated to a database of type `local`.

For local users, the `name` field must also meet the following requirements

- have a maximum length of 12 characters (nft set name must be 16 characters or less, 4 chars are reserved for future use)

The local `user` object can have the following non-mandatory options:

- `description`: a longer label for the user, like "Name Surname"
- `password`: shadow password hash, shadow format: `$<alg>$<salt>$<hash>`, where `alg` is always set to `6` (SHA-512)
- `openvpn_ipaddr`: an OpenVPN RoadWarrior IP address reserved for the user
- `openvpn_enabled`: can be `0` or `1`, if set to `0` the user can't authenticate itself inside OpenVPN
- `openvpn_2fa`: it's a string containing the secret for OpenVPN OTP authentication

A user device identified by a MAC address can be associated to a user by creating ad DHCP reservation and adding the reservation to the user as a `host` record.


Example of local users:
```
config user 'ns_rand123'
	option name "goofy"
	option database "main"
	option description 'Goofy Doe'

config user 'ns_rand456'
	option name "Daisy"
	option database "main"
	option label "Daisy White"
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

## Remote users

Remote users are the ones associated to a database of type `ldap`.
Each user represent a users inside a remote LDAP database.

The remote `user` object can have the following non-mandatory options:

- `openvpn_ipaddr`: an OpenVPN RoadWarrior IP address reserved for the user
- `openvpn_enabled`: can be `0` or `1`, if set to `0` the user can't authenticate itself inside OpenVPN
- `openvpn_2fa`: it's a string containing the secret for OpenVPN OTP authentication

A user device identified by a MAC address can be associated to a user by creating ad DHCP reservation and adding the reservation to the user as a `host` record.

Example of a remote user with OpenVPN access and a reserved IP:
```
config user
	option name "john"
	option database "ldap1"
	option openvpn_ipaddr "10.10.10.22"
	option openvpn_enabled "1"
	option openvpn_2fa "3PGEK5B7RBSODTUW6KAQUMED7ZAJ4ZEJ"
```

# Host set

Objects of type `host` represent a set of IP addresses.
When used inside a firewall rule, the host set object is expanded to a list of IP addresses.

Host sets have a special field named `family` which can be `ipv4` or `ipv6`.

A singleton host set is a special host set with only one IP address.

Example of `/etc/config/objects` for IPv4:
```
config host 'myhost4'
	option name 'Myhost4'
	option family 'ipv4'
	list ipaddr '192.168.100.24'
	list ipaddr '192.168.1.0/24'
```

The `ipaddr` of an IPv4 host set can be:
- IPv4 address like `192.168.1.1`
- IPv4 CIDR network like `192.168.1.0/24`
- IPv4 range like `192.168.1.3-192.168.10`
- a dhcp reservation like `dhcp/ns_xxxyy`
- a domain name like `dhcp/ns_aaaabbb`
- a vpn user like `vpn/ns_uuuuu`, the user must have an `openvpn_ipaddr` field set

Example of `/etc/config/objects` for IPv6:
```
config host 'myhost6'
	option name 'Myhost6'
	option family 'ipv6'
	list ipaddr '2001:db8:3333:4444:5555:6666:7777:8888'
	list ipaddr '2001:db8:3333:4444:5555:6666:7777:8888'
```

The `ipaddr` of an IPv6 host set can be:
- IPv6 address like `2001:db8:3333:4444:5555:6666:7777:8888`
- IPv6 CIDR network like `2001:db8::/95`
- IPv6 range like `2001:db8:3333:4444:5555:6666:7777:8888-2001:db8:3333:4444:5555:6666:7777:8890`
- a domain name like `dhcp/ns_aaaabbb`

DHCP reservation and VPN users are not supported in IPv6 host sets because both reservations and VPN users are always translated to IPv4 addresses.

# Domain set

Objects of type `domain` represent a set of DNS names resolved to IP addresses.

Example of `/etc/config/objects`:
```
config domain 'myset'
	option name 'MySet'
	option family 'ipv4'
	option timeout '600'
	list domain 'www.nethsecurity.org'
	list domain 'www.nethserver.org'
```

The record can have the following fields:
- `name`: the name of the object, it can contains only ASCII alphanumeric characters, maximum length is 16 characters
- `family`: can be `ipv4` or `ipv6`
- `timeout`: the timeout in seconds for the DNS resolution, default is `600` seconds
- `domain`: a list of valid DNS names

When used inside a firewall rule, the `domain` object is expanded to a nft set.
Given the above example, the corresponding ipset inside `/etc/config/firewall` will be:
```
config ipset
	option name 'myset
	option family 'ipv4'
	option timeout '600'
	option counters '1'
	list match 'ip'
	option ns_link 'objects/myset'
```

The nft set is populated with the IP addresses resolved by dnsmasq.
Given the above example, the corresponding nft set inside `/etc/config/dhcp` will be:
```
config ipset
	list name 'myset'
	list domain 'www.nethsecurity.org'
	list domain 'www.nethserver.org'
	option table_family 'inet'
	option ns_link 'objects/myset'
```

# Rules and objects

Objects can be used inside:

- firewall rules
- port forwards (redirects)
- multiwan rules
- dpi rules and exceptions

Objects are referenced by rules usually using the `ns_src` and `ns_dst` fields.
Each field refers to an object inside a database, it has the following format: `<database_name>/<record_id>`.

Possible object types:

- host from `dhcp` db, usually a static lease
- domain from `dhcp` db, usually a domain name
- host set from `objects` db
- domain set from `objects` db

Not all object types can be used in all sections, for example an host set can't be used in a multiwan rule.

Like for `ns_service` field, the UI could allow to select a custom source (or destination) without an object: in this case the user can enter one or more IPs.

If `ns_src` or `ns_dst` is non-empty, the user can select only one existing object. When the API saves the rules, it automatically compiles all required standard fields (like `src_ip` and `dest_ip`): the rule is still a valid uci rule that can be edited also from command line. If the rule is modified from the UI, all standard fields will be overwritten.

Standard fields are updated when:
- a rule is created or modified
- a redirect is created or modified
- an object is created, modified or deleted

Known fw4 limitations:
1. A rule can only use one ipset for the source or destination, but not both.
2. Ipsets can only contain entries with the same timeout. Therefore, if an ipset contains entries with a timeout of 0, it cannot contain entries with a timeout of 600.
3. It's not possible to create a rule that matches "an ipaddress or a MAC address". 

## Firewall rules

Supported object types for firewall rules are:

- a static lease, a record of type `host` from `dhcp` db
- a dns name, a record of type `domain` from `dhcp` db
- an host set, a record of type `host` from `objects` db
- a domain set, a record of type `domain` from `objects` db
- a vpn user, a record of type `user` from `users` db with `openvpn_ipaddr`

Objects can be used inside the following fields:

- `ns_src`: the source object
- `ns_dst`: the destination object

Also the following rules apply:
- A rule can use either a list of IP addresses or a list of objects as the source or destination, but the two cannot be mixed.
- An object of type host/dhcp/dns can be used as the source or destination of a rule and will be expanded into a list of IP addresses.
- An object of type user can also be used as the source or destination of a rule and will be expanded into a list of IP addresses. 

Due to fw4 limitation (see number 1 above), to allow a rule that involves a user and a DNS host (e.g., goofy user cannot access my.site.org), the user must be represented as a list of IP addresses rather than an ipset.

Example of rule with host object inside `/etc/config/firewall`:
```
config rule 'r2'
    option name 'r2'
    option src '*'
    option dest 'lan'
    list dest_ip '1.2.3.4'
    option target 'ACCEPT'
    option ns_service 'ssh'
    option ns_src 'dhcp/d1'
    list src_ip '192.168.100.1'
    list proto 'tcp'
    list proto 'udp'
    option dest_port '22'
    option enabled '1'
    option log '0'
```

Example of host object inside `/etc/config/dhcp`:
```
config domain 'd1'
    option name 'test.name.org'
    option ip '192.168.100.1'
```

Example of rule with domain set object inside `/etc/config/firewall`:
```
config rule 'r3'
	option name 'r3'
	option src '*'
	option dest 'lan'
	option target 'ACCEPT'
	option ns_dst 'objects/myset'
	option ipset 'myset dst'
	list src_ip ''
```

Example of domain set object inside `/etc/config/objects`:
```
config domain 'myset'
	option name 'MySet'
	option family 'ipv4'
	option timeout '600'
	list domain 'www.nethsecurity.org'
	list domain 'www.nethserver.org'
```

The `ns_src` field can change different fields in the rule:

- if the object is a domain set: removes `src_ip`, add `ipset` with the name of the domain set and `src` as direction
- in all other cases: removes `ipset`, add `src_ip` with the list of IP addresses of the object

The `ns_dst` field can change different fields in the rule:

- if the object is a domain set: removes `dest_ip`, add `ipset` with the name of the domain set and `dst` as direction
- in all other cases: removes `ipset`, add `dest_ip` with the list of IP addresses of the object

## Port forwards

Objects can be used inside the following fields:

- `ns_src`: the source object, it is mapped to an ipset and can be used to limit the access to the port forward to a list of IP addresses
- `ns_dst`: the destination object

Supported object types depends on the field:

- `ns_src` can be any type of object
- `ns_dst` can be an object with only one IP address, like:
  - a static lease, a record of type `host` from `dhcp` db
  - a dns name, a record of type `domain` from `dhcp` db
  - a vpn user, a record of type `user` from `users` db with `openvpn_ipaddr`
  
Example of port forward with domain set object inside `/etc/config/firewall`:
```
config redirect 'ns_c708dacb'
        option src 'wan'
        option target 'DNAT'
        option dest_ip '5.6.7.8'
        option enabled '1'
        option log '0'
        option name 'pf1'
        option reflection '0'
        option src_dport '5566'
		option ns_src 'objects/myset'
        option ipset 'myset src_net'
        list proto 'tcp'
        list proto 'udp'
        option src_dip '10.10.0.221'
```

The `ns_src` field can be used as allow list for the port forward and can change different fields in the port forward:

- if the object is a domain set: delete existing ipset, add `ipset` field with the name of the domain set and sets also `src_net` as direction
- in all other cases: delete existing ipset, add an `ipset` with static entries and creates a new ipset with the name of the object and sets also `src_net` as direction

The `ns_dst` field can be any type of object except a domain set. It changes only the `dest_ip` in the port forward.
If the objects has a list of IP addresses, the `dest_ip` is set to the first element of the IP addresses list.

## Multiwan rules

Objects can be used inside the following fields:

- `ns_src`: the source object
- `ns_dst`: the destination object

Supported object types depends on the field:

- `ns_src` can be an object with only one IP address, like:

  - a static lease, a record of type `host` from `dhcp` db
  - a dns name, a record of type `domain` from `dhcp` db
  - a vpn user, a record of type `user` from `users` db with `openvpn_ipaddr`
  - a singleton host set, a record of type `host` from `objects` db with only one IP address

- `ns_dst` can be:

  - a domain set object, a record of type `domain` from `objects` db
  - a dns name, a record of type `domain` from `dhcp` db
  - a host set object, a record of type `host` from `objects` db
  - a vpn user, a record of type `user` from `users` db with `openvpn_ipaddr`
  - a singleton host set, a record of type `host` from `objects` db with only one IP address


Example of multiwan rule with domain set object inside `/etc/config/mwan3`:
```
config rule 'ns_r1'
	option label 'r1'
	option use_policy 'ns_default'
	option sticky '0'
	option proto 'tcp'
	option ns_src 'dhcp/ns_host1'
	option src_ip '1.2.3.4'
	option ipset 'myset'
	option ns_dst 'objects/myset'
```

## DPI rules and exceptions

DPI rules and exceptions can use the following object types:

- a static lease, a record of type `host` from `dhcp` db
- a dns name, a record of type `domain` from `dhcp` db
- a vpn user, a record of type `user` from `users` db with `openvpn_ipaddr`- host set from `objects` db
- an host set, a record of type `host` from `objects` db

See [ns-dpi](../ns-dpi/) package for more details.