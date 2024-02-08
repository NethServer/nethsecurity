# ns-netmap

This package implements nft netmap rules not supported by fw4.

The configuration is saved inside `/etc/config/netmap`.
Each record must be of type `rule`.
Each rule can contains these fields:
- `name`: name identifying the rule, it must respect nft limitation for comments
- `src` (or `dest`): IPv4/IPv6 network address for source (or destination) NAT rule
- `device_in`: list of incoming network interfaces (optional)
- `device_out`: list of outgoing network interfaces (optional)
- `map_from`: IPv4/IPv6 network address for source address translation
- `map_to`:	IPv4/IPv6 network address for destination address translation

Example of configuration file:
```
config rule
	option name 'source_nat1'
	option dest '10.50.50.0/24'
	list device_in 'eth0'
	list device_in 'eth1'
	list device_out 'tunrw'
	option map_from '192.168.1.0/24'
	option map_to '192.168.57.0/24'

config rule
	option name 'dest_nat1'
	option src '10.50.50.0/24'
	option map_from '192.168.1.0/24'
	option map_to '192.168.57.0/24'
```

After adding a rule, execute the following commands to generate the rules:
```
uci commit netmap
ns-netmap
```
