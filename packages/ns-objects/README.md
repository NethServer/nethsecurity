# ns-objects

This package manages the firewall objects.

Supported object types:
- `user`
- `group`
- `host`

All objects are saved inside `/ect/config/objects` UCI database.

The `user` and `group` objects types can be used inside the abstract firewall UCI database named `/etc/config/absfirewall`.

## User and groups

A user is a dynamic entity representing all physical and devices belonging to a person like PCs, mobile phones or VPN road warrior accesses.
A group is a dynamic entity representing a list of users.

The `user` and `group` object are identified by the section name.
The section name must:

- be unique
- be a valid UCI id (it may contain only the characters `a-z`, `0-9` and `_`)
- have a maximum length of 14 characters (nft set name must be 16 characters or less, 4 chars are reserved by `abs2f2` to generate unique nft set names)

The `user` object can have the following non-mandatory options:

- `name`: name of user
- `description`: a longer label for the user
- `macaddr`: list of MAC address that will be resolved as IPs (see below)
- `ipaddr`: list of IP addresses
- `domain`: list of DNS names resolved to IP address, each DNS name is a `domain` record inside the [`dhcp` database](https://openwrt.org/docs/guide-user/base-system/dhcp_configuration#hostnames)
- `host`: list of DHCP reservations resolved to IP addresses, each reservation is a `host` record inside the [`dhcp` database](https://openwrt.org/docs/guide-user/base-system/dhcp#static_leases)
- `vpn`: list of VPN users with an IP reservation, each VPN user is a `user` record inside [`openvpn` database](https://nethserver.github.io/nextsecurity/packages/ns-openvpn/#authentications-methods)

The `group` object can have the following non-mandatory options:

- `name`: name of group
- `description`: a longer label for the group
- `user`: a list of `user` objects

Example of `/etc/config/objects`:
```
config user 'goofy'
	option name "Goofy"
	option description 'Goofy Doe'
	list macaddr '52:54:00:9d:3d:e5'
	list ipaddr '192.168.100.23'
	list domain 'ns_goofy_name'
	list host 'ns_goofy_pc'
	list vpn 'goofy'

config user 'daisy'
	option name "Daisy"
	list ipaddr '192.168.100.22'
	list ipaddr '2001:db8:3333:4444:5555:6666:7777:8888'

config group 'vip'
	option description 'Very Important People'
	list user 'goofy'
	list user 'daisy'
```

### Abstract firewall

The `absfirewall` configuration has the same syntax of `firewall` configuration but is also supports the following options inside the `rule` record:

- `user_src`: match incoming traffic from the specified user IPs
- `group_src`: match incoming traffic from the specified user group IPs

The abstract firewall must be converted to a standard firewall configuration using the `abs2f2` command. The command will:

- create all required IPv4 and IPv6 ipsets
- rewrite user/group based rules using the ipsets

MAC addresses listed inside the `macaddr` user option are converted to IPs at run-time using 2 daemons:

- `addrwatcher` exposes [addrwatch](https://github.com/fln/addrwatch) events to UNIX socket `/var/run/addrwatcher.sock` using `socat`
- `map2ip` reads ARP events from addrwatcher socket and dynamically adds the resolved IP to the existing ipsets

Rule example inside `absfirewall`:
```
config rule 'ns_test1'
	option name 'test-user-giacomo'
	option user_src 'giacomo'
	option proto 'udp'
	option dest_port '53'
	option target 'ACCEPT'
```

Apply configuration:
```
abs2fw > /var/etc/mac2ip.json
service mac2ip reload
fw4 restart
```

## Host

Objects of type `host` are used only as labels inside the UI to display details on firewall rules source and destinations.
This kind of objects can't be used inside `absfirewall` not `firewall` config: if the user changes the IP address of an host object, such
change is not propagated to any other configuration file.

Example of `/etc/config/objects`:
```
config host 'myhost'
	option description 'Myhost'
	list ipaddr '192.168.100.24'
```
