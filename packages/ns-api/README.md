# ns-api

NethSecurity APIs for `rpcd`.

* TOC
{:toc}

List available APIs:
```
ubus -S list | grep '^ns.'
```

APIs can be called directly from ubus, like:
```
ubus -S call ns.talkers list '{"limit": 5}'
```
Or using `api-cli`:
```
api-cli ns.talkers list --data '{"limit": 5}'
```

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

### add-default-config

Configure netwok and firewall for Dedalo:
```
api-cli ns.dedalo add-default-config
```

Response example:
```json
{ "success": true }
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
      "used_bytes": "98972",
      "available_bytes": "840060"
    },
    "storage": {
      "/": {
        "used_bytes": 175554560,
        "available_bytes": 127582208
      },
      "/mnt/storage": {
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
- the `data` field should contains 3600 points
- each point is composed by an array o 2 element: first one is received bytes, second one is sent bytes

# Creating a new API

Conventions:
- all APIs must start with `ns.` prefix
- all APIs must read JSON object input from standard input
- all APIs must write a JSON object to standard output: JSON arrays should always be wrapped inside
  an object due to ubus limitations
- APIs should not commit changes to the configuration database: it's up to the user (or the UI) to commit them and restart the services

To add a new API, follow these steps:
1. create an executable file inside `/usr/libexec/rpcd/` directory, like `ns.example`, and restart rpcd
2. create an ACL JSON file inside `/usr/share/rpcd/acl.d`, like `ns.example.json`

APIs can be written using any available programming language.
In this example we are going to use python.

Example for `/usr/libexec/rpcd/ns.example`:
```python
#!/usr/bin/python3

#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Return the same message given as input parameter

import sys
import json

def say(param):
    res = ''
    try:
        # do something here
        ret = param
    finally:
        print(json.dumps({"result": ret}))

cmd = sys.argv[1]

if cmd == 'list':
    print(json.dumps({"say": {"message": "value"}}))
elif cmd == 'call' and sys.argv[2] == "say":
    args = json.loads(sys.stdin.read())
    param = args.get('message', 'myvalue')
    say(param)
```

Make the file executable and restart rpcd:
```
chmod a+x /usr/libexec/rpcd/ns.example
/etc/init.d/rpcd restart
```

Usage example:
```
# ubus -v call ns.example say '{"message": "hello world"}' | jq
{
  "result": "hello world"
}
```

Create the ACL file to enable RPC calls.
Example for `/usr/share/rpcd/acl.d/ns.example.json`:
```
{
  "example-reader": {
    "description": "Access say method",
    "write": {},
    "read": {
      "ubus": {
        "ns.example": [
          "say"
        ]
      }
    }
  }
}
```

Test the new API:
```
api-cli ns.example say --data '{"message": "hello world"}'
```

Scripts can also be tested by passing arguments to standard input.
Example:
```
echo '{"limit": 5 }' | /usr/libexec/rpcd/ns.talkers call list
```

References
- [RPCD](https://openwrt.org/docs/techref/rpcd)
- [JSONRPC](https://github.com/openwrt/luci/wiki/JsonRpcHowTo)
