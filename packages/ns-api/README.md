# ns-api

NethSecurity APIs for `rpcd`.

* TOC
{:toc}

## ns.talkers

### list

List top network talkers:
```
api-cli ns.talkers list --data '{"limit": 1}'
```

Response:
```json
{
  "talkers": [
    {
      "mac": "40:62:31:19:05:22",
      "totals": {
        "download": 21666,
        "upload": 483727,
        "packets": 643,
        "bandwidth": 16846.433333333334,
        "bandwiddh_h": "16.5 KB/s"
      },
      "apps": {
        "0.netify.unclassified": 0,
        "10334.netify.nethserver": 505393
      },
      "ip": "192.168.5.211",
      "host": "nethvoice.nethesis.it"
    }
  ]
}
```

## ns.firewall

### rules

List firewall rules in order:
```
api-cli ns.firewall rules
```

Response:
```json
{
  "rules": [
    {
      "name": "Allow-DHCP-Renew",
      "src": "wan",
      "proto": "udp",
      "dest_port": "68",
      "target": "ACCEPT",
      "family": "ipv4"
    },
    {
      "name": "Allow-Ping",
      "src": "wan",
      "proto": "icmp",
      "icmp_type": "echo-request",
      "family": "ipv4",
      "target": "ACCEPT"
    }
  ]
}
```

### list zones

List firewall zones:

```
api-cli ns.firewall list_zones
```

Response:

```json
{
  "ns_lan": {
    "name": "lan",
    "input": "ACCEPT",
    "output": "ACCEPT",
    "forward": "ACCEPT",
    "network": [
      "GREEN_1"
    ]
  },
  "ns_wan": {
    "name": "wan",
    "input": "REJECT",
    "output": "ACCEPT",
    "forward": "REJECT",
    "masq": "1",
    "mtu_fix": "1",
    "network": [
      "wan6",
      "RED_2",
      "RED_3",
      "RED_1"
    ]
  },
  "ns_guests": {
    "name": "guests",
    "input": "DROP",
    "forward": "DROP",
    "output": "ACCEPT"
  }
}

```

### list forwardings

List forwardings:

```
api-cli ns.firewall list_forwardings
```

Response:

```json
{
  "cfg06ad58": {
    "src": "lan",
    "dest": "wan"
  },
  "ns_guests2wan": {
    "src": "guests",
    "dest": "wan"
  },
  "ns_lan2guests": {
    "src": "lan",
    "dest": "guests"
  }
}


```

### create zone

Create zone:

```
api-cli ns.firewall create_zone --data '{"name": "cool_zone", "input": "DROP", "forward": "DROP", "traffic_to_wan": true, "forwards_to": [], "forwards_from": ["lan"]}'
```

Response:

```json
{
  "message": "success"
}
```

### edit zone

Edit zone:

```
api-cli ns.firewall edit_zone --data '{"name": "cool_zone", "input": "ACCEPT", "forward": "REJECT", "traffic_to_wan": false, "forwards_to": ["lan"], "forwards_from": ["guest"]}'
```

Response:

```json
{
  "message": "success"
}
```

### delete zone

Delete zone:

```
api-cli ns.firewall delete_zone --data '{"config_name": "cool_zone"}'
```

Response:

```json
{
  "message": "success"
}
```


## ns.dpireport

Lightsquid-like reports based on netifyd data streams.

### days

List available reports:
```
api-cli ns.dpireport days
```

Example:
```json
{
	"days": [
		[
			"2023",
			"06",
			"16"
		]
	]
}
```

Each array contains year, month and day.

### details

Get report details for a client in the given date:
```
api-cli ns.dpireport details --data '{"year": "2023", "month": "06", "day": "16", "client": "192.168.100.22"}'
```

Data not grouped by hour are a total for the whole day.

Example:
```json
{
  "hours": {
    "00": {
      "total": 4697332,
      "protocol": {
        "http/s": 4669084,
        "ntp": 2700,
        "icmp": 70
      },
      "application": {
        "unknown": 38955,
        "netify.nethserver": 41934,
        "netify.reverse-dns": 226,
      },
      "host": {
        "pool.ntp.org": 2700,
        "urlhaus.abuse.ch": 882992,
      }
    },
    ...
    },
    "11": {
      "total": 930002,
      "protocol": {
        "http/s": 923080,
        "netbios": 1614,
      },
      "application": {
        "netify.internal-network": 793,
        "netify.nethserver": 27024,
        "unknown": 21930,
      },
      "host": {
        "_http._tcp.local": 576,
        "sambafax___nethservice._ipp._tcp.local": 217
      }
    },
    ...
    "23": {}
  },
  "total": 119058259,
  "name": "server.test.org",
  "protocol": {
    "http/s": 74134684,
    "netbios": 29590,
    ...
  },
  "host": {
    "nethservice": 29590,
    "211.222.102.147.in-addr.arpa": 233,
    ...
  },
  "application": {
    "netify.internal-network": 13273,
     ...
  }
}
```

### summary

Retrive a traffic summary for the given day:
```
api-cli ns.dpireport summary --data '{"year": "2023", "month": "06", "day": "16"}'
```

The summary contains network traffic from multiple hosts.
Lists are sorted in descending order by the amount of traffic in bytes.
JSON structure:
- `client`" is an array containing sub-arrays, where each sub-array represents a client.
   The sub-array consists of two elements: the client's IP address and the corresponding amount of traffic in bytes.
- `hours` is an array containing sub-arrays representing each hour. Each sub-array consists of two elements: the hour (represented as a string)
   and the total amount of traffic in bytes during that hour. The main array always contains all 24 hours, from `00` to `23`.
- `total` indicates the overall total traffic count in bytes.
- `names` a mapping between the host addess and reverse DNS
- `protocol` is the top 10 list of protocols
- `application` is the top 10 list of all applications
- `host` is the top 10 list of target hosts


Example:
```json
{
  "total": 53431766455,
  "clients": [
    [
      "172.25.5.13",
      31861541373
    ],
    [
      "fe80::9451:4aff:fec4:42d3",
      924
    ],
    ...
  ],
  "hours": [
    [
      "00",
      148225512
    ],
    ...
    [
      "23",
      0
    ]
  ],
  "names": {
    "fe80::9528:c0f8:553e:14ae": "fe80::9528:c0f8:553e:14ae",
    "192.168.5.5": "filippo-v6.nethesis.it",
     ...
  },
  "protocol": [
    [
      "http/s",
      39098676979
    ],
    [
      "stun",
      4719233858
    ],
    ...
  ],
  "host": [
    [
      "f003.backblazeb2.com",
      12985715728
    ],
    [
      "191.meet.nethesis.it",
      4618635575
    ],
    ...
  ],
  "application": [
    [
      "netify.backblaze",
      30906291212
    ],
    [
      "netify.ubuntu",
      753625987
    ],
    ...
  ]
}
```

## ns.ovpntunnel

### add-server

Add a tunnel server with subnet topology:
```
api-cli ns.ovpntunnel add-server --data '{"name": "server1", "lport": "2001", "proto": "tcp-server", "topology": "subnet", "server": "10.96.84.0/24", "public_ip": ["1.2.3.4"], "locals": ["192.168.102.0/24"], "remotes": ["192.168.5.0/24"]}'
``` 

Add a tunnel server with p2p topology:
```
api-cli ns.ovpntunnel add-server --data '{"name": "server1", "lport": "2001", "proto": "udp", "topology": "p2p", "ifconfig": "10.96.83.1 10.96.83.2", "public_ip": ["192.168.122.49"], "locals": ["192.168.102.0/24"], "remotes": ["192.168.5.0/24"]}'
```

Response example:
```json
{ "section": "ns_server1" }
```

### import-client

Import a tunnel client from NS7 exported json file:
```
cat client.json | api-cli ns.ovpntunnel import-client --data -
```

### export-client

Export a tunnel client as NS7 json file:
```
api-cli ns.ovpntunnel export-client --data '{"name": "ns_server1"}'
```

Response example:
```json
{
  "name": "cns_server1",
  "type": "tunnel",
  "Mode": "routed",
  "status": "enabled",
  "Compression": "",
  "RemotePort": "2001",
  "RemoteHost": "192.168.122.49",
  "Digest": "",
  "Cipher": "",
  "Topology": "subnet",
  "Protocol": "tcp-client",
  "RemoteNetworks": "192.168.5.0/24",
  "AuthMode": "certificate",
  "Crt": "-----BEGI..."
}
```

## ns.smtp

### get

Return the SMTP configuration for `/etc/msmtp`:
```
api-cli ns.smtp get
```

Response example:
```json
{"host": "mail.oursite.example", "port": "465", "tls": "on", "tls_starttls": "off", "from": "%U@oursite.example", "syslog": "LOG_MAIL"}
```

### set

Configure SMTP options to send mail using a NS7 machine:
```
echo '{"host": "mail.nethserver.org", "port": 587, "auth": "on", "user": "myuser", "password": "Nethesis,1234", "tls": "on", "tls_starttls": "on", "from": "no-reply@nethserver.org", "syslog": "LOG_MAIL"}' | api-cli ns.smtp set --data -

```

The API accepts all [msmtp options](https://marlam.de/msmtp/msmtprc.txt) but always configure only the default account.
Any existing configuration will be overridden.

Response example:
```json
{"success": true}
```

### test

Send a test mail to the given address:
```
echo '{"to": "giacomo@myserver.org"}' | api-cli ns.smtp test --data -
```

Response example:
```json
{"success": true}
```

## ns.templates

See [templates database](../../templates_database) for more info.

### list

Return the list of all templates from `/etc/config/templates` database:
```
api-cli ns.templates list
```

Response example:
```json
{
  "templates": {
    "ip6_dhcp": {
      "name": "Allow-DHCPv6",
      "src": "wan",
      "proto": "udp",
      "dest_port": "546",
      "family": "ipv6",
      "target": "ACCEPT"
    },
}
```

### add-ipv6-rules

Create all basic IPv6 rules. Return the list of created sections:
```
api-cli ns.templates add-ipv6-rules
```

Response example:
```json
["ns_93c53354", "ns_59669e47", "ns_a0340929", "ns_dd7bb722"]
```

### is-ipv6-enabled

Check if there are devices or network interfaces with IPv6 enabled:
```
api-cli ns.templates is-ipv6-enabled
```

Response example:
```json
{"enabled": true}
```

### disable-ipv6-firewall

Disable all rules, forwardings, redirects, zones and ipsets for ipv6-only family:
```
api-cli ns.templates disable-ipv6-firewall
```

Response example, a list of disabled sections:
```json
{"sections": ["ns_3cb45d88", "ns_5c877052", "ns_61615098", "ns_ba392633"]}
```

### disable-linked-rules

Disable all rules matching the given link:
```
api-cli ns.templates disable-linked-rules --data '{"link": "dedalo/config"}'
```

Response example, a list of disabled rules:
```json
{"rules": ["ns_3cb45d88", "ns_5c877052", "ns_61615098", "ns_ba392633"]}
```

### delete-linked-sections

Delete all sections matching the given link:
```
api-cli ns.templates delete-linked-sections --data '{"link": "dedalo/config"}'
```

Response example, a list of deleted sections:
```json
{"sections": ["ns_3cb45d88", "ns_5c877052", "ns_61615098", "ns_ba392633"]}
```

### add-service-group

Create all rules for the given service group:
```
api-cli ns.templates add-service-group --data '{"name": "ns_remote_admin", "src": "lan", "dest": "wan"}'
```

Response example:
```json
{"sections": ["ns_11a7ea5c", "ns_075979e2"]}
```


### add-guest-zone

Create the guest zone. Please note that the network interface must already exists inside the `network` database:
```
api-cli ns.templates add-guest-zone --data '{"network": "guest"}'
```

Response:
```json
{"zone": "ns_6d44f2a7", "forwardings": ["ns_c307fd13", "ns_9a15bb1d"]}
```

## ns.ovpnrw

Manage OpenVPN Road Warrior server.

### add-default-instance

Create basic instance with network and firewall configuration:
```
api-cli ns.ovpnrw add-default-instance
```

Response example:
```json
{ "success": true }
```

## ns.dedalo

Manage Dedalo hotspot

### list-sessions

List hotspot client sessions
```
api-cli ns.dedalo list-sessions
```

Response example:
```json
{
  "sessions": [
    {
      "macAddress": "00:11:22:33:44:",
      "ipAddress": "1.2.3.4",
      "status": "authenticated",
      "sessionKey": "000000111111000",
      "sessionTimeElapsed": 1456,
      "idleTimeElapsed": 43,
      "inputOctetsDownloaded": 6790,
      "outputOctetsUploaded": 1230
    },
    {
      "macAddress": "00:aa:bb:11:44:",
      "ipAddress": "192.168.100.231",
      "status": "not authenticated",
      "sessionKey": "145646000000111111000",
      "sessionTimeElapsed": 67841,
      "idleTimeElapsed": 2,
      "inputOctetsDownloaded": 98563,
      "outputOctetsUploaded": 11867
    }
  ]
}
```

### list-parents

List hotspot parents from remote hotspot manager:
```
api-cli ns.dedalo list-parents
```

Response example:
```json
{
  "parents": [
    {
      "id": 1746,
      "name": "nethsecurityng",
      "description": "NethSecurity dev"
    }
  ]
}
```

### list-devices

List available newtork devices:
```
api-cli ns.dedalo list-devices
```

Response example:
```json
{
  "devices": [
    "eth3",
    "eth4"
  ]
}
```

### login

Login to remote hotspot manager:
```
api-cli ns.dedalo login --data '{"host": "my.nethspot.com", "username": "myuser", "password": "mypass"}'
```

Successful response example:
```json
{ "result": "success" }
```

Error response example:
```json
{ "error": "login_failed" }
```

### unregister

Logout from remote hotspot manager and delete local config:
```
api-cli ns.dedalo unregister
```

Response example:
```json
{ "result": "success" }
```

### set-configuration

Configure the hotspot:
```
api-cli ns.dedalo set-configuration --data '{"network": "192.168.182.0/24", "hotspot_id": "1234", "unit_name": "myunit", "unit_description": "my epic unit", "interface": "eth3", "max_clients": 253, "dhcp_start": "192.168.182.10", "dhcp_end": "192.168.182.100"}'
```

Response example:
```json
{ "result": "success" }
```

### get-configuration

Get current configuration:
```
api-cli ns.dedalo get-configuration
```

Response example for non-configurated device:
```json
{
  "configuration": {
    "network": "192.168.182.0/24",
    "hotspot_id": "",
    "unit_name": "",
    "unit_description": "",
    "interface": "",
    "dhcp_start": "",
    "dhcp_end": "",
    "max_clients": "",
    "connected": true
  }
}
```

The `connected` field tells if the device is logged to the hotspot manager.
If the device is not connected, you need to execute the `login` api to retrieve remote data.

### get-dhcp-range

Return the first and last IPs valid for the DHCP range, given a network CIDR:
```
api-cli ns.dedalo get-dhcp-range --data '{"network": "10.0.0.0/24"}'
```

Response example:
```json
{
  "start": "192.168.0.2",
  "end": "192.168.255.254",
  "max_entries": 65533
}
```

If the network is not valid, the API raises a validation error:
```json
{
  "validation": {
    "errors": [
      {
        "parameter": "network",
        "message": "invalid_network",
        "value": "192.168.0.0/164"
      }
    ]
  }
}
```

The `max_entries` field is the maximum number of IPs available inside the network CIDR.

## ns.power

Reboot and shutdown the system

### reboot

Reboot:
```
api-cli ns.power reboot
```

Success response example:
```json
{ "result": "success" }
```

Error response example:
```json
{ "error": "command_failed" }
```

### poweroff

Shutdown:
```
api-cli ns.power poweroff
```

Success response example:
```json
{ "result": "success" }
```

Error response example:
```json
{ "error": "command_failed" }
```

## ns.routes

List and manage routes

### main-table

List routes from the main table:
```
api-cli ns.routes main-table --date '{"protocol": "ipv4"}'
```

The `protocol` field can be `ipv4 ` or `ipv6`.

IPv4 response example:
```json
{
  "table": [
    {
      "network": "default",
      "device": "eth3",
      "interface": "nat2",
      "gateway": "10.10.0.1",
      "metric": "",
      "protocol": "static"
    },
    {
      "network": "10.10.0.0/24",
      "device": "eth3",
      "interface": "nat2",
      "gateway": "",
      "metric": "",
      "protocol": "kernel"
    }
  ]
}
```

IPv6 response example:
```json
{
  "table": [
    {
      "network": "fe80::/64",
      "device": "ifb-dns",
      "interface": "ifb-dns",
      "gateway": "",
      "metric": 256,
      "protocol": "kernel"
    },
    {
      "network": "fe80::/64",
      "device": "eth1",
      "interface": "wan",
      "gateway": "",
      "metric": 256,
      "protocol": "kernel"
    }
  ]
}
```

### list-routes

List existing configured routes:
```
api-cli ns.routes list-routes --data '{"protocol": "ipv4"}'
```

The `protocol` field can be `ipv4 ` or `ipv6`.

IPv4 response example:
```json
{
  "routes": {
    "cfg07c8b4": {
      "target": "10.6.0.0/24",
      "gateway": "192.168.100.237",
      "metric": "0",
      "table": "main",
      "interface": "nat2",
      "type": "local",
      "mtu": "1500",
      "onlink": "1",
      "disabled": "0",
      "ns_description": ""
    },
    "cfg09c8b4": {
      "target": "192.168.4.0/24",
      "gateway": "192.168.100.1",
      "metric": "0",
      "table": "main",
      "interface": "",
      "type": "unicast",
      "mtu": "1500",
      "onlink": "0",
      "disabled": "1",
      "ns_description": ""
    }
  }
}
```

IPv6 response example:
```json
{
  "routes": {
    "cfg08df6a": {
      "target": "::/0",
      "gateway": "fe80::1",
      "metric": "0",
      "table": "main",
      "interface": "",
      "type": "local",
      "mtu": "1500",
      "onlink": "1",
      "disabled": "0",
      "ns_description": ""
    }
  }
}
```

### list-interfaces

List existing interfaces:
```
api-cli ns.routes list-interfaces
```

Response example:
```json
{
  "interfaces": [
    "loopback",
    "lan",
    "wan",
    "nat2"
  ]
}
```

### list-route-types

List route types:
```
api-cli ns.routes list-route-types
```

Response example:
```json
{
  "types": [
    "unicast",
    "local",
    "broadcast",
    "multicast",
    "unreachable",
    "prohibit",
    "blackhole",
    "anycast"
  ]
}
```

### add-route

Add a new IPv4 or IPv6 route:
```
api-cli ns.routes add-route --data '{"target": "192.168.4.0/24", "gateway": "192.168.100.1", "metric": "0", "table": "main", "interface": "", "type": "unicast", "mtu": "1500", "onlink": "0", "ns_description": "myroute2", "protocol": "ipv4"}'
```

The `protocol` field can be `ipv4 ` or `ipv6`.

Success response example, the id of the new route:
```json
{
  "id": "ns_0153cb52"
}
```

Error response example:
```json
{
  "id": null
}
```

### edit-route

Edit an existing route:
```
api-cli ns.routes edit-route --data '{"id": "ns_bc6a2749", "target": "192.168.7.0/24", "gateway": "192.168.100.1", "metric": "0", "table": "main", "interface": "lan", "type": "unicast", "mtu": "1501", "onlink": "1", "ns_description": "myroute2_edited"}'
```

Success response example, the id of the edited route:
```json
{
  "id": "ns_bc6a2749"
}
```

Error response example:
```json
{"error": "route_not_modified"}
```

### delete-route

Delete an existing route:
```
api-cli ns.routes delete-route --data '{"id": "ns_bc6a2749"}'
```

Success response example, the id of the deleted route:
```json
{
  "id": "ns_bc6a2749"
}
```

Error response example:
```json
{"error": "route_not_deleted"}
```

### enable-route

Enable an existing route:
```
api-cli ns.routes enable-route --data '{"id": "ns_bc6a2749"}'
```

Success response example, the id of the enabled route:
```json
{
  "id": "ns_bc6a2749"
}
```

Error response example:
```json
{"error": "route_not_enabled"}
```

### disable-route

Disable an existing route:
```
api-cli ns.routed disable-route --data '{"id": "ns_bc6a2749"}'
```

Success response example, the id of the disabled route:
```json
{
  "id": "ns_bc6a2749"
}
```

Error response example:
```json
{"error": "route_not_disabled"}
```

## ns.dashboard

Expose dashboard statistics.

### system-info

Retrive general system info:
```
api-cli ns.dashboard system-info
```

Response example:
```json
{
  "result": {
    "uptime": 8500.37,
    "load": [
      0.0205078125,
      0.00927734375,
      0
    ],
    "version": {
      "arch": "x86_64",
      "release": "NethSecurity 22.03.5"
    },
    "hostname": "NethSec",
    "hardware": "Standard PC (Q35 + ICH9, 2009)",
    "memory": {
      "used_bytes": 98972,
      "available_bytes": 840060
    },
    "storage": {
      "/": {
        "used_bytes": 175554560,
        "available_bytes": 127582208
      },
      "/mnt/data": {
        "used_bytes": 0,
        "available_bytes": 0
      },
      "tmpfs": {
        "used_bytes": 14372864,
        "available_bytes": 502484992
      }
    }
  }
}
```

### service-status

Retrive the status of a service:
```
api-cli ns.dashboard service-status --data '{"service": "internet"}'
```

Supported services are: `internet`, `banip`, `dedalo`, `netifyd`, `threat_shield_dns`, `adblock`, `threat_shield_ip`, `openvpn_rw`, `flashstart`, `mwan`

Valid return statuses are: `disabled`, `ok`, `error`, `warning`

Response example:
```json
{
  "result": {
    "status": "ok"
  }
}
```

### counter

Return a counter for the given service:
```
api-cli ns.dashboard counter --data '{"service": "hosts"}'
```

Supported services are:
- `hosts`: return the number of hosts as seen by ARP protocol

Response example:
```json
{
  "result": {
    "count": 3
  }
}
```

### traffic-interface

Return an array of point describing the network traffic in the last hour:
```
api-cli ns.dashboard interface-traffic --data  '{"interface": "eth0"}'
```

Response example (with only 3 points):
```json
{
  "result": {
    "labels": [
      1694438052,
      1694438050,
      1694438048
    ],
    "data": [
      [
        8.861697,
        5.850112
      ],
      [
        4.217272,
        3.222161
      ],
      [
        0.72875,
        0.399582
      ]
    ]
  }
}
```

Description of response:
- the `labels` field contains the timestamp of each point
- the `data` field should contains 180 points
- each point is composed by an array o 2 element: first one is received bytes, second one is sent bytes

### list-wans

List wan interfaces:
```
api-cli ns.dashboard list-wans
```

Response example:
```json
{
  "result": [
    {
      "iface": "wan",
      "device": "eth1"
    },
    {
      "iface": "nat2",
      "device": "eth3"
    }
  ]
}
```

## ns.subscription

Manage server subscription for [my.nethesis.it](https://my.nethesis.it) and [my.nethserver.com](https://my.nethserver.com).

### register

Register the machine to the remote server.
First, try to register an Enteprise subscription. If Enterprise subscription fails, try the Community one.
Example:
```
api-cli ns.subscription register --data '{"secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}'
```

Success response:
```json
{"result": "success"}
```

Error response:
```json
{"error": "invalid_secret_or_server_not_found"}
```

### unregister

Unregister the machine from the remote server:
```
api-cli ns.subscription unregister
```

Success response:
```json
{"result": "success"}
```

Error response:
```json
{"error": "unregister_failure"}
```

### info

Retrieve subscription information from remote server:
```
api-cli ns.subscription info
```

Success response:
```json
{
  "server_id": 5034,
  "systemd_id": "1af7701a-b2c5-4445-9718-e102c80aef55",
  "plan": "Trial Pizza",
  "expiration": 1697183326,
  "active": true
}
```

If the subscription does not expire, `expiration` is set to `0`.

Error response:
```json
{"error": "no_subscription_info_found"}
```

## ns.dhcp

Manage DHCPv4 servers and static leases.

### list-interfaces

List all interfaces where it is possible to enable a DHCPv4 server:
```
api-cli ns.dhcp list-interfaces
```

Response example:
```json
{
  "lan": {
    "device": "br-lan",
    "start": "",
    "end": "",
    "active": true,
    "options": {
      "leasetime": "12h",
      "gateway": "192.168.100.1",
      "domain": "nethserver.org",
      "dns": "1.1.1.1 8.8.8.8",
      "SIP ": "192.168.100.151"
    },
    "zone": "lan",
    "first": "192.168.100.2",
    "last": "192.168.100.150"
  },
  "blue": {
    "device": "eth2.1",
    "start": "",
    "end": "",
    "active": false,
    "options": {},
    "zone": ""
  }
}
```

### list-dhcp-options

List all supported DHCPv4 options:
```
api-cli ns.dhcp list-dhcp-options
```

These options can be used inside the `options` array for the `edit-interface` API.

Response example (just a part):
```json
{
  "netmask": "1",
  "time-offset": "2",
  "router": "3",
  "dns-server": "6",
  "log-server": "7",
  "lpr-server": "9",
  "boot-file-size": "13",
}
```

### get-interface

Get DHCPv4 configuration for the given interface:
```
api-cli ns.dhcp get-interface --data '{"interface": "lan"}'
```

Successfull response example:
```json
{
  "interface": "lan",
  "options": [
    {
      "gateway": "192.168.100.1"
    },
    {
      "domain": "nethserver.org"
    },
    {
      "dns": "1.1.1.1,8.8.8.8"
    },
    {
      "120": "192.168.100.151"
    }
  ],
  "first": "192.168.100.2",
  "last": "192.168.100.150",
  "leasetime": "12h",
  "active": true
}
```

Each element of the `options` array is a key-value object.
The key is the DHCP option name or number, the value is the option value.
Multiple values can be comma-separated.

Error response example:
```json
{"error": "interface_not_found"}
```

### edit-interface

Change or add the DHCPv4 configuration for a given interface:
```
api-cli ns.dhcp edit-interface --data '{"interface":"lan","first":"192.168.100.2","last":"192.168.100.150","active":true,"leasetime": "12h","options":[{"gateway":"192.168.100.1"},{"domain":"nethserver.org"},{"dns":"1.1.1.1,8.8.8.8"},{"120":"192.168.100.151"}]}'
```

See [ns.dhcp get-interface][#get-interface] for the `options` array format.

Successfull response:
```json
{"interface": "lan"}
```

Error response example:
```json
{"error": "interface_not_found"}
```

### list-active-leases

List active DHCPv4 leases:
```
api-cli ns.dhcp list-active-leases
```

Response example:
```json
{
  "leases": [
    {
      "timestamp": "1694779698",
      "macaddr": "62:2b:d7:6d:69:3d",
      "ipaddr": "192.168.5.138",
      "hostname": "",
      "interface": "blue",
      "device": "eth2.1"
    },
    {
      "timestamp": "1694779311",
      "macaddr": "2c:ea:7f:ff:03:35",
      "ipaddr": "192.168.5.38",
      "hostname": "xps9500",
      "interface": "blue",
      "device": "eth2.1"
    }
}
```

### list-static-leases

List configured static DHCPv4 leases:
```
api-cli ns.dhcp list-static-leases
```

Response example:
```json
{
  "leases": [
    {
      "lease": "ns_lease1",
      "macaddr": "80:5e:c0:7b:06:a1",
      "ipaddr": "192.168.5.220",
      "hostname": "W80B-2",
      "interface": "blue",
      "device": "eth2.1"
    },
    {
      "lease": "ns_lease2",
      "macaddr": "80:5e:c0:d9:c5:eb",
      "ipaddr": "192.168.5.162",
      "hostname": "W90B-1",
      "interface": "blue",
      "device": "eth2.1"
    }
  ]
}
```

The `lease` field contains the lease id which can be used to retrive the lease configuration.

### get-static-lease

Get a static lease:
```
api-cli ns.dhcp get-static-lease --data '{"lease": "ns_mylease"}'
```

Successfull response example:
```json
{
  "hostname": "myhost",
  "ipaddr": "192.168.100.22",
  "macaddr": "80:5e:c0:d9:c6:9b",
  "description": "my desc"
}
```

Error response example:
```json
{"error": "lease_not_found"}
```

### delete-static-lease

Delete a static lease:
```
api-cli ns.dhcp get-static-lease --data '{"lease": "ns_mylease"}'
```

Successfull response example:
```json
{"lease": "ns_d5facd89"}
```

Error response example:
```json
{"error": "lease_not_found"}
```

### add-static-lease

Add static lease:
```
api-cli ns.dhcp add-static-lease --data '{"ipaddr": "192.168.100.22", "macaddr": "80:5e:c0:d9:c6:9b", "hostname": "myhost", "description": "my desc"}'
```

Successfull response example:
```json
{"lease": "ns_d5facd89"}
```

If the mac address has already a reservation, a validation error is returned:
```
{
  "validation": {
    "errors": [
      {
        "parameter": "mac",
        "message": "mac_already_reserved",
        "value": "80:5e:c0:d9:c6:9b"
      }
    ]
  }
}
```

### edit-static-lease

Edit static lease:
```
api-cli ns.dhcp edit-static-lease --data '{"lease": "ns_d5facd89", "ipaddr": "192.168.100.22", "macaddr": "80:5e:c0:d9:c6:9b", "hostname": "myhost", "description": "my desc"}'
```

Successfull response example:
```json
{"lease": "ns_d5facd89"}
```

Error response example:
```json
{"error": "lease_not_found"}
```

This API can also raise a validation error like the `add-static-lease` API.

## ns.dns

Manage global DNS configuration and DNS records.

### list-records

List DNS records:
```
api-cli ns.dns list-records
```

Response example:
```json
{
  "records": [
    {
      "record": "cfg0af37d",
      "ip": "1.2.3.4",
      "name": "host1.nethesis.it",
      "description": ""
      "wildcard": true
    }
  ]
}
```

The `record` field is the id of the DNS record.

### get-record

Retrieve the given record by id:
```
api-cli ns.dns get-record --data '{"record": "cfg0af37d"}'
```

Response example:
```json
{
  "name": "host1.nethesis.it",
  "ip": "1.2.3.4",
  "description": "",
  "wildcard": false
}
```

### add-record

Add a DNS record:
```
api-cli ns.dns add-record --data '{"name": "www.example.org", "ip": "192.168.100.2", "description": "My record", "wildcard": true}'
```

Successful response example:
```json
{"record": "my_record"}
```

### edit-record

Edit a DNS record:
```
api-cli ns.dns edit-record --data '{"record": "cfg0af37d", "name": "www.example.org", "ip": "192.168.100.2", "description": "My record", "wildcard": false}'
```

Successful response example:
```json
{"record": "my_record"}
```

Error response example:
```json
{"error": "record_not_found"}
```

### delete-record

Delete a DNS record:
```
api-cli ns.dns delete-record --data '{"record": "cfg0af37d"}'
```

Successful response example:
```json
{"record": "my_record"}
```

Error response example:
```json
{"error": "record_not_found"}
```

### get-config

Get DNS general configuration:
```
api-cli ns.dns get-config
```

Response example:
```json
{
  "domain": "lan",
  "logqueries": true,
  "server": [
    "8.8.7.7"
  ]
}
```

### set-config

Set DNS general configuration:
```
api-cli ns.dns set-config --data '{"domain": "lan", "logqueries": true, "server": ["8.8.8.8"], ["1.1.1"]]}''
```

Response example:
```json
{"server": "cfg01411c"}
```

## ns-don

Manage remote support sessions using `don` client.

### start

Start a support session:
```
api-cli ns.don start
```
The action can take a few seconds.

Response example:
```json
{
  "server_id": "Axxxxxxx-5xxx-4xx6-8xx4-481xxxxxxxx0",
  "session_id": "bff8736a-c593-40ed-af90-10faa01abaf9"
}
```

### stop

Stop a support session:
```
api-cli ns.don stop
```
The action can take a few seconds.

Response example:
```json
{
  "result": "success"
}
```

### status

Retrieve info on don status:
```
api-cli ns.don status
```

Response example if don is running:
```json
{
  "server_id": "Axxxxxxx-5xxx-4xx6-8xx4-481xxxxxxxx0",
  "session_id": "bff8736a-c593-40ed-af90-10faa01abaf9"
}
```

Response example if don is not running:
```json
{
  "result": "no_session"
}
```

## ns.redirects

Manage redirects (port forwards).

### list-redirects

List existing redirects:
```
api-cli ns.redirects list-redirects
```

Response example:
```json
{
  "redirects": {
    "192.168.1.250": [
      {
        "dest_ip": "192.168.1.250",
        "protocol": [
          "tcp",
          "udp",
          "icmp"
        ],
        "source_port": "587",
        "source_port_name": "submission",
        "destination_port": "587",
        "dest": "lan",
        "name": "Submission mail",
        "wan": "1.2.3.4",
        "enabled": true,
        "id": "ns_pf1",
        "restrict": [],
        "log": true,
        "reflection": true,
        "reflection_zone": [
          "lan",
          "wan"
        ]
      },
      {
        "dest_ip": "192.168.1.250",
        "protocol": [
          "tcp"
        ],
        "source_port": "143",
        "source_port_name": "imap2",
        "destination_port": "143",
        "dest": "lan",
        "name": "IMAP on mail server",
        "wan": "1.2.3.5",
        "enabled": true,
        "id": "ns_pf2",
        "restrict": [
            "6.7.8.9"
        ],
        "log": false,
        "reflection": false
      }
    ]
  }
}
```

Redirects are grouped by destination (`dest_ip`).
The `id` field can be used to edit or delete the record.

### enable-redirect

Enable the redirect rule and associated ipset (if any):
```
api-cli ns.redirects enable-redirect --data '{"id": "ns_pf40"}'
```

Success response:
```json
{
  "id": "ns_pf40"
}
```
### disable-redirect

Disable the redirect rule and associated ipset (if any):
```
api-cli ns.redirects disable-redirect --data '{"id": "ns_pf40"}'
```

Success response:
```json
{
  "id": "ns_pf40"
}
```

### delete-redirect

Delete the redirect rule and associated ipset (if any):
```
api-cli ns.redirects delete-redirect --data '{"id": "ns_pf40"}'
```

Success response:
```json
{
  "id": "ns_pf40"
}
```

Error response:
```json
{
  "error": "redirect_not_found"
}
```

### add-redirect

Add a redirect rule:
```
api-cli ns.redirects add-redirect --data '{"name": "my pf", "dest_ip": "10.0.0.1", "proto": ["tcp"], "src_dport": "22", "reflection": "1", "log": "1",  "dest_port": "222", "restrict": ["1.2.3.4"], "src_dip": "4.5.6.7", "dest": "lan", "reflection_zone": ["lan", "guest"], "enabled": "1"}'
```

Fields description:
- `enabled`: `1` means enabled, `0` means disabled
- `name`: name of the port forward
- `dest_ip`: destination address
- `proto`: list of protocols
- `src_dport`: source port 
- `reflection`: hairpin nat flag, `1` means enabled, `0` means disabled
- `log`: `1` means enabled, `0` means disabled
- `dest_port`: destination port
- `src_dip`: WAN IP
- `restrict`: if it is not empty, the API will automatically create an associated ipset.
- `dest`: destination zone
- `reflection_zone`: list of hairpin NAT zones

Success response:
```json
{
  "id": "ns_pf40"
}
```

### edit-redirect

Edit a redirect rule:
```
api-cli ns.redirects edit-redirect --data '{"id": "ns_pf40", "name": "my pf", "dest_ip": "10.0.0.1", "proto": ["tcp"], "src_dport": "22", "reflection": "1", "log": "1",  "dest_port": "222", "restrict": [], "src_dip": "4.5.6.7", "enabled": "0"}'
```

Fields are the same as `add-redirect` API, plus the `id` field that identifies the rule.

### list-protocols

List supported protocols:
```
api-cli ns.redirects list-protocols
```

Response:
```json
{
  "protocols": [
    "tcp",
    "udp",
    "udplite",
    "icmp",
    "esp",
    "ah",
    "sctp",
    "all"
  ]
}
```

### list-wans

List interfaces inside the WAN zone:
```
api-cli ns.redirects list-wans
```

Response example:
```json
{
  "wans": [
    {
      "device": "eth1",
      "ipaddr": "192.168.122.49"
    },
    {
      "device": "eth1",
      "ipaddr": "fe80::5054:ff:fe20:82a6"
    }
  ]
}
```

### list-zones

List reflection zones:
```
api-cli ns.redirects list-zones
```

Response example:
```json
{
  "zones": [
    "guest"
  ]
}
```

## ns.dpi

Manage netifyd DPI engine.

### list-applications

List application and protocols:

```bash
api-cli ns.dpi list-applications
```

Filtering is provided out of the box, searching in both name and category:

```bash
api-cli ns.dpi list-applications --data '{"search": "apple"}'
```

Data can be limited and paginated by using the `limit` and `page` parameters:

```bash
api-cli ns.dpi list-applications --data '{"limit": 10, "page": 3}'
```

**PLEASE NOTE**: `category` field can be missing in some applications/protocols.

Example response:
```json
{
  "values": [
    {
      "id": 10392,
      "name": "netify.apple-siri",
      "type": "application",
      "category": {
        "id": 5,
        "name": "business"
      }
    },
    {
      "id": 10706,
      "name": "netify.apple-id",
      "type": "application"
    },
    {
      "id": 10152,
      "name": "netify.appnexus",
      "type": "application",
      "category": {
        "id": 3,
        "name": "advertiser"
      }
    },
    {
      "id": 142,
      "name": "WhatsApp",
      "type": "protocol",
      "category": {
        "id": 24,
        "name": "messaging"
      }
    },
    {
      "id": 238,
      "name": "Apple/Push",
      "type": "protocol"
    },
    {
      "id": 246,
      "name": "WhatsApp/Call",
      "type": "protocol",
      "category": {
        "id": 20,
        "name": "voip"
      }
    }
  ]
}
```

### list-rules

List created rules:

```bash
api-cli ns.dpi list-rules
```

Example response:

```json
{
  "values": [
    {
      "config-name": "ns_3869dc35",
      "enabled": true,
      "interface": "eth4",
      "action": "block",
      "criteria": [
        {
          "id": 156,
          "name": "netify.spotify",
          "type": "application",
          "category": {
            "id": 29,
            "name": "streaming-media"
          }
        },
        {
          "id": 10119,
          "name": "netify.adobe",
          "type": "application",
          "category": {
            "id": 5,
            "name": "business"
          }
        }
      ]
    },
    {
      "config-name": "ns_f1c6e9e0",
      "enabled": false,
      "interface": "eth4",
      "action": "block",
      "criteria": [
        {
          "id": 196,
          "name": "HTTP/S",
          "type": "protocol",
          "category": {
            "id": 22,
            "name": "web"
          }
        }
      ]
    }
  ]
}
```

### add-rule

Add DPI rule:

```bash
api-cli ns.dpi add-rule --data '{"enabled": false, "interface": "eth4", "applications": [], "protocols": ["HTTP/S"]}'
```

Rundown of required parameters:

- `enabled`: `true` or `false`
- `interface`: device name, e.g. `eth4`
- `applications`: list of application names, e.g. `["netify.spotify", "netify.adobe"]`, refer to `list-applications`
  api.
- `protocols`: list of protocol names, e.g. `["HTTP/S"]`, refer to `list-applications` api.

Example response:

```json
{
   "message": "success"
}
```

### delete-rule

Delete DPI rule:

```bash
api-cli nd.dpi delete-rule --data '{"config-name": "ns_f1c6e9e0"}'
```

Required parameters:

- `config-name`: rule name, refer to `list-rules` api.

Example response:

```json
{
   "message": "success"
}
```

### edit-rule

Edit DPI rule:

```bash
api-cli ns.dpi edit-rule --data '{"config-name": "ns_f1c6e9e0", "enabled": true, "interface": "eth4", "applications": ["netify.spotify", "netify.adobe"], "protocols": []}'
```

Rundown of required parameters:
- `config-name`: rule name, refer to `list-rules` api.
- `enabled`: `true` or `false`
- `interface`: device name, e.g. `eth4`
- `applications`: list of application names, e.g. `["netify.spotify", "netify.adobe"]`, refer to `list-applications`
  api.
- `protocols`: list of protocol names, e.g. `["HTTP/S"]`, refer to `list-applications` api.

Example response:

```json
{
   "message": "success"
}
```
