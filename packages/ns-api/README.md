# ns-api

NethSecurity APIs for `rpcd`.

* TOC
{:toc}

## ns.commit

This API will take care to commit all UCI changes. This is the workflow:

- pre-commit hook: run all executable scripts inside the /usr/libexec/ns-api/pre-commit directory
- commit UCI changes
- post-commit hook: run all executable scripts inside the /usr/libexec/ns-api/post-commit directory
- inform ubus about changes to apply them

Usage example:
```
api-cli ns.commit commit --data '{"changes":{"system":[["set","cfg01e48a","hostname","NethSec2"]]}}'
```

Successful response example:
```json
{"pre_errors": [], "post_errors": []}
```

The API will fail only if commit of UCI changes raises and error.
Even if one of the hooks script fail, the API will exit successfully (with exit status code 0) but 
the failed scripts will be added to the array below:
```json
{"pre_errors": ["/usr/libexec/ns-api/pre-commit/test.py", "/usr/libexec/ns-api/pre-commit/test_bash"], "post_errors": []}
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
  "talkers": {
    "top_hosts": [
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
    ],
    "top_apps": [
      {
        "name": "10974.netify.meta-cdn",
        "value": 149845562
      },
      {
        "name": "201.netify.instagram",
        "value": 63817984
      },
      {
        "name": "10334.netify.nethserver",
        "value": 31100837
      },
      {
        "name": "0.netify.unclassified",
        "value": 10138483
      },
      {
        "name": "126.netify.google",
        "value": 6314644
      },
      {
        "name": "119.netify.facebook",
        "value": 4381644
      },
      {
        "name": "10034.netify.hubspot",
        "value": 2430153
      },
      {
        "name": "156.netify.spotify",
        "value": 1139379
      },
      {
        "name": "10002.netify.github",
        "value": 1114048
      },
      {
        "name": "10041.netify.google-ads",
        "value": 791534
      }
    ],
    "top_protocols": [
      {
        "name": "QUIC",
        "value": 218488582
      },
      {
        "name": "HTTP/S",
        "value": 24080025
      },
      {
        "name": "STUN",
        "value": 21171007
      },
      {
        "name": "SYSLOG/S",
        "value": 5880696
      },
      {
        "name": "HTTP",
        "value": 2545062
      },
      {
        "name": "Unknown",
        "value": 851164
      },
      {
        "name": "SSH",
        "value": 684836
      },
      {
        "name": "WireGuard",
        "value": 600214
      },
      {
        "name": "TLS",
        "value": 507668
      },
      {
        "name": "OpenVPN",
        "value": 467074
      }
    ]
  }
}
```

## ns.firewall

### list-forward-rules

List forward rules in order:
```
api-cli ns.firewall list-forward-rules
```

Response:
```json
{
  "rules": [
    {
      "name": "r1",
      "dest": "wan",
      "dest_port": "22",
      "target": "ACCEPT",
      "src": "lan",
      "src_ip": [
        {
          "value": "192.168.100.1",
          "label": "test.name.org",
          "type": "domain"
        },
        {
          "value": "192.168.100.238",
          "label": null,
          "type": null
        }
      ],
      "dest_ip": [
        {
          "value": "192.168.122.1",
          "label": null,
          "type": null
        },
        {
          "value": "192.168.122.49",
          "label": null,
          "type": null
        }
      ],
      "log": true,
      "proto": [
        "tcp",
        "udp",
        "icmp"
      ],
      "id": "cfg1492bd",
      "index": 0,
      "system_rule": false,
      "ns_tag": [],
      "enabled": true,
      "ns_service": "ssh"
    }
  ]
}
```

### list-output-rules

List output rules in order:
```
api-cli ns.firewall list-output-rules
```

Response:
```json
{
  "rules": [
    {
      "name": "output1",
      "dest_ip": [
        {
          "value": "192.168.100.1",
          "label": "test.name.org",
          "type": "domain"
        }
      ],
      "target": "ACCEPT",
      "ns_service": "",
      "dest": "wan",
      "id": "cfg1592bd",
      "index": 0,
      "system_rule": false,
      "ns_tag": [],
      "src_ip": [],
      "proto": [
        "udp",
        "tcp"
      ],
      "log": false,
      "enabled": true
    },
    {
      "name": "output2",
      "src_ip": [
        {
          "value": "192.168.100.238",
          "label": null,
          "type": null
        }
      ],
      "dest": "lan",
      "dest_port": "45678",
      "target": "ACCEPT",
      "ns_service": "",
      "id": "cfg1692bd",
      "index": 1,
      "system_rule": false,
      "ns_tag": [],
      "dest_ip": [],
      "proto": [
        "udp",
        "tcp"
      ],
      "log": false,
      "enabled": true
    }
  ]
}
```

### list-input-rules

List input rules in order:
```
api-cli ns.firewall list-input-rules
```

Response:
```json
{
  "rules": [
    {
      "name": "Allow-Ping",
      "src": "wan",
      "proto": [
        "icmp"
      ],
      "icmp_type": "echo-request",
      "family": "ipv4",
      "target": "ACCEPT",
      "id": "ns_ping_wan",
      "index": 1,
      "system_rule": false,
      "ns_tag": [],
      "src_ip": [],
      "dest_ip": [],
      "log": false,
      "enabled": true
    },
    {
      "name": "Allow-ovpns1",
      "src": "wan",
      "dest_port": "1202",
      "proto": [
        "udp"
      ],
      "target": "ACCEPT",
      "ns_service": "",
      "enabled": false,
      "ns_link": "openvpn/ns_s1",
      "ns_tag": [
        "automated"
      ],
      "id": "ns_allow_ovpns1",
      "index": 3,
      "system_rule": true,
      "src_ip": [],
      "dest_ip": [],
      "log": false
    }
  ]
}
```


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
    "log": "1",
    "network": [
      "wan6",
      "RED_2",
      "RED_3",
      "RED_1"
    ]
  },
  "ns_guest": {
    "name": "guest",
    "input": "DROP",
    "forward": "DROP",
    "output": "ACCEPT"
  }
}
```

### list-service-suggestions

List all services from /etc/service:
```
api-cli ns.firewall list-service-suggestions
```

Response example:
```json
{
  "services": [
    {
      "id": "echo",
      "proto": [
        "tcp",
        "udp"
      ],
      "port": 7
    },
    {
      "id": "netstat",
      "proto": [
        "tcp"
      ],
      "port": 15
    }
  ]
}
```

### list-host-suggestions

List suggestions for hosts:
```
api-cli ns.firewall list-host-suggestions
```

Response:
```json
{
  "hosts": [
    {
      "value": "192.168.100.1",
      "label": "test.name.org",
      "type": "domain"
    },
    {
      "value": "192.168.100.2",
      "label": "test2.giacomo.org",
      "type": "host"
    },
    {
      "value": "192.168.100.238",
      "label": "lan",
      "type": "network"
    },
    {
      "value": "192.168.1.219",
      "label": "test2",
      "type": "lease"
    }
  ]
}
```

### list-object-suggestions

List suggestions for objects:
```
api-cli ns.firewall list-object-suggestions
```

Response:
```json
{
  "objects": [
    {
      "name": "myset",
      "family": "ipv4",
      "id": "ns_3cf75e0e",
      "singleton": false,
      "type": "host_set"
    },
    {
      "name": "MySet",
      "description": "Mydomain set",
      "family": "ipv4",
      "id": "myset",
      "type": "domain_set"
    },
    {
      "id": "users/ns_af3425ab",
      "name": "giacomo",
      "type": "vpn_user",
      "family": "ipv4"
    },
    {
      "id": "dhcp/ns_271ca281",
      "name": "reserve1",
      "type": "dhcp_static_lease",
      "family": "ipv4"
    },
    {
      "id": "dhcp/ns_9e7f705e",
      "name": "test1.domain",
      "type": "dns_record",
      "family": "ipv4"
    }
  ]
}
```

### add-rule

Add a rule:
```
api-cli ns.firewall add-rule '{"name": "r1", "src": "lan", "src_ip": [], "dest": "wan", "dest_ip": ["1.2.3.4"], "proto": [], "dest_port": ", "target": "ACCEPT", "ns_service": "ssh", "enabled": true, "log": false, "ns_tag": [], "add_to_top": false}'
```

Response example:
```json
{"id": "ns_206325d3"}
```

The `proto` and `dest_port` field will be validated and saved only if `ns_service` is set to `custom`.

Possible validation errors:
- `invalid_format` for `dest_ip` and `src_ip`
- `same_zone` is `src` is equal to `dest`
- `invalid_target` for `target`
- if `ns_service` is `custom`: `invalid_proto` for `proto` and `invalid_port` for `dest_port`
- if `ns_service` is not `cutom` or `*`: `invalid_service` for `ns_service

### edit-rule

Edit an existing rule:
```
api-cli ns.firewall edit-rule '{"id": "ns_206325d3", "name": "r1", "src": "lan", "src_ip": [], "dest": "wan", "dest_ip": ["1.2.3.4"], "proto": ["tcp"], "dest_port": "22", "target": "ACCEPT", "ns_service": "ssh", "enabled": true, "log": false, "ns_tag": []}'
```

Response example:
```json
{"id": "ns_206325d3"}
```

Possible validation errors:
- the same for add-rule
- `rule_does_not_exists` for `id`

### order-rules

Order a group of rules:
```
api-cli ns.firewall order-rule '{"type": "forward", "order": ["ns_e6f258a3", "ns_2be3a634", "cfg0f92bd"]}'
```

This API assumes that the /etc/config/firewall file is ordered using this schema:
- defaults and includes
- zones
- forwardings
- forward rules
- output rules
- input rules

The field `type` can have the following values:
- `forward`
- `input`
- `output`

The `order` field must contain all ids of the given type.

Reponse example:
```json
{"message": "success"}
```

It may rise the following validation errors:
- `invalid_rule_type` for `type`
- `invalid_order` if the `order` array does not contains all ids of rules for the given type

### delete-rule

Delete an existing rule:
```
api-cli ns.firewall delete-rule '{"id": "ns_206325d3"}'
```

Reponse example:
```json
{"message": "success"}
```

It may raise `rule_not_found` if the `id` is not found inside the `firewall` config.

### enable-rule

Enable an existing rule:
```
api-cli ns.firewall enable-rule '{"id": "ns_206325d3"}'
```

Reponse example:
```json
{"message": "success"}
```

It may raise `rule_not_found` if the `id` is not found inside the `firewall` config.

### disable-rule

Disable an existing rule:
```
api-cli ns.firewall disable-rule '{"id": "ns_206325d3"}'
```

Reponse example:
```json
{"message": "success"}
```

It may raise `rule_not_found` if the `id` is not found inside the `firewall` config.

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
  "ns_guest2wan": {
    "src": "guest",
    "dest": "wan"
  },
  "ns_lan2guest": {
    "src": "lan",
    "dest": "guest"
  }
}


```

### create zone

Create zone:

```
api-cli ns.firewall create_zone --data '{"name": "cool_zone", "input": "DROP", "forward": "DROP", "traffic_to_wan": true, "forwards_to": [], "forwards_from": ["lan"], "log": true}'
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
api-cli ns.firewall edit_zone --data '{"name": "cool_zone", "input": "ACCEPT", "forward": "REJECT", "traffic_to_wan": false, "forwards_to": ["lan"], "forwards_from": ["guest"], "log": false}'
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

### summary

Retrive a traffic summary for the given day:
```
api-cli ns.dpireport summary --data '{"year": "2023", "month": "06", "day": "16", "limit": 10}'
```

The `limit` field is optional and defaults to 10, it will limit the number of items in the `client`, `protocol`, `application` and `host` lists.
Elements exceeding the limit will be grouped in a single item called `others`.
If set to -1, all items will be returned.

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

### summary-by-client

Retrive a traffic summary for the given day limited to a single client (host on the local network):
```
api-cli ns.dpireport summary-by-client --data '{"year": "2023", "month": "06", "day": "16", "client": "192.168.2.2", "limit": 10}'
```

It has the same structure of the `summary` API.

### summary-v2

Improved version of the `summary` API, the api can accept the following parameters:

- year: the year of the report (default to the current year)
- month: the month of the report (default to the current month)
- day: the day of the report (default to the current day)
- client: filter data for the given client
- section: section to filter data (application, protocol, host)
- value: value to filter the previous section
- limit: limit the items returned in the lists (default to 20)

Example:

```
api-cli ns.dpireport summary-v2 --data '{"year": "2023", "month": "06", "day": "16", "limit": 10}'
```

Response:

```json
{
  "total_traffic": 16035446620,
  "hourly_traffic": [
    {
      "id": "00",
      "traffic": 120281002
    },
    {
      "id": "01",
      "traffic": 879624129
    },
    {
      "id": "02",
      "traffic": 127278297
    },
    {
      "id": "03",
      "traffic": 320193579
    }
  ],
  "clients": [
    {
      "id": "11.0.1.1",
      "label": "11.0.1.1",
      "traffic": 1962950942
    },
    {
      "id": "10.0.0.2",
      "label": "cool-PC",
      "traffic": 1413666916
    }
  ],
  "applications": [
    {
      "id": "unknown",
      "label": "Unknown",
      "traffic": 2148481014
    },
    {
      "id": "netify.google",
      "label": "Google",
      "traffic": 2012854079
    },
    {
      "id": "netify.youtube",
      "label": "Youtube",
      "traffic": 732979058
    }
  ],
  "remote_hosts": [
    {
      "id": "nethservice.nethesis.it",
      "traffic": 1142530419
    },
    {
      "id": "community.nethserver.org",
      "traffic": 389680308
    },
    {
      "id": "1d.tlu.dl.delivery.mp.microsoft.com",
      "traffic": 296533256
    }
  ],
  "protocols": [
    {
      "id": "http/s",
      "label": "HTTP/S",
      "traffic": 9277455653
    },
    {
      "id": "quic",
      "label": "QUIC",
      "traffic": 3638009875
    }
  ]
}
```

Note: the fields `applications`, `remote_hosts` and `protocols` will always be present if no section is specified. If 
a section is specified, the response will contain only the `clients`, `hourly_traffic` and `total_traffic` fields.

## ns.ovpntunnel

### list-tunnels

List existing tunnels:
```
api-cli ns.ovpntunnel list-tunnels
```

Response example:
```json
{
  "servers": [
    {
      "id": "ns_tunp2p",
      "ns_name": "mytun",
      "topology": "p2p",
      "enabled": true,
      "port": "1202",
      "local_network": [],
      "remote_network": [],
      "vpn_network": "10.87.32.1 - 10.87.32.2"
    },
    {
      "id": "ns_tunsubnet",
      "ns_name": "",
      "topology": "subnet",
      "enabled": true,
      "port": "1200",
      "local_network": [
        "192.168.100.0/24"
      ],
      "remote_network": [
        "192.168.200.0/24"
      ],
      "vpn_network": "10.36.125.0/24"
    }
  ],
  "clients": [
    {
      "ns_name": "clientsubent",
      "id": "ns_1234",
      "topology": "subnet",
      "enabled": true,
      "port": "1200",
      "remote_host": "185.96.130.33",
      "remote_network": []
    },
    {
      "ns_name": "c1",
      "id": "ns_333",
      "topology": "p2p",
      "enabled": true,
      "port": "1122",
      "remote_host": "1.2.3.4",
      "remote_network": [
        "10.0.1.0/24"
      ]
    }
  ]
}
```

### add-client

Add a tunnel client with subnet topology:
```
api-cli ns.ovpntunnel add-client --data '{"ns_name": "client", "port": "2001", "proto": "tcp", "dev_type": "tun", "remote": ["192.168.5.1"], "compress": "", "auth": "", "cipher": "", "certificate": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANxxxx\n-----END CERTIFICATE-----\n", "enabled": "1", "username": "myuser", "password": "mypass"}'
```

Add a tunnel client with p2p topology:
```
api-cli ns.ovpntun add-client --data '{"ns_name": "client", "port": "2001", "proto": "tcp", "dev_type": "tun", "remote": ["192.168.5.1"], "compress": "", "auth": "", "cipher": "", "secret": "#\n-----END OpenVPN Static key V1-----", "enabled": "1", "ifconfig_local": "10.0.0.1", "ifconfig_remote": "10.0.0.2", "route": ["192.168.78.0/24"]}'
```

The following fields are aoptionals:
- username
- password
- compress
- auth
- cipher

Response example:
```json
{ "id": "ns_client1" }
```

The `id` return by the response can be used to reference the tunnel inside other API calls.

### edit-client

Edit a tunnel client with subnet topology:
```
api-cli ns.ovpntunnel edit-client --data '{"id": "ns_client1", "ns_name": "client1", "port": "2001", "proto": "tcp", "dev_type": "tun", "remote": ["192.168.5.1"], "compress": "", "auth": "", "cipher": "", "certificate": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANxxxx\n-----END CERTIFICATE-----\n", "enabled": "1", "username": "myuser", "password": "mypass"}'
```

Edit a tunnel client with p2p topology:
```
api-cli ns.ovpntun edit-client --data '{"id": "ns_client1", "ns_name": "client1", "port": "2001", "proto": "tcp", "dev_type": "tun", "remote": ["192.168.5.1"], "compress": "", "auth": "", "cipher": "", "secret": "#\n-----END OpenVPN Static key V1-----", "enabled": "1", "ifconfig_local": "10.0.0.1", "ifconfig_remote": "10.0.0.2", "route": ["192.168.78.0/24"]}'
```

### add-server

Add a tunnel server with subnet topology:
```
api-cli ns.ovpntunnel add-server --data '{"ns_name": "server1", "port": "2001", "topology": "subnet", "proto": "tcp", "local": ["192.168.100.0/24"], "remote": ["192.168.5.0/24"], "compress": "", "auth": "", "cipher": "", "ns_public_ip": ["1.2.3.4"], "tls_version_min": "1.2", "server": "192.168.4.0/24"}'
``` 

Add a tunnel server with p2p topology:
```
api-cli ns.ovpntunnel add-server --data '{"ns_name": "server2", "port": "2003", "topology": "p2p", "proto": "tcp", "local": ["192.168.100.0/24"], "remote": ["192.168.5.0/24"], "secret": "#\n# 2048 bit OpenVPN static key\n#\n-----BEGIN OpenVPN Static key V1-----....----END OpenVPN Static key V1-----\n", "compress": "", "auth": "", "cipher": "", "ns_public_ip": ["1.2.3.4"], "tls_version_min": "1.2", "ifconfig_local": "192.168.3.1", "ifconfig_remote": "192.168.3.2"}'
```

Response example:
```json
{ id"": "ns_server1" }
```

### edit-server

Edit a tunnel server. The API takes the same object passed to the `add-client`, plus the `id` field:
```
api-cli ns.ovpntunnel edit-server --data '{"id": "ns_server1", "ns_name": "server1", "port": "2002", "topology": "subnet", "proto": "tcp", "local": ["192.168.100.0/24"], "remote": ["192.168.5.0/24"], "compress": "", "auth": "", "cipher": "", "ns_public_ip": ["1.2.3.4"], "tls_version_min": "1.2", "server": "192.168.4.0/24"}'
``` 

Response example:
```json
{ id"": "ns_server1" }
```

### get-tunnel-client

Get tunnel client configuration:
```
api-cli ns.ovpntunnel get-tunnel-client --data '{"id": "ns_502e84af"}'
```

Format returned is the same object passed to the `add-client`, plus the `id` field.

Response example:
```json
{
  "ns_name": "client1",
  "port": "2002",
  "remote": [
    "192.168.5.1"
  ],
  "proto": "udp",
  "dev_type": "tun",
  "enabled": "1",
  "route": [
    "192.168.78.0/24"
  ],
  "id": "ns_502e84af",
  "secret": "#\n-----END OpenVPN Static key V1-----",
  "ifconfig_local": "10.0.0.1",
  "ifconfig_remote": "10.0.0.2"
}
```

### get-tunnel-server

Get tunnel server configuration:
```
api-cli ns.ovpntunnel get-tunnel-server '{"id": "ns_502e84af"}'
```

Format returned is the same object passed to the `add-server`, plus the `id` field.

Response example:
```json
{
  "enabled": "1",
  "proto": "tcp",
  "topology": "p2p",
  "tls_version_min": "1.2",
  "ns_public_ip": [
    "1.2.3.4"
  ],
  "ns_name": "server2",
  "id": "ns_server2",
  "port": "2003",
  "secret": "#\n# 2048 bit OpenVPN............-----END OpenVPN Static key V1-----",
  "remote": [
    "192.168.5.0/24"
  ],
  "local": [
    "192.168.100.0/24"
  ],
  "ifconfig_local": "192.168.3.1",
  "ifconfig_remote": "192.168.3.2"
}
```

### import-client

Import a tunnel client from NS7 exported json file:
```
cat client.json | api-cli ns.ovpntunnel import-client --data -
```

### export-client

Export a tunnel client as NS7 json file:
```
api-cli ns.ovpntunnel export-client --data '{"id": "ns_server1"}'
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

### disable-tunnel

Disable the given tunnel:
```
api-cli ns.ovpntunnel disable-tunnel '{"id": "tun1"}'
```

It can raise a `tunnel_not_found` validation error.

Success response example:
```json
{"result": "success"}
```

Error response example:
```json
{"error": "tunnel_not_disabled"}
```

### enable-tunnel

Enable the given tunnel:
```
api-cli ns.ovpntunnel enable-tunnel '{"id": "tun1"}'
```

It can raise a `tunnel_not_found` validation error.

Success response example:
```json
{"result": "success"}
```

Error response example:
```json
{"error": "tunnel_not_enabled"}
```

### delete-tunnel

Disable the given tunnel:
```
api-cli ns.ovpntunnel delete-tunnel '{"id": "tun1"}'
```

It can raise a `tunnel_not_found` validation error.

Success response example:
```json
{"result": "success"}
```

Error response example:
```json
{"error": "tunnel_not_deleted"}
```

### list-cipher

List available ciphers:
```
api-cli ns.ovpntun list-cipher
```

The value of the `name` field can be used inside the `cipher` field of edit and add APIs.

Response example:
```json
{
  "ciphers": [
    {
      "name": "AES-128-CBC",
      "description": "weak"
    },
    {
      "name": "AES-128-CFB",
      "description": "weak"
    },
      "name": "AES-128-OFB",
      "description": "weak"
    },
    {
      "name": "AES-192-CBC",
      "description": "strong"
    }
  ]
}
```

### list-digest

List available digest:
```
api-cli ns.ovpntun list-digest
```

The value of the `name` field can be used inside the `auth` field of edit and add APIs.

Response example:
```json
{
  "digests": [
    {
      "name": "SHA3-224",
      "description": "strong"
    },
    {
      "name": "SHA512",
      "description": "strong"
    }
  ]
}
```

### get-defaults

Retrieve server defaults:
```
api-cli ns.ovpntun get-defaults
```

Response example:
```json
{
  "secret": "#\n# 2048 bit OpenVPN static key\n#\n-----BEGIN OpenVPN Static key V1-----\n...xxxxxx...\nEND OpenVPN Static key V1-----",
  "port": 1203,
  "server": "10.191.228.0/24",
  "ifconfig_local": "10.191.228.1",
  "ifconfig_remote": "10.191.228.2",
  "route": [
    "192.168.3.0/24",
    "192.168.6.0/24"
  ],
  "remote": [
    "1.2.3.4",
    "5.6.7.8"
  ]
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

## ns.ovpnrw

Manage OpenVPN Road Warrior server instances.

### list-instances

List existing instances:
```
api-cli ns.ovpnrw list-instances
```

Response example:
```json
{
  "instances": [
    "ns_roadwarrior1"
  ]
}
```
### add-instance

Create a new instance:
```
api-cli ns.ovpnrw add-instance
```

Response example:
```json
{"instance": "ns_roadwarrior2"}
```

### remove-instance

```
api-cli ns.ovpnrw remove-instance --data '{"instance": "ns_roadwarrior2"}'
```

Response example:
```json
{"result": "success"}
```

### get-configuration

Get current server configuration:
```
api-cli ns.ovpnrw get-configuration --data '{"instance": "ns_roadwarrior1"}'
```

Response example for a server in routed mode:
```json
{
  "proto": "udp",
  "port": "1194",
  "dev_type": "tun",
  "topology": "subnet",
  "enabled": "1",
  "client_to_client": "0",
  "auth": "SHA256",
  "cipher": "AES-256-GCM",
  "tls_version_min": "1.2",
  "ns_auth_mode": "certificate",
  "ns_bridge": "lan",
  "server": "192.168.101.0/24",
  "ifconfig_pool": ["192.169.101.50","192.169.101.254"],
  "ns_public_ip": [
    "192.168.100.238"
  ],
  "ns_redirect_gateway": "0",
  "ns_local": [
    "192.168.101.0/24",
    "192.168.100.0/24"
  ],
  "ns_dhcp_options": [],
  "ns_description": "Road Warrior 1"
}
```

Response example for a server in bridged mode:
```json
{
  "proto": "udp",
  "port": "1194",
  "dev_type": "tap",
  "topology": "subnet",
  "enabled": "1",
  "client_to_client": "0",
  "auth": "SHA256",
  "cipher": "AES-256-GCM",
  "tls_version_min": "1.2",
  "ns_auth_mode": "certificate",
  "ns_bridge": "lan",
  "ns_public_ip": [
    "192.168.100.238"
  ],
  "server": "",
  "ns_redirect_gateway": "0",
  "ns_local": [
    "192.168.100.0/24"
  ],
  "ns_dhcp_options": [
    {
      "option": "NBDD",
      "value": "1.2.3.4"
    }
  ],
  "ns_pool_start": "192.168.100.240",
  "ns_pool_end": "192.168.100.242",
  "ns_description": "Road Warrior 1"
}
```

After `add-instance`, the `ns_description` field is empty. If the field is empty, the instance has never been edited from UI.

### download_all_user_configuration

Prepare a tar.gz archive with all user configuration
```
api-cli ns.ovpnrw download_all_user_configurations --data '{"instance": "ns_roadwarrior1"}'
```

Response example:
```json
{
  "archive_path": "/var/run/ns-api-server/download/ns_roadwarrior1_user_configurations.tar.gz"
}
```

The archive can be download using `scp` or the files APIs of nethsecurtity-api-server

### list-users

List existing users with their status:
```
api-cli ns.ovpnrw list-users --data '{"instance": "ns_roadwarrior1"}'
```

Response example:
```json
{
  "users": [
    {
      "local": true,
      "database": "main",
      "name": "john",
      "password": "$6$3c955d30ce84091a$F385YlvQX44FJpNZ7CECB6gxrtKcv..rB5mnco9YMEicfLJ2EmVALg2I3t6xPaUxMCOzIDKhuzLhJPWYFNAuc.",
      "description": "John Doe",
      "openvpn_enabled": "1",
      "openvpn_ipaddr": "10.84.232.22",
      "openvpn_2fa": "ORWDWV66I4BHIWGT7CJLLCREFUS33BVZ",
      "admin": false,
      "id": "ns_d486faa0",
      "connected": false,
      "expiration": "",
      "expired": false
      "used": false,
      "matches": []
    },
    {
      "local": true,
      "database": "main",
      "name": "daisy",
      "password": "$6$3c955d30ce84091a$F385YlvQX44FJpNZ7CECB6gxrtKcvxxrB5mnco9YMEicfLJ2EmVALg2I3t6xPaUxMCOzIDKhuzLhJPWYFNAuc.",
      "description": "Daisy Doe",
      "openvpn_enabled": "1",
      "openvpn_2fa": "ORWDWV66I4BHIWGT7CJLLCREFUS33BVZ",
      "admin": false,
      "id": "ns_d486faa0",
      "connected": true,
      "real_address": "192.168.100.1",
      "virtual_address": "192.168.101.44",
      "bytes_received": "3703",
      "bytes_sent": "3091",
      "since": 1701701676,
      "expiration": 2012741635,
      "expired": false,
      "used": true,
      "matches": ["firewall/ns_allow_xx"]
    }
  ]
}
```

The following fields may not be present:
- `password`
- `ipaddr`

If `connected` field is `true`, the user object should contain also:
- `real_address`, the remote address
- `virtual_address`
- `bytes_received`
- `bytes_sent`
- `since`, connected since the given timestamp

The `used` field is `true` if the user has been used as firewall objects. The `matches` field contains the firewall objects where the user has been used.

### list-auth-modes

List authentication modes:
```
api-cli ns.ovpnrw list-auth-modes
```

Response example:
```json
{
  "options": [
    "username_password",
    "certificate",
    "username_password_certificate",
    "username_otp_certificate"
  ]
}
```

### list-cipher

List all available ciphers to be used inthe the `cipher` option:
```
api-cli ns.ovpnrw list-cipher
```

Response example:
```json
{
  "ciphers": [
    {
      "name": "AES-128-CBC",
      "description": "weak"
    }
  ]
}
```

### list-digest

List availalble digests to be used inside the `auth` option:
```
api-cli ns.ovpnrw list-digest
```

Response example:
```json
{
  "digests": [
    {
      "name": "SHA3-224",
      "description": "strong"
    }
  ]
}
```

### list-dhcp-options

List available DHCP options:
```
api-cli ns.ovpnrw list-dhcp-options
```

Response example:
```json
{
  "options": [
    "DNS",
    "WINS",
    "NBDD",
    "NBT",
    "NBS",
    "DISABLE-NBT"
  ]
}
```

### list-bridges

```
api-cli ns.ovpnrw list-bridges
```
Response example:
```json
{
  "bridges": [
    "lan"
  ]
}
```

### set-configuration

Configure a routed server:
```
api-cli ns.ovpnrw set-configuration --data '{"instance": "ns_roadwarrior1", "proto":"udp","port":"1194","dev_type":"tun","topology":"subnet","enabled":"1","client_to_client":"0","auth":"SHA256","cipher":"AES-256-GCM","tls_version_min":"1.2","ns_auth_mode":"certificate","ns_public_ip":["192.168.100.238"],"server":"192.168.101.0/24","ns_redirect_gateway":"0","ns_local":["192.168.22.0/24","192.168.100.0/24"],"ns_dhcp_options":[{"option": "NBDD", "value": "1.2.3.4"}],"ns_pool_start":"","ns_pool_end":"","ns_bridge":"", "ns_description": "Road Warrior 1", "ns_user_db": "main"}'
```

Configure a bridged server: 
```
api-cli ns.ovpnrw set-configuration --data '{"instance": "ns_roadwarrior1", "proto":"udp","port":"1194","dev_type":"tap","topology":"subnet","enabled":"1","client_to_client":"0","auth":"SHA256","cipher":"AES-256-GCM","tls_version_min":"1.2","ns_auth_mode":"certificate","ns_public_ip":["192.168.100.238"],"server":"","ns_redirect_gateway":"0","ns_local":["192.168.22.0/24","192.168.100.0/24"],"ns_dhcp_options":[],"ns_pool_start":"192.168.100.239","ns_pool_end":"192.168.100.240","ns_bridge":"lan", "ns_description": "Road Warrior 1", "ns_user_db": "main"}'
```

Valid values for `proto` field are: `udp` and `tcp-server`

Required fields for routed mode:
- `dev_type` field must be set to `tun`
- `server` field must contain a valid CIDR
- `ns_pool_start`, `ns_pool_end` and `ns_brdige` fields should be empty

Required fields for bridged mode:
- `dev_type` field must be set to `tap`
- `ns_pool_start`, `ns_pool_end` must contain a valid IP addresses; both address should be inside the bridge network, start must be greater than end
- `ns_brdige` field must contain a bridge obtained from `list-bridges` API
- `server` should be empty

The API may raise the following validation errors:
- bridge_not_found
- start_not_in_network
- end_not_in_network
- ip_already_used
- start_must_be_greater_then_end

### import-users

Create all VPN uses from the database associated to an instance:
```
api-cli ns.ovpnrw add-user --data '{"instance": "ns_roadwarrior1"}'
```

Response example:
```json
{"result": "success"}
```

If one or more user creation fails, it will return something like:
```json
{"error": "user_import_failed-ns_d486faa0-ns_d79f110"}
```
Where the format is `user_import_failed-<user_id_1>-<user_id_2>...`.

### add-user

Create a user and generate a certficate for it:
```
api-cli ns.ovpnrw add-user --data '{"instance": "ns_roadwarrior1", "enabled": "1", "username": "myuser", "expiration": "3650", "ipaddr": "1.2.3.4"}'
```

Response example:
```json
{"result": "success"}
```

The APIs can raise the following validation errors:
- user_add_failed
- reserved_ip_must_be_in_server_network
- reserverd_ip_already_used
- reserved_ip_must_be_in_server_network
- user_db_not_configured
- db_not_found
- user_not_in_db

### edit-user

Edit a user and generate a certficate for it:
```
api-cli ns.ovpnrw add-user --data '{"instance": "ns_roadwarrior1", "enabled": "1", "username": "myuser", "ipaddr": "1.2.3.4"}'
```

Response example:
```json
{"result": "success"}
```

The APIs can raise the following validation errors:
- user_not_found
- user_add_failed
- reserved_ip_must_be_in_server_network
- reserverd_ip_already_used
- reserved_ip_must_be_in_server_network

### disconnect-user

Disconnect a connected client:
```
api-cli ns.ovpnrw disconnect-user --data '{"instance": "ns_roadwarrior1", "username": "myuser"}''
```

Response example:
```json
{"result": "success"}
```

Throws a validation error if the user is not found.

### disable-user

Disable an existing user:
```
api-cli ns.ovpnrw disable-user --data '{"instance": "ns_roadwarrior1", "username": "myuser"}''
```
If the user is currently utilizing the VPN, the API will also disconnect the client.

Response example:
```json
{"result": "success"}
```

Throws a validation error if the user is not found.

### enable-user

Enable an existing user:
```
api-cli ns.ovpnrw enable-user --data '{"instance": "ns_roadwarrior1", "username": "myuser"}''
```

Response example:
```json
{"result": "success"}
```

Throws a validation error if the user is not found.


### delete-user

Delete an existing user:
```
api-cli ns.ovpnrw delete-user --data '{"instance": "ns_roadwarrior1", "username": "myuser"}''
```

Response example:
```json
{"result": "success"}
```

The API can raise the following validation errors:
- `user_not_found` if the user is not found
- `user_is_used` if the user is currently used as firewall object, error is like:
  ```json
  {"validation": {"errors": [{"parameter": "username", "message": "user_is_used", "value": ["firewall/ns_allow_OpenVPNRW1"]}]}}
  ```


### regenerate-user-certificate

Delete current user certificate and create a new one:
```
api-cli ns.ovpnrw regenerate-user-certificate --data '{"instance": "ns_roadwarrior1", "username": "myuser", "expiration": "3650"}''
```

Response example:
```json
{"result": "success"}
```

Throws a validation error if the user is not found.

### download-user-certificate

Download the certificate chain for the given user:
```
api-cli ns.ovpnrw download-user-certificate --data '{"instance": "ns_roadwarrior1", "username": "myuser"}'
```

Response example:
```json
{
  "data": "-----BEGIN CERTIFICATE-----\nMII...\n-----END PRIVATE KEY-----\n\n"}
```

Throws a validation error if the user is not found.

### download-user-configuration

Download the OpenVPN configuration with embedded certificates for the given user:
```
api-cli ns.ovpnrw download-user-configuration --data '{"instance": "ns_roadwarrior1", "username": "myuser"}''
```

Response example:
```json
{
  "data": "dev tun\nproto udp\..\ncompress\n"
}
```

Throws a validation error if the user is not found.

### download-user-2fa

Download the 2FA secret, the secret is encoded inside a QR code in a SVG file:
```
api-cli ns.ovpnrw download-user-2fa --data '{"instance": "ns_roadwarrior1", "username": "myuser"}''
```

Response example:
```json
{
  "data": "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n<!-- Created with qrencode 4.1.1 (https://fukuchi.org/works/qrencode/index.html) -->\n<svg width=\"4.34cm\..." 
}
```

Throws a validation error if the user is not found.

### connection-history

Output the users connection history in a json format:
```
api-cli ns.ovpnrw connection-history --data '{"instance": "ns_roadwarrior1"}'
```

Response example:
```json
{
  [
    {"account": "foo", "bytesReceived": null, "bytesSent": null, "duration": null, "endTime": null, "remoteIpAddress": "12.34.56.78", "startTime": 1729592489, "virtualIpAddress": "10.9.9.41"}, 
    {"account": "john", "bytesReceived": 9605402, "bytesSent": 33898343, "duration": 968, "endTime": 1729516942, "remoteIpAddress": "12.34.56.78", "startTime": 1729515974, "virtualIpAddress": "10.9.9.41"}
  ]
}
```

Throws a generic error:
- the sqlite database is not found
- the sqlite database cannot be read.

### connection-history-csv

Download the users connection history in a csv file:
```
api-cli ns.ovpnrw connection-history-csv --data '{"instance": "ns_roadwarrior1", "timezone":"Europe/Rome"}'
```

- `timezone`: user timezone, e.g. "Europe/Rome"

Response example:
```json
{
  "csv_path": "/var/run/ns-api-server/downloads/connection_history.csv"
}
```

Throws a generic error:
- the sqlite database is not found
- the sqlite database cannot be read.


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
api-cli ns.dedalo set-configuration --data '{"network": "192.168.182.0/24", "hotspot_id": "1234", "unit_name": "myunit", "unit_description": "my epic unit", "interface": "eth3", "dhcp_limit": "150"}'
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
    "hotspot_id": "2",
    "unit_name": "NethSec",
    "unit_description": "My hotspot",
    "interface": "eth2",
    "dhcp_start": "192.168.182.2",
    "dhcp_limit": "100",
    "max_clients": "255",
    "connected": true
  }
}
```

The `connected` field tells if the device is logged to the hotspot manager.
If the device is not connected, you need to execute the `login` api to retrieve remote data.

### get-dhcp-range

Return the first and last IPs valid for the DHCP range, given a network CIDR:
```
api-cli ns.dedalo get-dhcp-range --data '{"network": "192.168.0.0/24"}'
```

Response example:
```json
{
  "start": "192.168.0.2",
  "end": "252",
  "max_entries": 253
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
      "ns_description": "",
      "readonly": true
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
      "ns_description": "",
      "readonly": false
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

Supported services are: `internet`, `banip`, `dedalo`, `netifyd`, `threat_shield_dns`, `adblock`, `threat_shield_ip`, `openvpn_rw`, `flashstart`, `mwan`, `dns-configured`

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
- `threat_shield_ip`: return the number of blocked IPs in the last hour
- `openvpn_rw`: return the number of clients connected to `ns_roadwarrior1` instance

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

### ipsec-tunnels

Count enabled and connected IPsec tunnels:
```
api-cli ns.dashboard ipsec-tunnels
```

Response example:
```json
{
  "result": {
    "enabled": 2,
    "connected": 1
  }
}
```

### ovpn-tunnels

Count enabled and connected OpenVPN tunnels:
```
api-cli ns.dashboard ovpn-tunnels
```

Response example:
```json
{
  "result": {
    "enabled": 2,
    "connected": 1
  }
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
    "force": true,
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
    "force": false,
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
  "active": true,
  "force": true
}
```

Each element of the `options` array is a key-value object.
The key is the DHCP option name or number, the value is the option value.
Multiple values can be comma-separated.

### edit-interface

Change or add the DHCPv4 configuration for a given interface:
```
api-cli ns.dhcp edit-interface --data '{"interface":"lan","first":"192.168.100.2","last":"192.168.100.150","active":true,"leasetime": "12h","force":true,"options":[{"gateway":"192.168.100.1"},{"domain":"nethserver.org"},{"dns":"1.1.1.1,8.8.8.8"},{"120":"192.168.100.151"}]}'
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
      "device": "eth2.1",
      "description": "description 1",
      "used": false,
      "matches": []
    },
    {
      "lease": "ns_lease2",
      "macaddr": "80:5e:c0:d9:c5:eb",
      "ipaddr": "192.168.5.162",
      "hostname": "W90B-1",
      "interface": "blue",
      "device": "eth2.1",
      "description": "description 2",
      "used": true,
      "matches": ["firewall/ns_allow_xxx"]
    }
  ]
}
```

The `lease` field contains the lease id which can be used to retrive the lease configuration.
The `used` field is `true` if the lease has been used as firewall objects. The `matches` field contains the firewall objects where the lease has been used.

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

It can raise the `static_lease_is_used` validation error if the lease is currently used as firewall object. The error is like:
```json
{"validation": {"errors": [{"parameter": "lease", "message": "static_lease_is_used", "value": ["firewall/ns_allow_xxx"]}]}}
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
      "description": "",
      "wildcard": true,
      "used": true,
      "matches": ["firewall/ns_allow_xxx"]
    }
  ]
}
```

The `record` field is the id of the DNS record.
If `used` is `true`, the record is used as firewall object. The `matches` field contains the firewall objects where the record has been used.

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

It may raise `dns_record_is_used` validation error if the record is currently used as firewall object. The error is like:
```json
{"validation": {"errors": [{"parameter": "record", "message": "dns_record_is_used", "value": ["firewall/ns_allow_xxx"]}]}}
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
api-cli ns.redirects add-redirect --data '{"name": "my pf", "dest_ip": "10.0.0.1", "proto": ["tcp"], "src_dport": "22", "reflection": "1", "log": "1",  "dest_port": "222", "restrict": ["1.2.3.4"], "src_dip": "4.5.6.7", "dest": "lan", "reflection_zone": ["lan", "guest"], "enabled": "1", "ns_rc": "", "ns_dst": ""}'
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
- `ns_src`: can contain an object if in the form `<database>/<id>`, it overwrites the `restrict` field
- `ns_dst`: can contain an object if in the form `<database>/<id>`, it overwrites the `dest_ip` field

Success response:
```json
{
  "id": "ns_pf40"
}
```

### edit-redirect

Edit a redirect rule:
```
api-cli ns.redirects edit-redirect --data '{"id": "ns_pf40", "name": "my pf", "dest_ip": "10.0.0.1", "proto": ["tcp"], "src_dport": "22", "reflection": "1", "log": "1",  "dest_port": "222", "restrict": [], "src_dip": "4.5.6.7", "enabled": "0", "ns_rc": "", "ns_dst": ""}'
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

### list-object-suggestions

List firewall objects suggestions:
```
api-cli ns.redirects list-object-suggestions
```

Response example:
```json
  "objects": {
    "ns_src": [
      {
        "name": "h1",
        "family": "ipv4",
        "id": "ns_04fadb5c",
        "singleton": true,
        "type": "host_set"
      },
      {
        "name": "myset",
        "family": "ipv4",
        "id": "ns_3cf75e0e",
        "singleton": false,
        "type": "host_set"
      },
      {
        "name": "MySet",
        "description": "Mydomain set",
        "family": "ipv4",
        "id": "myset",
        "type": "domain_set"
      }
    ],
    "ns_dst": [
      {
        "name": "h1",
        "family": "ipv4",
        "id": "ns_04fadb5c",
        "singleton": true,
        "type": "host_set"
      },
      {
        "id": "dhcp/ns_9e7f705e",
        "name": "test1.domain",
        "type": "dns_record",
        "family": "ipv4"
      }
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
   "values": {
      "data": [
         {
            "id": 10392,
            "name": "netify.apple-siri",
            "type": "application",
            "category": {
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
               "name": "advertiser"
            }
         },
         {
            "id": 142,
            "name": "WhatsApp",
            "type": "protocol",
            "category": {
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
               "name": "voip"
            }
         }
      ],
      "meta": {
         "last_page": 2,
         "total": 12
      }
   }
}
```

### list-popular

List popular applications and protocols:

```bash
api-cli ns.dpi list-popular
```

Data can be limited and paginated by using the `limit` and `page` parameters:

```bash
api-cli ns.dpi list-popular --data '{"limit": 3, "page": 2}'
```

**PLEASE NOTE**:

- `category` field can be missing in some applications/protocols.
- `missing` field is true when the application/protocol is not available in the current netifyd database.

Example response:

```json
{
   "values": {
      "data": [
         {
            "id": 10392,
            "name": "netify.apple-siri",
            "type": "application",
            "category": {
               "name": "business"
            },
            "missing": false
         },
         {
            "id": 142,
            "name": "WhatsApp",
            "type": "protocol",
            "category": {
               "name": "messaging"
            },
            "missing": false
         },
         {
            "name": "whatsapp",
            "missing": true
         },
         {
            "id": 238,
            "name": "Apple/Push",
            "type": "protocol",
            "missing": false
         }
      ],
      "meta": {
         "last_page": 3,
         "total": 8
      }
   }
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
      "device": "eth4",
      "interface": "GREEN_1",
      "action": "block",
      "criteria": [
        {
          "id": 156,
          "name": "netify.spotify",
          "type": "application",
          "category": {
            "name": "streaming-media"
          }
        },
        {
          "id": 10119,
          "name": "netify.adobe",
          "type": "application",
          "category": {
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
api-cli ns.dpi add-rule --data '{"enabled": false, "device": "eth4", "applications": [], "protocols": ["HTTP/S"]}'
```

Rundown of required parameters:

- `enabled`: `true` or `false`
- `device`: device name, e.g. `eth4`
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
api-cli ns.dpi edit-rule --data '{"config-name": "ns_f1c6e9e0", "enabled": true, "device": "eth4", "applications": ["netify.spotify", "netify.adobe"], "protocols": []}'
```

Rundown of required parameters:
- `config-name`: rule name, refer to `list-rules` api.
- `enabled`: `true` or `false`
- `device`: device name, e.g. `eth4`
- `applications`: list of application names, e.g. `["netify.spotify", "netify.adobe"]`, refer to `list-applications`
  api.
- `protocols`: list of protocol names, e.g. `["HTTP/S"]`, refer to `list-applications` api.

Example response:

```json
{
   "message": "success"
}
```

### list-devices

List available devices to be added to DPI rules:

```bash
api-cli ns.dpi list-devices
```

Example response:

```json
{
  "values": [
    {
      "interface": "GREEN_1",
      "device": "eth0"
    },
    {
      "interface": "GREEN_2",
      "device": "eth4"
    }
  ]
}
```

### list-exemptions

List configured global exemptions:

```bash
api-cli ns.dpi list-exemptions
```

Example response:
```json
{
  "values": [
    {
      "config-name": "cfg024ffe",
      "enabled": true,
      "criteria": "192.168.1.1",
      "description": "my ex"
    }
  ]
}
```
### add-exemption

Add global exemption:

```bash
api-cli ns.dpi add-rule --data '{"criteria": "192.168.1.1", "description": "my host", "enabled": true}'
```

Rundown of required parameters:

- `enabled`: `true` or `false`
- `critera`: an IP address like `192.168.1.1`
- `description`: an optional description

Example response:

```json
{
   "message": "success"
}
```

It can raise a validation error if the criteria is duplicated. Example:

```json
{
  "validation": {
    "errors": [
      {
        "parameter": "criteria",
        "message": "criteria_already_exists",
        "value": "192.168.1.3"
      }
    ]
  }
}
```

### delete-exemption

Delete global exemption rule:

```bash
api-cli nd.dpi delete-exemption --data '{"config-name": "ns_f1c6e9e0"}'
```

Required parameters:

- `config-name`: exemption name, refer to `list-exemptions` api.

Example response:

```json
{
   "message": "success"
}
```

### edit-rule

Edit global exemption:

```bash
api-cli ns.dpi edit-rule --data '{"config-name": "ns_f1c6e9e0", "criteria": "192.168.1.1", "description": "my host", "enabled": true}'
```

Rundown of required parameters:
- `config-name`: rule name, refer to `list-rules` api.
- `enabled`: `true` or `false`
- `critera`: an IP address like `192.168.1.1`
- `description`: an optional description

Example response:

```json
{
   "message": "success"
}
```

## ns.flashstart

Manage Flashstart service configuration.

### get-config

Prints configuration of Flashstart service:

```bash
api-cli ns.flashstart get-config
```

Example response:

```json
{
   "values": {
      "enabled": false,
      "username": "user",
      "password": "password",
      "zones": [
         "lan"
      ],
      "bypass": [
         "192.168.1.1"
      ]
   }
}

```

### set-config

Sets configuration of Flashstart service, **BEWARE** this commits directly the uci changes due to the need to restart
flashstart service. The automatic uci commit is made inside `dhcp` and `flashstart` config.

```bash
api-cli ns.flashstart set-config --data '{"enabled": true, "username": "user", "password": "password", "zones": ["lan"], "bypass": ["192.168.1.1"]}'
```

Example response:

```json
{
   "message": "success"
}
```

### list-zones

List available zones to apply Flashstart service:

```bash
api-cli ns.flashstart list-zones
```

Example response:

```json
{
  "values": [
    {
      "id": "ns_lan",
      "label": "lan"
    },
    {
      "id": "ns_guest",
      "label": "guest"
    }
  ]
}
```

## ns.storage

Manage data storage.

### list-devices

Retrieve the list of not-mounted disk with read-write access:
```
api-cli ns.storage list-devices
```

Response example:
```json
{
  "devices": [
    {
      "name": "vdb",
      "size": 1073741824,
      "path": "/dev/vdb",
      "type": "disk",
      "model": null,
      "vendor": "0x1af4"
    },
    {
      "name": "vda",
      "size": 968899584,
      "path": "/dev/vda",
      "type": "partition",
      "model": null,
      "vendor": null
    }
  ]
}
```

Please note that model and vendor could be empty on some hardware.

### add-storage

Configure the device to be used as extra data storage:
```
api-cli ns.storage add-storage --data '{"device": "/dev/sdb", "type": "disk"}'
```

Successful response example:
```json
{"result": "success"}
```

Error response example:
```json
{"error": "command_failed"}
```

### remove-storage

Unmount the storage:
```
api-cli ns.storage remove-storage
```

Successful response example:
```json
{"result": "success"}
```

Error response example:
```json
{"error": "command_failed"}
```

### get-configuration

Get current configuration
```
api-cli ns.storage get-configuration
```

If the storage is not configured, the output will be:
```json
{
  "name": null,
  "size": null,
  "path": null,
  "model": null,
  "vendor": null
}
```

If the storage is configured, the response will be like:
```json
{
  "name": "sda",
  "size": "1G",
  "path": "/dev/sda",
  "model": "QEMU HARDDISK",
  "vendor": "QEMU"
}
```

## ns.log

Show and filter logs.

### get-log

```bash
api-cli ns.log get-log --data '{"limit": 10, "search: "mwan"}'
```

Parameter list:

- `limit`: number of lines to show
- `search`: search string, uses `grep` syntax

Both parameters are _optional_

Example response:

```json
{
   "values": [
      "Oct 12 08:56:55 NethSec dropbear[21682]: Exit (root) from <W.X.Y.Z:00000>: Disconnect received",
      "Oct 12 09:00:00 NethSec crond[4002]: USER root pid 22583 cmd sleep $(( RANDOM % 60 )); /usr/sbin/send-heartbeat",
      "..."
   ]
}
```

**Notes**: returning strings are syslog formatted, be aware of it if any parsing is needed.

## ns.account

Manage accounts.

### set-password

Allow to change the user password.

**WARNING**: due to how OpenWRT handles loging, if you change the password to the `root` user, you will also change the
password for the shell access.

```bash
api-cli ns.account set-password --data '{"username": "john", "password": "CoolNewPassword123!!"}'
```

Parameter list:

- `username`: target to change the password to, must be present inside `rpcd` configuration
- `password`: password to set to the user

## ns.backup

Allows the backup/restore of the system, some features are only available to subscribed users. Please refer
to `ns.subscription` for more info.

### set-passphrase

Set encryption passphrase to be used to encrypt/decrypt backups.

Required parameters:

- `passphrase`: passphrase to be saved in the machine

```bash
api-cli ns.backup set-passphrase --data='{"passphrase": "another-very-cool-passphrase"}'
```

To delete the passphrase, just set it to an empty string:

```bash
api-cli ns.backup set-passphrase --data='{"passphrase": ""}'
```

Example response:

```json
{
   "message": "success"
}
```

### backup

Runs a backup of the system, returning the name of the result file to download, the backup will be encoded with the passphrase set with `set-passphrase` API.

```bash
api-cli ns.backup backup
```

Example response:

```json
{
   "backup": "backup-vtEUjmUAaMzxAzAsIJmr"
}
```

### restore

Restore the system with the given backup, once successful, restarts the system.
Before invokig this API, the file must have been uploaded with the `files` API.

Required parameters:

- `backup`: contains the backup to restore, must be a `base64` encoded string

```bash
api-cli ns.backup restore --data '{"backup": "backup-vtEUjmUAaMzxAzAsIJmr"}' 
```

Optional `passphrase` can be given to decrypt the file:

```bash
api-cli ns.backup restore --data '{"backup": "backup-vtEUjmUAaMzxAzAsIJmr", "passphrase": "very-cool-passphrase"}'
```

Example response:

```json
{
   "message": "success"
}
```

### registered-list-backups

List backups stored on remote server.

```bash 
api-cli ns.backup registered-list-backups
```

Example response:

```json
{
   "values": [
      {
         "file": "882e399c4e6562da3cfa43e886d82454c1b6311392608100801ad0e19307e8b3.bin",
         "name": "Cool backup"
      },
      {
         "file": "2fc23dae2cfa1ac1aafe074f7662cb0a2fc23dae2cfa1ac1aafe074f7662cb0a.bin",
         "name": "Not so cool backup"
      },
      {
         "file": "83174ecdae5e5de26942c026c37d30b31793b667d35a8bb62794da153853c8f0.bin",
         "name": "Very old backup"
      }
   ]
}
```

### registered-backup

Manually run a backup and send it to remote server, the backup will be encoded with the passphrase set with `set-passphrase` API.

```bash
api-cli ns.backup registered-backup
```

Example response:

```json
{
   "message": "success"
}
```

### registered-restore

Restore a backup from the remote server.

Required parameters:

- `file`: contains the name of the backup to restore, can be retrieved from `registered-list-backups` API

```bash
api-cli ns.backup registered-restore --data '{"file": "882e399c4e6562da3cfa43e886d82454c1b6311392608100801ad0e19307e8b3.bin"}'
```

Optional parameters:

- `passphrase`: passphrase to decrypt the backup if needed

```bash
api-cli ns.backup registered-restore --data '{"file": "882e399c4e6562da3cfa43e886d82454c1b6311392608100801ad0e19307e8b3.bin", "passphrase": "very-cool-passphrase"}'
```

Example response:

```json
{
   "message": "success"
}
```

### registered-download-backup

Download a backup from the remote server.
The returned file name must be downloaded with the `files` API.

Required parameters:

- `file`: contains the name of the backup to download, can be retrieved from `registered-list-backups` API

```bash
api-cli ns.backup registered-download-backup --data '{"file": "882e399c4e6562da3cfa43e886d82454c1b6311392608100801ad0e19307e8b3.bin"}'
```

Example response:

```json
{
   "backup": "backup-lGUGdQZLAuFlhfegTNYQ"
}
```

### is-passphrase-set

Check if a passphrase is set.

```bash
api-cli ns.backup is-passphrase-set
```

Example response:

```json
{
  "values": {
    "set": true
  }
}
 ```

## ns.migration

Manage migration from NS7

### list-target-devices

List existing target devices:
```
api-clit ns.migration list-target-devices
```

Response example:
```json
{
  "devices": [
    {
      "name": "eth0",
      "hwaddr": "52:54:00:6a:50:bf",
      "role": null,
      "ipaddr": null
    },
    {
      "name": "eth1",
      "hwaddr": "52:54:00:20:82:a6",
      "role": "wan",
      "ipaddr": "192.168.122.49"
    }
  ]
}
```

### list-source-devices

Upload a NS7 migration archive:
```
api-cli ns.migration list-source-devices --data '{"archive": "upload-1e20f4b3-e581-454c-9162-ca33885eb223"}' 
```

The archive field is the name of file uploaded with the POST /files API.

This API can return a validation error if the given file is not a valid NS7 migration export archive.

Response example:
```json
{
  "devices": [
    {
      "name": "enp1s0",
      "hwaddr": "xx:yy:xx",
      "ipaddr": "1.2.3.4",
      "role": "green"
    },
    {
      "name": "en1",
      "hwaddr": "xx:zz:zz",
      "ipaddr": "4.5.6.7",
      "role": "red"
    }
  ]
}
```

### migrate

Execute the migration:
```
api-cli ns.migration migrate --data '{"mappings": [{"old": "52:54:00:75:1C:C1", "new": "53:54:44:75:1A:AA"}], "archive": "upload-1e20f4b3-e581-454c-9162-ca33885eb223"}'
```

Response example:
```json
{"result": "success"}
```

## ns.ipsectunnel

### list-tunnels

List existing tunnels:
```
api-cli ns.ipsectunnel list-tunnels
```

Response example:
```json
{
  "tunnels": [
    {
      "id": "ns_81df3995",
      "name": "tun1",
      "local": [
        "192.168.100.0/24"
      ],
      "remote": [
        "192.168.200.0/24"
      ],
      "enabled": "1",
      "connected": false
    }
  ]
}
```

### list-wans

List available wans:
```
api-cli ns.ipsectunnel list-wans
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

### get-defaults

Get tunnel defaults:
```
api-cli ns.ipsectunnel get-defaults
```

Response example:
```json
{
  "pre_shared_key": "gFWPtHR38XaAWrT4GjeFOS0aOtGJnVksvbVcGdJ1EYWB",
  "local_identifier": "@tun2.local",
  "remote_identifier": "@tun2.local",
  "local_networks": [
    "192.168.100.0/24"
  ]
}

```

### get-tunnel

Retrieve tunnel info:
```
api-cli ns.ipsectunnel get-tunnel --data '{"id": "ns_81df3995"}'
```

Response example:
```json
{
  "ike": {
    "encryption_algorithm": "3des",
    "hash_algorithm": "md5",
    "dh_group": "modp1024",
    "rekeytime": "3600"
  },
  "esp": {
    "encryption_algorithm": "3des",
    "hash_algorithm": "md5",
    "dh_group": "modp1024",
    "rekeytime": "3600"
  },
  "ipcomp": "false",
  "dpdaction": "restart",
  "remote_subnet": "192.168.200.0/24",
  "local_subnet": "192.168.100.0/24",
  "ns_name": "tun1",
  "gateway": "10.10.0.172",
  "keyexchange": "ike",
  "local_identifier": "@ipsec1.local",
  "local_ip": "192.168.122.49",
  "enabled": "1",
  "remote_identifier": "@ipsec1.remote",
  "pre_shared_key": "xxxxxxxxxxxxxxxxxxx"
}
```

### add-tunnel

Create a tunnel:
```
api-cli ns.ipsectunnel add-tunnel --data '{"ns_name": "tun1", "ike": {"hash_algorithm": "md5", "encryption_algorithm": "3des", "dh_group": "modp1024", "rekeytime": "3600"}, "esp": {"hash_algorithm": "md5", "encryption_algorithm": "3des", "dh_group": "modp1024", "rekeytime": "3600"}, "pre_shared_key": "xxxxxxxxxxxxxxxxxxx", "local_identifier": "@ipsec1.local", "remote_identifier": "@ipsec1.remote", "local_subnet": ["192.168.100.0/24"], "remote_subnet": ["192.168.200.0/24"], "enabled": "1", "local_ip": "192.168.122.49", "keyexchange": "ike", "ipcomp": "false", "dpdaction": "restart", "gateway": "10.10.0.172"}'
```

Response example:
```json
{"id": "ns_81df3995"}
```

### edit-tunnel

Edit a tunnel:
```
api-cli ns.ipsectunnel add-tunnel --data '{"id": "ns_81df3995", "ns_name": "tun1", "ike": {"hash_algorithm": "md5", "encryption_algorithm": "3des", "dh_group": "modp1024", "rekeytime": "3600"}, "esp": {"hash_algorithm": "md5", "encryption_algorithm": "3des", "dh_group": "modp1024", "rekeytime": "3600"}, "pre_shared_key": "xxxxxxxxxxxxxxxxxxx", "local_identifier": "@ipsec1.local", "remote_identifier": "@ipsec1.remote", "local_subnet": ["192.168.100.0/24"], "remote_subnet": ["192.168.200.0/24"], "enabled": "1", "local_ip": "192.168.122.49", "keyexchange": "ike", "ipcomp": "false", "dpdaction": "restart", "gateway": "10.10.0.172"}'
```

Response example:
```json
{"id": "ns_81df3995"}
```

### enable-tunnel

Enable a tunnel:
```
api-cli ns.ipsectunnel enable-tunnel --data '{"id": "ns_81df3995"}'
```

Response example:
```json
{"result": "success"}
```

### disable-tunnel

Disable a tunnel:
```
api-cli ns.ipsectunnel disable-tunnel --data '{"id": "ns_81df3995"}'
```

Response example:
```json
{"result": "success"}
```

### delete-tunnel

Delete a tunnel all associated configurations like routes and interfaces:
```
api-cli ns.ipsectunnel delete-tunnel --data '{"id": "ns_81df3995"}'
```

Response example:
```json
{"result": "success"}
```

### list-algs

List available algorithms:
```
api-cli ns.ipsectunnel list-algs
```

Result example:
```json
{
  "encryption": [
    {
      "name": "AES 128",
      "id": "aes128"
    },
    {
      "name": "128 bit Blowfish-CBC",
      "id": "blowfish"
    }
  ],
  "integrity": [
    {
      "name": "MD5",
      "id": "md5"
    },
    {
      "name": "AES XCBX",
      "id": "aesxcbc"
    }
  ],
  "dh": [
    {
      "name": "1024 bit (DH-2)",
      "id": "modp1024"
    },
    {
      "name": "Newhope 128",
      "id": "newhope"
    }
  ]
}
```

## ns.netdata

Configure netdata reporting daemon.

### get-configuration

Get current netdata configuration:
```
api-cli ns.netdata get-configuration
```

Response example:
```json
{
  "hosts": [
    "1.2.3.4",
    "google.it"
  ]
}
```

### set-hosts

Configure hosts to be monitored by fping:
```
api-cli ns.netdata set-hosts --data '{"hosts": ["1.1.1.1", "google.com"]}'
```

Response example:
```json
{"result": "success"}
```

## ns.factoryreset

### reset

Perform a factory reset of the firmware:
```
api-cli ns.factoryreset reset
```

Response example:
```json
{
  "result": "success"
}
```

## ns.update

### check-package-updates

Check if there are any package updates:
```
api-cli ns.update check-package-updates
```

Response example:
```json
{
  "updates": [
    {
      "package": "ns-api",
      "currentVersion": "1.0.2",
      "lastVersion": "1.0.3",
    },
    {
      "package": "ns-openvpn",
      "currentVersion": "1.1.7",
      "lastVersion": "1.2.0",
    }
  ]
}
```

### get-package-updates-last-check

Get the timestamp of the last check of package updates:
```
api-cli ns.update get-package-updates-last-check
```

Response example:
```json
{
  "lastCheck": 1699615827
}
```

### install-package-updates

Install all available package updates:
```
api-cli ns.update install-package-updates
```

Response example:
```json
{"result": "success"}
```

### check-system-update

Check if there is a system update available:
```
api-cli ns.update check-system-update
```

Response example - system update available:
```json
{
  "currentVersion": "NethSecurity 23.05.0",
  "lastVersion": "NethSecurity 23.05.1",
  "scheduleAt": -1
}
```

Response example - system update available and scheduled:
```json
{
  "currentVersion": "NethSecurity 23.05.0",
  "lastVersion": "NethSecurity 23.05.1",
  "scheduleAt": 1699615827
}
```

### schedule-system-update

Schedule a system update:
```
api-cli ns.update schedule-system-update --data '{"scheduleAt": 1699615827}'
```

Response example:
```json
{"result": "success"}
```

Cancel the schedule of a system update:
```
api-cli ns.update schedule-system-update --data '{"scheduleAt": -1}'
```

Response example:
```json
{"result": "success"}
```

### update-system

Install the latest system update available immediately and reboot the unit:
```
api-cli ns.update update-system
```

Response example:
```json
{"result": "success"}
```

### install-uploaded-image

Install a previously uploaded image inside `/var/run/ns-api-server/` and reboot the unit:
```
api-cli ns.update install-uploaded-image --data '{"image": "upload-204be0f3-4bb2-4cb8-ba28-4ac8e41ac697"}'
```

Response example:
```json
{"result": "success"}
```

### get-automatic-updates-status

Check if automatic updates are enabled:
```
api-cli ns.update get-automatic-updates-status
```

Response example:
```json
{"enabled": false}
```

### set-automatic-updates

Enable or disable automatic updates.

Enable:
```
api-cli ns.update set-automatic-updates --data '{"enable": true}'
```

Disable:
```
api-cli ns.update set-automatic-updates --data '{"enable": false}'
```

Response example:
```json
{"result": "success"}
```

## ns.ssh

Read SSH keys

### list-keys

Return the content of `/etc/dropbear/authorized_keys` file:
```
api-cli ns.ssh list-keys
```

Output example:
```json
{'keys': '\nssh-rsa AAAAB3N...6m5 test@nethserver.org\n'}
```

## ns.reverseproxy

Allows to configure a reverse proxy through the nginx web server.

### list-certificates

List available certificates, rundown of the fields:

- `type`: this can be: `self-signed`, `custom` or `acme`.
   - `self-signed`: certificate generated by the system at first start.
   - `custom`: certificate uploaded by the user, it's used by default for the `*.lan` domain.
   - `acme`: requested certificate through `acme.sh`.
- `default`: if the certificate is used by the `_lan` route.
- `details`: certificate details obtained through `openssl`.
- `expiration`: certificate expiration date, this is a `iso8601` formatted string.
- `servers`: list of domains that are using this certificate.
- `domain`: domain of the certificate, since common name is not a required field, this is used to identify the
  certificate, can be empty.

If `type` is `acme`, there are two additional fields:

- `pending`: if the certificate is still pending to be issued.
- `requested_domains`: list of domains requested for the certificate.

If `pending` is true, you won't find the following values in that entry: `default`, `details`, `expiration`, `servers`
and `domain`.

```bash
api-cli ns.reverseproxy list-certificates
```

Response example:

```json
{
   "values": {
      "_lan": {
         "type": "self-signed",
         "cert_path": "/etc/nginx/conf.d/_lan.crt",
         "key_path": "/etc/nginx/conf.d/_lan.key",
         "default": true,
         "details": "Certificate:\n    Data:\n        ...",
         "expiration": "2027-04-07 15:13:27Z",
         "servers": [
            "_lan"
         ],
         "domain": "OpenWrt"
      },
      "kool_cert": {
         "type": "custom",
         "cert_path": "/etc/nginx/custom_certs/kool_cert.crt",
         "key_path": "/etc/nginx/custom_certs/kool_cert.key",
         "default": false,
         "details": "Certificate:\n    Data:\n        ...",
         "expiration": "2025-01-07 11:40:51Z",
         "servers": [],
         "domain": ""
      },
      "test_trigger": {
         "type": "acme",
         "pending": false,
         "requested_domains": [
            "*.nethserver.net"
         ],
         "cert_path": "/etc/ssl/acme/*.nethserver.net.fullchain.crt",
         "key_path": "/etc/ssl/acme/*.nethserver.net.key",
         "default": false,
         "details": "Certificate:\n    Data:\n        ...",
         "expiration": "2024-04-11 14:13:46Z",
         "servers": [],
         "domain": "*.nethserver.net"
      }
   }
}
```

### list-dns-providers

List available DNS providers to ACME:

```bash
api-cli ns.reverseproxy list-dns-providers
```

Response example:

```json
{
   "values": [
      "1984hosting",
      "acmedns",
      "acmeproxy",
      "active24",
      "ad",
      "ali",
      "anx",
      "arvan",
      "aurora",
      "autodns",
      "aws"
   ]
}
```

### request-certificate

Allows to request a let's encrypt certificate through `acme.sh`.

Required parameters:

- `name`: friendly name of the certificate, must be unique and conform to the uci name format.
- `domains`: domain list of the certificate, must be a list of valid domains,
  e.g. `["test.example.com", "test2.example.com"]`.
- `validation_method`: validation method to be used, must be one of `standalone` or `dns`.

Optional parameters:

- `dns_provider`: if `validation_method` is `dns`, this is the provider to be used, must be one of the values returned
  by `list-dns-providers`.
- `dns_provider_options`: if `validation_method` is `dns`, this is the credentials to be used, must be a list of
  strings, of the format `KEY=VALUE`.

```bash
api-cli ns.reverseproxy request-certificate --data '{"name": "pretty_certificate", "domains": ["test.example.com", "test2.example.com"], "validation_method": "dns", "dns_provider": "cloudflare", "dns_provider_options": ["CF_Key=1234567890"]}"
```

Example response:

```json
{
   "message": "success"
}
```

### add-certificate

Allows to add a custom certificate uploaded to the system.

Required parameters:

- `name`: name of the certificate, must be unique and conform to the uci name format
- `certificate_path`: path to the certificate file, will be imported and saved under `/etc/acme`, then deleted.
- `key_path`: path to the key file, will be imported and saved under `/etc/acme`, then deleted.

Optional parameters:

- `chain_path`: path to the subsequent certificate, will be appended to the `certficate_file` and deleted.

```bash
api-cli ns.reverseproxy add-certificate --data '{"name": "pretty_certificate", "certificate_path": "/tmp/cert.pem", "key_path": "/tmp/key.pem", "chain_path": "/tmp/chain.pem"}'
```

Example response:

```json
{
   "message": "success"
}
```

### delete-certificate

Delete a certificate.

Required parameters:

- `name`: name of the certificate to be deleted

```bash
api-cli ns.reverseproxy delete-certificate --data '{"name": "pretty_certificate"}'
```

### set-default-certificate

Set a certificate as default used by the UI.

Required parameters:

- `name`: name of the certificate to be set as default

```bash
api-cli ns.reverseproxy set-default-certificate --data '{"name": "pretty_certificate"}'
```

### add-path

Adds a path to the default server. This action will commit the `nginx` uci configuration and restart the `nginx` service.

Required parameters:

- `path`: path to be added, e.g. `/test`
- `destination`: url to be proxied, e.g. `http://10.1.2.3:4000`
- `description`: user-friendly description of the path

Optional parameters:

- `allow`: array of CIDR to filter access to this path

```bash
api-cli ns.reverseproxy add-path --data '{"path": "/test", "destination": "10.0.0.3:3000", "allow": ["127.0.0.1", "10.24.0.1/24"], "description": "testing rule"}'
```

Example response:

```json
{
   "message": "success"
}
```

### add-domain

Adds a domain reverse proxy. This action will commit the `nginx` uci configuration and restart the `nginx` service.

Required parameters:

- `domain`: domain to be proxied, e.g. `test.example.com`
- `destination`: url to be proxied, e.g. `http://10.0.0.1/24`
- `description`: user-friendly description of the domain
- `certificate`: certificate to be used, list is provided in `list-certificates`

Optional parameters:

- `allow`: array of CIDR to filter access to this path

```bash
api-cli ns.reverseproxy add-path --data '{"domain": "test.example.com", "destination": "http://10.0.0.1/24", "description": "testing rule", "certificate": "test", "allow": ["10.0.2.0/12", "10.0.1.0/12"]}'
```

Example response:

```json
{
   "message": "success"
}
```

### delete-proxy

Delete a path or domain reverse proxy. This action will commit the `nginx` uci configuration and restart the `nginx`
service.

Required parameters:

- `id`: id of the proxy to be deleted

```bash
api-cli ns.reverseproxy delete-proxy --data '{"id": "ns_81df3995"}'
```

Example response:

```json
{
   "message": "success"
}
```

### list-proxies

List configured paths and domains:

```bash
api-cli ns.reverseproxy list-proxies
```

Example response:

```json
{
  "data": [
    {
      "id": "ns_87f9ea98",
      "type": "location",
      "description": "Cool Location",
      "location": "/cool",
      "destination": "http://10.0.0.1"
    },
    {
      "id": "ns_8af9va38",
      "type": "location",
      "description": "Another location but cooler",
      "location": "/cooler",
      "destination": "http://102.30.41.5",
      "allow": [
        "10.3.4.0/24",
        "1.0.0.2/32"
      ]
    },
    {
      "id": "ns_de64he34",
      "type": "domain",
      "description": "cool domain",
      "domain": "cool.domain",
      "certificate": "cool_certificate", 
      "destination": "http://10.24.42.1",
      "location": "/",
      "allow": [
        "192.168.1.0/24",
        "3.4.6.7/32"
      ]
    }
  ]
}
```

### edit-domain

Edit a domain reverse proxy. This action will commit the `nginx` uci configuration and restart the `nginx` service.

Required parameters:

- `id`: id of the proxy to be edited
- `domain`: domain to be proxied, e.g. `test.example.com`
- `destination`: url to be proxied, e.g. `http://10.0.0.1/24`
- `description`: user-friendly description of the domain
- `certificate`: certificate to be used, list is provided in `list-certificates`

Optional parameters:

- `allow`: array of CIDR to filter access to this path

```bash
api-cli ns.reverseproxy edit-domain --data '{"id": "ns_8af9va38", "domain": "edit.example.com", "destination": "http://11.1.1.1", "description": "edited rule", "certificate": "test", "allow": ["10.0.2.0/12"]}'
```

Example response:

```json
{
   "message": "success"
}
```

### edit-path

Edit a path reverse proxy. This action will commit the `nginx` uci configuration and restart the `nginx` service.

Required parameters:

- `id`: id of the proxy to be edited
- `path`: path to be added, e.g. `/test`
- `destination`: url to be proxied, e.g. `http://10.1.2.3:4000`
- `description`: user-friendly description of the path

Optional parameters:

- `allow`: array of CIDR to filter access to this path

```bash
api-cli ns.reverseproxy edit-path --data '{"id": "ns_4he2hgi2", "path": "/edited", "destination": "http://11.1.1.1", "description": "description edited", "allow": ["1.1.1.1/24"]}'
```

Example response:

```json
{
   "message": "success"
}
```

### check-config

Checks the configuration using `nginx -t -c /etc/nginx/uci.conf`, this call returns the output of the command in case of
failure. Run this call after you've committed the configuration to check if it's valid. This command will return invalid
configuration only when `nginx` is unable to start with the given configuration.

```bash
api-cli ns.reverseproxy check-config
```

Example response:

```json
{
   "message": "success"
}
```

Invalid configuration response:

```json
{
   "status": "invalid",
   "output": "nginx: [emerg] \"server\" directive is not allowed here in /etc/nginx/uci.conf:1\nnginx: configuration file /etc/nginx/uci.conf test failed\n"
}
```

## ns.devices

Manages network devices and interfaces.

### list-devices

List configured and unconfigured network interfaces and devices, organized by zone.

```bash
api-cli ns.devices list-devices
```

Response example:

```json
{
  "devices_by_zone": [
    { "name": "lan", "devices": ["br-lan"] },
    { "name": "wan", "devices": ["eth1"] },
    { "name": "unassigned", "devices": ["eth2", "eth3"] }
  ],
  "all_devices": [
    {
      "ipaddrs": [
        { "address": "192.168.122.144/24", "broadcast": "192.168.122.255" }
      ],
      "ip6addrs": [{ "address": "fe80::5054:ff:fe5b:1506/64" }],
      "link_type": "ether",
      "mac": "52:54:00:5b:15:06",
      "mtu": 1500,
      "name": "eth1",
      "up": true,
      "stats": {
        "collisions": 0,
        "multicast": 0,
        "rx_bytes": 12253535,
        "rx_dropped": 0,
        "rx_errors": 0,
        "rx_packets": 119400,
        "tx_bytes": 66034,
        "tx_dropped": 0,
        "tx_errors": 0,
        "tx_packets": 665
      },
      "speed": 1000
    },
    {
      "name": "br-lan",
      "type": "bridge",
      "ports": ["eth0"],
      ".name": "cfg020f15",
      ".type": "device",
      "ipaddrs": [
        { "address": "192.168.122.30/24", "broadcast": "192.168.122.255" }
      ],
      "ip6addrs": [{ "address": "fe80::5054:ff:fe28:d273/64" }],
      "link_type": "ether",
      "mac": "52:54:00:28:d2:73",
      "mtu": 1500,
      "up": true,
      "stats": {
        ...
      },
      "speed": -1
    },
    ...
  ]
}
```

### configure-device

Create or configure an unconfigured device, or edit its configuration. What happens exactly in the configuration process depends on the input parameters. Anyway, as a rule of thumb the configuration of a device executes one or more of the following steps:
- creation of a network interface
- association of the device to the newly created interface
- configuration of some attributes of the network interface
- association of the network interface to a firewall zone

Required parameters:

- The set of other required parameters depends on the specific device configuration

All parameters:

- `interface_name`: network interface name to assign to the device
- `device_name`: name of the device to create
- `device_type`: can be `physical` or `logical`
- `protocol`: can be `static`, `dhcp`, `dhcpv6` or `pppoe`
- `zone`: can be any configured firwall zone name, e.g. `lan`, `wan`...
- `logical_type`: can be `bridge` or `bond`
- `interface_to_edit`: name of the network interface to edit
- `ip4_address`: an IPv4 address in CIDR notation (e.g. 10.20.30.40/24)
- `ip4_gateway`: an IPv4 gateway
- `ip4_mtu`: IPv4 maximum transmission unit
- `ip6_enabled`: `True` to enable IPv6, `False` otherwise
- `ip6_address`: an IPv4 address in CIDR notation (e.g. 2001:db8:0:1:1:1:1:1/64)
- `ip6_gateway`: an IPv6 gateway
- `ip6_mtu`: IPv6 maximum transmission unit
- `attached_devices`: when configuring a bridge or a bond, it's the list of slave devices, e.g. `["eth0", "eth1"]`
- `bonding_policy`: when configuring a bond, can be any of `balance-rr`, `active-backup`, `balance-xor`, `broadcast`, `802.3ad`, `balance-tlb`, `balance-alb`
- `bond_primary_device`: when configuring a bond, name of the primary device
- `pppoe_username`: PPPoE username
- `pppoe_password`: PPPoE password
- `dhcp_client_id`: Client ID to send when requesting DHCP
- `dhcp_vendor_class`: Vendor class to send when requesting DHCP
- `dhcp_hostname_to_send`: Hostname to send when requesting DHCP, can be `deviceHostname`, `doNotSendHostname` or `customHostname`
- `dhcp_custom_hostname`: Custom hostname to use when `dhcp_hostname_to_send = customHostname`

```bash
api-cli ns.devices configure-device --data '{"device_type": "physical", "interface_name": "myiface", "protocol": "static", "zone": "lan", "ip6_enabled": false, "device_name": "eth2", "ip4_address": "10.20.30.40/24"}'
```

Response example:

```json
{
   "message": "success"
}
```

### unconfigure-device

Remove a device to an unconfigured state by deleting the associated network interface and other data created during the configuration process.

Required parameters:

- `iface_name`: name of the interface associated to the device to unconfigure

```bash
api-cli ns.devices unconfigure-device --data '{"iface_name": "myiface"}'
```
Response example:

```json
{
   "message": "success"
}
```

### create-alias-interface

Create an alias interface in order to associate multiple IPv4/IPv6 addresses to a network interface.

Required parameters:

- `alias_iface_name`: name of the alias interface
- `parent_iface_name`: name of the parent network interface (the one we need to add IP addresses to)

Optional parameters:

- `ip4_addresses`: list of IPv4 addresses in CIDR notation
- `ip6_addresses`: list of IPv6 addresses in CIDR notation

At least one of `ip4_addresses` and `ip6_addresses` are required.

```bash
api-cli ns.devices create-alias-interface --data '{"alias_iface_name": "al_myiface", "parent_iface_name": "myiface", "ip4_addresses": ["11.22.33.44/24"], "ip6_addresses": []}'
```

Response example:

```json
{
   "message": "success"
}
```

### edit-alias-interface

Edit the list of IPv4/IPv6 addresses of an alias interface.

Required parameters:

- `alias_iface_name`: name of the alias interface to edit
- `parent_iface_name`: name of the parent network interface

Optional parameters:

- `ip4_addresses`: list of IPv4 addresses in CIDR notation
- `ip6_addresses`: list of IPv6 addresses in CIDR notation

At least one of `ip4_addresses` and `ip6_addresses` are required.

```bash
api-cli ns.devices edit-alias-interface --data '{"alias_iface_name": "al_myiface", "parent_iface_name": "myiface", "ip4_addresses": ["11.22.33.44/24", "55.66.77.88/24"], "ip6_addresses": []}'
```

Response example:

```json
{
   "message": "success"
}
```

### delete-alias-interface

Delete an alias interface and remove the associated IPv4/IPv6 addresses from the parent interface.

Required parameters:

- `alias_iface_name`: name of the alias interface to edit
- `parent_iface_name`: name of the parent network interface

```bash
api-cli ns.devices delete-alias-interface --data '{"alias_iface_name": "al_myiface", "parent_iface_name": "myiface"}'
```

Response example:

```json
{
   "message": "success"
}
```

### create-vlan-device

Create a VLAN device.

Required parameters:

- `vlan_type`: can be `8021q` or `8021ad`
- `base_device_name`: name of the network device to create the VLAN on
- `vlan_id`: VLAN ID, must be a positive integer

```bash
api-cli ns.devices create-vlan-device --data '{"vlan_type": "8021q", "base_device_name": "eth3", "vlan_id": 5}'
```

Response example:

```json
{
   "message": "success"
}
```

### delete-device

Delete a device from `network` database.

Required parameters:

- `device_name`: name of the network device to delete

```bash
api-cli ns.devices delete-device --data '{"device_name": "eth3.5"}'
```

Response example:

```json
{
   "message": "success"
}
```

### list-zones-for-device-config

List firewall zones that can be selected for device configuration. Currently all zones are returned except: `hotspot`, `openvpn`, `ipsec` and `rwopenvpn`.

```bash
api-cli ns.devices list-zones-for-device-config
```

Response example:

```json
{
  "zones": [
    {
      "name": "lan",
      "input": "ACCEPT",
      "output": "ACCEPT",
      "forward": "ACCEPT",
      "network": [
        "lan"
      ],
      ".name": "ns_lan",
      ".type": "zone"
    },
    {
      "name": "wan",
      "input": "REJECT",
      "output": "ACCEPT",
      "forward": "REJECT",
      "masq": "1",
      "mtu_fix": "1",
      "network": [
        "wan",
        "myiface"
      ],
      ".name": "ns_wan",
      ".type": "zone"
    },
    {
      "name": "myzone",
      "input": "DROP",
      "forward": "DROP",
      "output": "ACCEPT",
      ".name": "ns_myzone",
      ".type": "zone"
    }
  ]
}
```

## ns.users

### list-users

List configured users
```
api-cli ns.users list-users --data '{"database": "main"}'
```

Response example for a local database:
```json
{
  "users": [
    {
      "local": true,
      "database": "main",
      "name": "user",
      "password": "$6$nu00HaYNNF/rxGV4$nWpG3j5ydXy6anlK1x0DjNDN3PGC78YSxUvgEiFaW/3mWjyWP62iTp+IdBf7tynQueHl4zBBD+9JN3Ws+HMT7w==",
      "description": "User",
      "id": "ns_652b6c80"
    }
  ]
}
```

Response example for a remote LDAP database:
```json
{
  "users": [
    {
      "name": "admin",
      "description": "admin",
      "local": false,
      "admin": true,
      "database": "ns7",
      "id": "admin"
    },
    {
      "name": "pluto",
      "description": "Pluto Rossi",
      "local": false,
      "admin": false,
      "database": "ns7",
      "openpvn_ipaddr": "1.2.3.4",
      "openvpn_enabled": "1",
      "id": "pluto"
    }
  ]
}
```

May raise the following validation errors:
- db_not_found

### list-databases

List configured user databases
```
api-cli ns.users list-databases
```

Response example:
```json
{
  "databases": [
    {
      "name": "main",
      "type": "local",
      "description": "Main local database"
    },
    {
      "name": "ns7",
      "type": "ldap",
      "description": "OpenLDAP NS7",
      "schema": "rfc2307",
      "uri": "ldap://192.168.100.2",
      "used": [
        "wireguard"
      ]
    }
  ]
}
```

### get-database

Retrieve all configuration of the given database:
```
api-cli ns.users get-database --data '{"name": "main"}'
```

Response example for a local database:
```json
{
  "database": {
    "description": "Main local database",
    "name": "main",
    "type": "local"
  }
}
```

Response example for a ldap database:
```json
{
  "database": {
    "uri": "ldap://192.168.100.234",
    "schema": "rfc2307",
    "base_dn": "dc=directoy,dc=nh",
    "user_dn": "ou=People,dc=directory,dc=nh",
    "user_attr": "uid",
    "user_display_attr": "cn",
    "bind_dn": "cn=admin,dc=directory,dc=nh",
    "bind_password": "pass",
    "start_tls": "0",
    "tls_reqcert": "never",
    "description": "OpenLDAP NS7",
    "name": "ns7",
    "type": "ldap"
  }
}
```

### add-ldap-database

Add new remote LDAP database:
```
api cli ns.users add-ldap-database --data '{"name": "ns7", "uri": "ldap://192.168.100.234", "schema": "rfc2307", "base_dn": "dc=directoy,dc=nh", "user_dn": "ou=People,dc=directory,dc=nh", "user_attr": "uid", "user_display_attr": "cn", "start_tls": false, "tls_reqcert": "never", "description": "OpenLDAP NS7", "bind_dn": "cn=admin,dc=directory,dc=nh", "bind_password": "pass", "user_bind_dn": ""}'
```

Response example:
```json
{"result": "success"}
```

May raise the following validation errors:
- db_already_exists

### edit-ldap-database

Edit a remote LDAP database:
```
api-cli ns.users add-ldap-database --data '{"name": "ns7", "uri": "ldap://192.168.100.234", "schema": "rfc2307", "base_dn": "dc=directoy,dc=nh", "user_dn": "ou=People,dc=directory,dc=nh", "user_attr": "uid", "user_display_attr": "cn", "start_tls": false, "tls_reqcert": "never", "description": "OpenLDAP NS7", "bind_dn": "cn=admin,dc=directory,dc=nh", "bind_password": "pass", "user_bind_dn": ""}'
```

Response example:
```json
{"result": "success"}
```

May raise the following validation errors:
- db_not_found

### delete-ldap-database

Delete a remote LDAP databse:
```
api-cli ns.users delete-ldap-database --data '{"name": "ns7"}'
```

Response example:
```json
{"result": "success"}
```

May raise the following validation errors:
- db_not_found

### test-ldap

Test LDAP connection, it returns the list of users:
```
api-cli ns.users test-ldap --data '{"uri": "ldap://192.168.100.234", "base_dn": "dc=directoy,dc=nh", "user_dn": "ou=People,dc=directory,dc=nh", "user_attr": "uid", "user_display_attr": "cn", "start_tls": false, "tls_reqcert": "never"}'
```

Response example:
```json
{
  "users": [
    {
      "name": "admin",
      "description": "admin"
    },
    {
      "name": "pluto",
      "description": "Pluto Rossi"
    }
  ]
}
```

### add-local-database

Create a local user database:
```
api-cli ns.users add-local-database --data '{"name": "local2", "description": "Local users"}''
```

Response example:
```json
{"result": "success"}
```

May raise the following validation errors:
- db_already_exists

### edit-local-database

Edit a local user database:
```
api-cli ns.users add-local-database --data '{"name": "local2", "description": "Local users 2"}''
```

Response example:
```json
{"result": "success"}
```

May raise the following validation errors:
- db_not_found

### delete-local-database

Delete the local user database and all its users and groups:
```
api-cli ns.users delete-local-database --data '{"name": "local2"}''
```

Response example:
```json
{"result": "success"}
```

May raise the following validation errors:
- db_not_found

### add-local-user

Add a user to the local database:
```
api-cli ns.users add-local-user --data '{"name": "john", "password": "P4**$w0rd", "description": "John Doe", "database": "main", "extra": {"openvpn_enabled": "0"}}'
```

Response example:
```json
{"id": "ns_0d0e8762"}
```

Extra fields will be added to user object.

May raise the following validation errors:
- user_already_exists
- db_not_local

### edit-local-user

Change an existing user inside the local database:
```
api-cli ns.users edit-local-user --data '{"name": "john", "password": "P4**$w0rd", "description": "John Doe", "database": "main", "extra": {"openvpn_ipaddr": "1.2.3.4"}}'
```

To remove an existing extra option, just pass the `extra` field without that specific option.
As an example, the above call removes the `openvpn_enabled` option from the user and add the `openvpn_ipaddr` option.

Response example:
```json
{"id": "ns_0d0e8762"}
```

May raise the following validation errors:
- user_not_found
- db_not_local

### delete-local-user

Delete a user from a local database:
```
api-cli ns.users delete-local-user --data '{"name": "john", "database": "main"}'
```

Response example:
```json
{"result": "success"}
```

May raise the following validation errors:
- user_not_found
- db_not_local

### add-remote-user

Add a user to the remote database:
```
api-cli ns.users add-remote-user --data '{"name": "john", "database": "main", "extra": {"openvpn_enabled": "0"}}'
```

Response example:
```json
{"id": "ns_427824b1"}
```

Extra fields will be added to user object.

May raise the following validation errors:
- user_already_exists
- db_not_remote

### edit-remote-user

Change an existing remoteuser:
```
api-cli ns.users edit-remote-user --data '{"name": "john", "database": "main", "extra": {"openvpn_ipaddr": "1.2.3.4"}}'
```

To remove an existing extra option, just pass the `extra` field without that specific option.
As an example, the above call removes the `openvpn_enabled` option from the user and add the `openvpn_ipaddr` option.

Response example:
```json
{"id": "ns_427824b1"}
```

May raise the following validation errors:
- user_not_found
- db_not_remote

### delete-remote-user

Delete an existing user from a remote LDAP database:
```
api-cli ns.users delete-remote-user --data '{"name": "john", "database": "main"}'
```

Response example:
```json
{"result": "success"}
```

May raise the following validation errors:
- user_not_found
- db_not_remote

### set-admin

Make a local user an admin. The admin can login to the UI:
```
api-cli ns.users set-admin --data '{"name": "pluto", "database": "main"}'
```

Response example:
```json
{"id": "ns_bc8c1aa1"}
```

### remove-admin

Remove the admin role from  a local user:
```
api-cli ns.users set-admin --data '{"name": "pluto"}'
```

Response example:
```json
{"result": "success"}
```

## ns.threatshield

Manage banip and adguard configuration.

### list-blocklist

List current blocklist:
```
api-cli ns.threatshield list-blocklist
```

Response example:
```json
{
  "data": [
    {
      "name": "yoroimallvl1",
      "type": "enterprise",
      "enabled": false,
      "confidence": 10,
      "description": "Yoroi malware - Level 1"
    },
    {
      "name": "yoroimallvl2",
      "type": "enterprise",
      "enabled": false,
      "confidence": 8,
      "description": "Yoroi malware - Level 2"
    }
  ]
}
```

Fields:
- type can be `enterprise` or `community`
- confidence can be `-1` if the value is not available


### list-settings

Show current banip settings:
```
api-cli ns.threatshield list-settings
```

Response example:
```json
{"data": {"enabled": true}}
```

### edit-settings

Configure banip settings:

- `enabled`: disable or enable banip (true or false).
- `ban_logprerouting`: Log suspicious packets in the prerouting chain (true or false).
- `ban_loginput`: Log suspicious packets in the WAN-input chain (true or false).
- `ban_logforwardwan`: Log suspicious packets in the WAN-forward chain (true or false).
- `ban_logforwardlan`: Log suspicious packets in the LAN-forward chain (true or false).
- `ban_loglimit`: Enable or disable scanning of logfiles (true or false).
- `ban_logcount`: Specify how many times an IP must appear in the log to be considered suspicious (integer).
- `ban_logterm`: List of regex entries for logfile parsing (list of strings).
- `ban_icmplimit`: Enable or disable icmp DoS detection (true or false).
- `ban_synlimit`: Enable or disable syn DoS detection (true or false).
- `ban_udplimit`: Enable or disable udp DoS detection (true or false).
- `ban_nftexpiry`: Set the ban expiry, format is `1d` for 1 day, `2h` for 2 hours, `1m` for 1 minute. (string)


```bash
api-cli ns.threatshield edit-settings --data '{"enabled": true, "ban_logprerouting": true, "ban_loginput": true, "ban_logforwardwan": true, "ban_logforwardlan": true, "ban_loglimit": false, "ban_logcount": 5, "ban_logterm": ["regex1", "regex2"], "ban_icmplimit": true, "ban_synlimit": true, "ban_udplimit": true, "ban_nftexpiry": "1d"}'
```

Response example:
```json
{"message": "success"}
```

### edit-blocklist

Enable or disable a blocklist:
```
api-cli ns.threatshield edit-blocklist --data '{ "blocklist": "blocklist_name", "enabled": True }'
```

### list-allowed

List addresses always allowed:
```
api-cli ns.threatshield list-allowed
```

Response example:
```json
{
  "data": [
    {
      "address": "10.10.0.221/24",
      "description": "WAN"
    },
    {
      "address": "52:54:00:6A:50:BF",
      "description": "my MAC address"
    }
  ]
}
```

### add-allowed

Add an address which is always allowed:
```
api-cli ns.threatshield add-allowed --data '{"address": "1.2.3.4", "description": "my allow1"}'
```

The `address` field can be an IPv4/IPv6, a CIDR, a MAC or host name

Response example:
```json
{"message": "success"}
```

It can raise the following validation errors:
- `address_already_present` if the address is already inside the allow list

### edit-allowed

Change the description of an address already insie the allow list:
```
api-cli ns.threatshield edit-allowed --data '{"address": "1.2.3.4", "description": "my new desc"}'
```

Response example:
```json
{"message": "success"}
```

It can raise the following validation errors:
- `address_not_found` if the address is not inside the allow list

### delete-allowed

Delete an address from the allow list:
```
api-cli ns.threatshield delete-allowed --data '{"address": "1.2.3.4"}'
```

Response example:
```json
{"message": "success"}
```

It can raise the following validation errors:
- `address_not_found` if the address is not inside the allow list

### list-blocked

List blocked addresses from the local blocklist:
```
api-cli ns.threatshield list-blocked
```

Response example:
```json
{
  "data": [
    {
      "address": "10.10.0.221/24",
      "description": "WAN"
    },
    {
      "address": "52:54:00:6A:50:BF",
      "description": "my MAC address"
    }
  ]
}
```

### add-blocked

Add an address to the block list:
```
api-cli ns.threatshield add-blocked --data '{"address": "1.2.3.4", "description": "my block1"}'
```

The `address` field can be an IPv4/IPv6, a CIDR, a MAC or host name

Response example:
```json
{"message": "success"}
```

It can raise the following validation errors:
- `address_already_present` if the address is already inside the block list

### edit-blocked

Change the description of an address already inside the block list:
```
api-cli ns.threatshield edit-blocked --data '{"address": "1.2.3.4", "description": "my new desc"}'
```

It can raise the following validation errors:
- `address_not_found` if the address is not inside the allow list

### delete-blocked

Delete an address from the block list:
```
api-cli ns.threatshield delete-blocked --data '{"address": "1.2.3.4"}'
```

Response example:
```json
{"message": "success"}
```

It can raise the following validation errors:
- `address_not_found` if the address is not inside the block list

### dns-list-blocklist

List current dns blocklist:
```
api-cli ns.threatshield dns-list-blocklist
```

Response example:
```json
{
  "data": [
    {
      "name": "malware_lvl2",
      "type": "community",
      "enabled": true,
      "confidence": 8,
      "description": "Threat Intelligence Feed"
    },
    {
      "name": "yoroi_malware_level1",
      "type": "enterprise",
      "enabled": false,
      "confidence": -1,
      "description": "malware"
    }
  ]
}
```

### dns-edit-blocklist

Enable or disable a dns blocklist:
```
api-cli ns.threatshield dns-edit-blocklist --data '{ "blocklist": "blocklist_name", "enabled": True }'
```

Response example:
```json
{"message": "success"}
``` 

### dns-list-settings

Show current dns adblock settings:
```
api-cli ns.threatshield dns-list-settings
```

Response example:
```json
{"data": {"enabled": true, "zones": ["lan"]}}
```

### dns-edit-settings

Edit dns adblock settings:
```
api-cli ns.threatshield dns-edit-settings --data '{"enabled": true, "zones": ["lan"]}'
```

Response example:
```json
{"message": "success"}
```

### dns-list-allowed

List domains always allowed:
```
api-cli ns.threatshield dns-list-allowed
```

Response example:
```json
{
  "data": [
    {
      "address": "nethesis.it"
    }
  ]
}
```

### dns-add-allowed

Add a domain which is always allowed:
```
api-cli ns.threatshield dns-add-allowed --data '{"address": "nethesis.it", "description": "my allow1"}'
```

Response example:
```json
{"message": "success"}
```

### dns-edit-allowed

Change the description of an address already insie the allow list:
```
api-cli ns.threatshield dns-edit-allowed --data '{"address": "nethesis.it", "description": "my new desc"}'
```

Response example:
```json
{"message": "success"}
```

### dns-delete-allowed

Delete an address from the allow list:
```
api-cli ns.threatshield dns-delete-allowed --data '{"address": "nethesis.it"}'
```

Response example:
```json
{"message": "success"}
```

### dns-list-bypass

List hosts that can bypass the adblock DNS redirect:
```
api-cli ns.threatshield dns-list-bypass
```

Response example:
```json
{"data": ["192.168.1.22"]}
```

### dns-add-bypass

Add a host that can bypass the adblock DNS redirect:
```
api-cli ns.threatshield dns-add-bypass --data '{"address": "192.168.1.22"}'
```

Response example:
```json
{"message": "success"}
```

### dns-delete-bypass

Delete a host that can bypass the adblock DNS redirect:
```
api-cli ns.threatshield dns-delete-bypass --data '{"address": "192.168.1.22"}'
```

Response example:
```json
{"message": "success"}
```

## ns.qos

Allows to configure QoS for each network interface available.

### list

List all QoS rules present in `/etc/config/qosify`:

```bash
api-cli ns.qos list
```

Example response:

```json
{
  "rules": [
    {
      "interface": "wan",
      "device": "eth1",
      "disabled": true,
      "upload": 100,
      "download": 100
    },
    {
      "interface": "VM",
      "device": "eth3",
      "disabled": true,
      "upload": 5,
      "download": 5
    }
  ]
}
 ```

### add

Add a new QoS rule:

```bash
api-cli ns.qos add --data '{"interface": "VM", "disabled": true, "upload": 5, "download": 5}'
```

Example response:

```json
{
  "message": "success"
}
```

### edit

Edit an existing QoS rule:

```bash
api-cli ns.qos edit --data '{"interface": "VM", "disabled": true, "upload": 5, "download": 5}'
```

Example response:

```json
{
  "message": "success"
}
```

### delete

Delete an existing QoS rule:

```bash
api-cli ns.qos delete --data '{"interface": "VM"}'
```

### set-status

Disable or enable an existing QoS rule:

```bash
api-cli ns.qos set-status --data '{"interface": "VM", "disabled": true}'
```

Example response:

```json
{
  "message": "success"
}
```

## ns.netmap

Manage netmap rules.

### list-rules

List existing netmap rules.
```
api-cli ns.netmap list-rules
```

Respose example:
```json
{
  "rules": [
    {
      "name": "myrule",
      "src": "10.50.51.0/24",
      "device_in": [
        "eth0"
      ],
      "device_out": [
        "eth1"
      ],
      "map_from": "10.10.10.0/24",
      "map_to": "192.168.1.0/24",
      "id": "ns_b829ca2d"
    },
    {
      "name": "myrule",
      "dest": "10.51.52.0/24",
      "device_in": [],
      "device_out": [],
      "map_from": "10.10.10.0/24",
      "map_to": "192.168.1.0/24",
      "id": "ns_c365af3b"
    }
  ]
}
```

### list-devices

List available devices:
```
api-cli ns.netmap list-devices
```

Reponse example:
```json
{
  "devices": [
    {
      "device": "eth2",
      "interface": null
    },
    {
      "device": "br-lan",
      "interface": "lan"
    },
    {
      "device": "tuntun1",
      "interface": "tun1"
    }
  ]
}
```

### add-rule

Add new netmap rules.

Add a destination rule:
```
api-cli ns.netmap add-rule --data '{"name": "myrule", "src": "10.50.51.0/24", "dest": "", "device_in": ["eth0"], "device_out": ["eth1"], "map_from": "10.10.10.0/24", "map_to": "192.168.1.0/24"}'
```

Add a source rule:
```
api-cli ns.netmap add-rule --data '{"name": "myrule", "src": "", "dest": 10.50.51.0/24"", "device_in": [], "device_out": ["eth1"], "map_from": "10.10.10.0/24", "map_to": "192.168.1.0/24"}'
```

Response example:
```json
{"id": "ns_9a553fa2"}
```

The API may rise the following errors:
- name_too_long: if the length of `name` is greater than 120 characters
- src_or_dest: if both `src` and `dest` are non-empty
- map_from_invalid_format: if `map_from` is not a valid IP network format
- map_to_invalid_format: if `map_to` is not a valid IP network format
- src_invalid_format: if `src` is provided and is not a valid IP network format
- dest_invalid_format: if `dest` is provided and is not a valid IP network format

### edit-rule

Edit an existing netmap rule:
```
api-cli ns.netmap edit-rule --data '{"id": "ns_9a553fa2", "name": "myrule2", "src": "10.50.51.0/24", "dest": "", "device_in": ["eth0"], "device_out": ["eth1"], "map_from": "10.10.10.0/24", "map_to": "192.168.1.0/24"}'
```

Response example:
```json
{"id": "ns_9a553fa2"}
```

The API may raise the same errors of the `add-rule` call.

### delete-rule

Delete an existing netmap rule:
```
api-cli ns.netmap delete-rule --data '{"id": "ns_9a553fa2"}'
```

Response example:
```json
{"result": "success"}
```

The API may raise a `rule_does_not_exists` error if the rule does not exist.

## ns.mwan

Automates configuration of MWANs.

### index_policies

List all MWAN policies:

```bash
api-cli ns.mwan index_policies
```

Example response:

```json
{
   "values": [
      {
         "label": "Default",
         "members": {
            "10": [
               {
                  "interface": "RED_1",
                  "metric": "10",
                  "name": "ns_RED_1_M10_W100",
                  "status": "notracking",
                  "weight": "100"
               },
               {
                  "interface": "RED_2",
                  "metric": "10",
                  "name": "ns_RED_2_M10_W100",
                  "status": "notracking",
                  "weight": "100"
               }
            ]
         },
         "name": "ns_default",
         "type": "balance"
      }
   ]
}
```

Note: `type` is just a helper field, always refer to how members are disposed in the `members` field.

### store_policy

Store a new MWAN policy:

```bash
api-cli ns.mwan store_policy --data '{"name": "Default","interfaces": [{"name": "RED_1","metric": 10,"weight": "100"},{"name": "RED_2","metric": 10,"weight": "100"}]}'
```

Parameters:

- `name`: friendly name for the policy
- `interfaces`: list of interfaces to be included in the policy, each interface must have the following fields:
   - `name`: name of the interface
   - `metric`: metric to be used for the interface
   - `weight`: weight to be used for the interface

Example response:

```json
{
   "message": "success"
}
```

### edit_policy

Edit an existing MWAN policy:

```bash
api-cli ns.mwan edit_policy --data '{"name": "ns_default","label": "Default","interfaces": [{"name": "RED_1","metric": 10,"weight": "100"},{"name": "RED_2","metric": 20,"weight": "100"}]}'
```

Parameters:

- `name`: name of the policy to be edited
- `label`: friendly name for the policy
- `interfaces`: list of interfaces to be included in the policy, each interface must have the following fields:
   - `name`: name of the interface
   - `metric`: metric to be used for the interface
   - `weight`: weight to be used for the interface

Example response:

```json
{
   "message": "success"
}
```

### delete_policy

Deletes an existing MWAN policy:

```bash
api-cli ns.mwan delete_policy --data '{"name": "ns_test"}'
```

Parameters:

- `name`: name of the policy to be deleted

Example response:

```json
{
   "message": "success"
}
```

### index_rules

List all MWAN rules (ordered by priority):

```bash
api-cli ns.mwan index_rules
```

Example response:

```json
{
  "values": [
    {
      "label": "Default Rule",
      "name": "ns_default_rule",
      "policy": {
        "label": "Default",
        "name": "ns_default"
      },
      "protocol": "all",
      "source_address": "1.1.1.1/30",
      "destination_address": "10.0.0.1/20",
      "sticky": false
    }
  ]
}
```

Beware, additional field `ns_src` and `ns_dst` with a `id` representing the firewall object might be present in the
response, they are the object replacement of `source_address` and `destination_address` respectively, consider them with
higher priority over the other fields.

Note: field `protocol`, `source_address` and `destination_address` can be missing from the response, in that case
consider them to be set as `any`.

### store_rule

Store a new MWAN rule:

```bash
api-cli ns.mwan store_rule --data '{"name": "hello","policy": "ns_default","protocol": "all","source_address": "","source_port": "","destination_address": "","destination_port": "", "sticky": false}'
```

Parameters:
- `name`: friendly name for the rule
- `policy`: name of the policy to be used, must be present in the list of policies
- `protocol`: protocol to be used, can be `all`, `tcp`, `udp`, `icmp` or `esp`
- `source_address`: source address to be used, can be a single IP, a CIDR or empty for `any`
- `source_port`: source port to be used, can be a single port, a range or empty for `any`
- `destination_address`: destination address to be used, can be a single IP, a CIDR or empty for `any`
- `destination_port`: destination port to be used, can be a single port, a range or empty for `any`
- `sticky`: Allow traffic from the same source IP address within the timeout limit to use same wan interface as prior session (Boolean default false)
- `ns_src`: source address object id, will override `source_address`
- `ns_dst`: destination address object id, will override `destination_address`

Example response:

```json
{
   "message": "success"
}
```

### order_rules

Order rules by priority (highest priority first):

```bash
api-cli ns.mwan order_rules --data '{"rules": ["ns_hello", "ns_test", "ns_default_rule"]}'
```

Parameters:
- `rules`: list of rule names in the order they should be applied

Example response:

```json
{
   "message": "success"
}
```

### delete_rule

Deletes an existing MWAN rule:

```bash
api-cli ns.mwan delete_rule --data '{"name": "ns_test"}'
```

Parameters:
- `name`: name of the rule to be deleted

Example response:

```json
{
   "message": "success"
}
```

### edit_rule

Edit an existing MWAN rule:

```bash
api-cli ns.mwan edit_rule --data '{"name": "ns_hello","policy": "ns_default", "label": "hello", "protocol": "all","source_address": "","source_port": "","destination_address": "","destination_port": "", "sticky": false}'
```

Parameters:
- `name`: name of the rule to be edited
- `policy`: name of the policy to be used, must be present in the list of policies
- `label`: friendly name for the rule
- `protocol`: protocol to be used, can be `all`, `tcp`, `udp`, `icmp` or `esp`
- `source_address`: source address to be used, can be a single IP, a CIDR or empty for `any`
- `source_port`: source port to be used, can be a single port, a range or empty for `any`
- `destination_address`: destination address to be used, can be a single IP, a CIDR or empty for `any`
- `destination_port`: destination port to be used, can be a single port, a range or empty for `any`
- `sticky`: Allow traffic from the same source IP address within the timeout limit to use same wan interface as prior session (Boolean default false)
- `ns_src`: source address object id, will override `source_address`
- `ns_dst`: destination address object id, will override `destination_address`

Example response:

```json
{
   "message": "success"
}
```

### clear_config

Clears all MWAN configuration (useful if you want to start over configuring), will still have pending changes until you commit them.

```bash
api-cli ns.mwan clear_config
```

Example response:

```json
{
   "message": "success"
}
```

### list_object_suggestions

List all available objects that can be used in MWAN rules:

```bash
api-cli ns.mwan list_object_suggestions
```

Example response:

```json
{
  "objects": {
    "ns_src": [
      {
        "name": "h1",
        "family": "ipv4",
        "id": "ns_04fadb5c",
        "singleton": true,
        "type": "host_set"
      }
    ],
    "ns_dst": [
      {
        "name": "MySet",
        "description": "Mydomain set",
        "family": "ipv4",
        "id": "myset",
        "type": "domain_set"
      }
    ]
  }
}
```

## ns.nat

Manage all NAT rules.

### list-rules

List NAT rules:
```
api-cli ns.nat list-rules
```

Output example:
```json
{
  "rules": [
    {
      "name": "source_NAT1_vpm",
      "src": "*",
      "src_ip": "192.168.55.0/24",
      "dest_ip": "10.20.30.0/24",
      "target": "SNAT",
      "snat_ip": "10.44.44.1",
      "id": "cfg0b93c8"
    },
    {
      "name": "masquerade",
      "src": "lan",
      "src_ip": "192.168.1.0/24",
      "dest_ip": "10.88.88.0/24",
      "target": "MASQUERADE",
      "id": "cfg0c93c8"
    },
    {
      "name": "cdn_via_router",
      "src": "lan",
      "src_ip": "192.168.1.0/24",
      "dest_ip": "192.168.50.0/24",
      "target": "ACCEPT",
      "id": "cfg0d93c8"
    },
    {
      "name": "SNAT_NSEC7_style",
      "src": "wan",
      "src_ip": "192.168.1.44",
      "target": "SNAT",
      "snat_ip": "10.20.30.5",
      "id": "cfg0e93c8"
    }
  ]
}
```

### add-rule

Add a new NAT rule:
```
api-cli ns.nat add-rule --data '{"name":"r1","src":"lan","src_ip":"7.8.9.1","dest_ip":"1.2.3.4","target":"SNAT","snat_ip":"4.5.6.7"}'
```

Response example:
```json
{"id": "ns_75bec982"}
```

The API can raise the following validation exceptions:

- `name_too_long`: the name field length must not exceed 120 chars
- `invalid_target`: valid targets are `ACCEPT`, `MASQUERADE`, `SNAT`

### edit-rule

Edit an existing NAT rule:
```
api-cli ns.nat edit-rule --data '{"id": "ns_75bec982", "name":"r1","src":"lan","src_ip":"7.8.9.1","dest_ip":"1.2.3.4","target":"SNAT","snat_ip":"4.5.6.7"}'
```

Response example:
```json
{"id": "ns_75bec982"}
```

### delete-rule

Delete an existing NAT rule:
```
api-cli ns.nat delete-rule --data '{"id": "ns_75bec982"}'
```

Response example:
```json
{"result": "success"}
```

## ns.plug

Manager registration to NethSecurity controller.

### status

Check the status of the registration:
```
api-cli ns.plug status
```

Response example with connected machine:
```json
{
  "status": "connected",
  "address": "172.19.64.2",
  "server": "https://controller.nethsecurity.org",
  "unit_name": "NethSec",
  "unit_id": "94615a9e-2fae-4ac4-91b0-6c03e624ab48",
  "tls_verify": false,
  "push_status": "enabled",
  "push_last_sent": 1727703300
}
```

Response example for an unconfigured machine:
```json
{
  "status": "unregistered",
  "address": null,
  "server": null,
  "unit_name": "NethSec",
  "unit_id": "",
  "tls_verify": true,
  "push_status": "disabled",
  "push_last_sent": -1
}
```

Possible values for `status` are `connected`, `unregistered` and `pending`.
`address` is null if the status is `unregistered` or `pending`.
`server` is null if the status is `unregistered`.
`push_status` can be `enabled` or `disabled`, it's `enabled` if the server has a valid subscription; if enabled, `push_last_sent` contains the timestamp of last
time the unit has pushed data to the controller.
If `unit_name` has not been previously set, default value is the hostname of the machine.
The `unit_id` is generated from the controller and contained inside the join_code.

### register

Register the device to the NethSecurity controller:
```
api-cli ns.plug register --data '{"join_code": "eyJmcWRuIjoiY29udHJvbGxlci5ncy5uZXRoc2VydmVyLm5ldCIsInRva2VuIjoiMTIzNCIsInVuaXRfaWQiOiI5Njk0Y2Y4ZC03ZmE5LTRmN2EtYjFjNC1iY2Y0MGUzMjhjMDIifQ==", "tls_verify": true, "unit_name": "fw.test.local"}'
```

Response example:
```json
{"result": "success"}
```

### unregister

Unregister the device from the NethSecurity controller:
```
api-cli ns.plug unregister
```

Response example:
```json
{"result": "success"}
```

Please note that the unregister will also cleanup the `unit_name` field.

### restart

Restart the registration process:
```
api-cli ns.plug restart
```

Response example:
```json
{"result": "success"}
```

If the restart fails return a `restart_failed` error.

## ns.netifyd

Manage netifyd sink configuration.

### status

Check the status of the sink confinguration:
```
api-cli ns.netifyd status
```

Response example with connected machine:
```json
{
  "uuid": "QD-SC-WB-N7",
  "enabled": true
}
```

Response example for an unconfigured machine:
```json
{
  "uuid": "QD-SC-WB-N7",
  "enabled": false
}
```

### enable

Enable the sink to Neitfyd cloud:
```
api-cli ns.netifyd enable
```

Response example:
```json
{"result": "success"}
```

### disable

Disable the sink to Neitfyd cloud:
```
api-cli ns.netifyd disable
```

Response example:
```json
{"result": "success"}
```

## ns.controller

This API is designed to be called from the controller:
it simplifies the communication between the controller and the managed devices.

### info

Get the information of the device:
```
api-cli ns.controller info
```

Response example:
```json
{
  "unit_name": "MyFirewall",
  "version": "NethSecurity 8 23.05.2-ns.0.0.2-beta2-88-gd3a896a",
  "subscription_type": "enterprise",
  "system_id": "xxxxxxxxxxxxxxx",
  "ssh_port": 22,
  "fqdn": "fw.local"
}
```

### add-ssh-key

Add a new SSH key to the device:
```
api-cli ns.controller add-ssh-key --data '{"ssh_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQ...."}'
```

Response example:
```json
{"result": "success"}
```

The API does not fail if the key is already present but it will not add it again.
It can raise the error `invalid_ssh_key` if the key is not a valid SSH key.

### remove-ssh-key

Delete an existing SSH key from the device:
```
api-cli ns.controller remove-ssh-key --data '{"ssh_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQ...."}'
```

Response example:
```json
{"result": "success"}
```

The API does not fail if the key is not present but it will not delete it.
It can raise the error `invalid_ssh_key` if the key is not a valid SSH key.


### dump-mwan-events

Dump MWAN events to the controller as a time series.
The function reads all data from last 20 minutes. If the firewall has been rebooted, try to read the whole log.
Returned JSON output can be sent to the controller.
Example:
```
api-cli ns.controller dump-mwan-events
```

```json
{
  "data": [
    {
      "timestamp": 1724221238,
      "wan": "wan",
      "interface": "eth1",
      "event": "offline"
    },
    {
      "timestamp": 1724221243,
      "wan": "wan",
      "interface": "eth1",
      "event": "online"
    }
  ]
}
```

### dumpt-ts-attacks

Dump ThreatShield attacks to the controller as a time series.
An attack is an IP blocked due to a temporary ban (fail2ban behavior).
The function reads all data from last 20 minutes. If the firewall has been rebooted, try to read the whole log.
Returned JSON output can be sent to the controller.

Output example:
```json
{
  "data": [
    {
      "timestamp": 1724230611,
      "ip": "79.10.245.41"
    },
    {
      "timestamp": 1724230781,
      "ip": "79.10.245.41"
    }
  ]
}
```

### dump-ts-malware

Dump ThreatShield malware to the controller as a time series.
A malware is an IP blocked due to a blocklist.
The function reads all data from last 20 minutes. If the firewall has been rebooted, try to read the whole log.

Output example:
```json
{
  "data": [
    {
      "timestamp": 1724230020,
      "src": "123.13.237.76",
      "dst": "192.168.5.3",
      "category": "nethesislvl3v4",
      "chain": "fwd-wan"
    },
    {
      "timestamp": 1724230021,
      "src": "218.21.220.12",
      "dst": "192.168.5.3",
      "category": "nethesislvl3v4",
      "chain": "fwd-wan"
    }
  ]
}
```

### dump-openvpn-connections

Dump OpenVPN connections to the controller as a time series.
The function reads all data from last 20 minutes. If the firewall has been rebooted, data are not available.
Returned JSON output can be sent to the controller.

Output example:
```json
{
  "data": [
    {
      "timestamp": 1724231288,
      "instance": "ns_roadwarrior1",
      "common_name": "giacomo",
      "virtual_ip_addr": "10.9.9.4",
      "remote_ip_addr": "1.2.3.33",
      "start_time": 1724231288,
      "duration": null,
      "bytes_received": null,
      "bytes_sent": null
    }
  ]
}
```

### dump-dpi-stats

Dump DPI stats to the controller as a time series.
The function reads all data from last 20 minutes. If the firewall has been rebooted, data are not available.
Returned JSON output can be sent to the controller.

Output example:
```json
{
  "data": [
    {
      "timestamp": 1724198400,
      "client_address": "fe80::fc54:ff:fe6a:4aa1",
      "client_name": "host1.local"
      "protocol": "icmpv6",
      "bytes": 70
    },
    {
      "timestamp": 1724198400,
      "client_address": "fe80::fc54:ff:fe6a:4aa1",
      "client_name": "host1.local"
      "bytes": 101
    },
    {
      "timestamp": 1724198400,
      "client_address": "fe80::fc54:ff:fe6a:4aa1",
      "client_name": "host1.local"
      "application": "unknown",
      "bytes": 171
    }
  ]
}
```

### dump-openvpn-config

Dump OpenVPN configuration to the controller.
Returned JSON output can be sent to the controller.

Output example:
```json
{
  "data": [
    {
      "instance": "ns_roadwarrior1",
      "name": "myserver1",
      "device": "tunrw1",
      "type": "rw",
    },
    {
      "instance": "ns_tunsrv1",
      "name": "mytunsrv",
      "device": "tunsrv1",
      "type": "server",
    }
  ]
}
```

The `type` field can be `rw` for roadwarrior, `server` for tunnel server, or `client` for tunnel client.

### dump-wan-config

Dump WAN configuration to the controller.
Returned JSON output can be sent to the controller.

Output example:
```json
{
  "data": [
    {
      "interface": "wan",
      "device": "eth1",
      "status": "online"
    },
    {
      "interface": "wan2",
      "device": "eth2",
      "status": "offline"
    }
  ]
}
```

## ns.scan

Scan network to find existing hsots.

### list-interfaces

List all available interfaces:
```
api-cli ns.scan list-interfaces
```

Response example:
```json
{
  "interfaces": [
    {
      "interface": "lan",
      "device": "br-lan"
    }
  ]
}
```

### scan

Scan the given device and return the results:
```
api-cli ns.scan scan --data '{"device": "br-lan"}'
```

Response example:
```json
{
  "hosts": [
    {
      "mac": "54:xx:xx:xx:xx:29",
      "ip": "192.168.1.3",
      "hostname": "",
      "description": "REALTEK"
    },
    {
      "mac": "00:xx:xx:xx:xx:3b",
      "ip": "",
      "hostname": "host.nethserver.org",
      "description": ""
    }
  ]
}
```

## ns.conntrack

List and delete conntrack entries.

### list

List all conntrack entries:

```bash
api-cli ns.conntrack list
```

Example response:

```json
{
   "data": [
      {
         "destination": "192.168.122.155",
         "destination_stats": {
            "bytes": "9996",
            "packets": "119"
         },
         "id": "3363877713",
         "protocol": "icmp",
         "source": "192.168.122.1",
         "source_stats": {
            "bytes": "9996",
            "packets": "119"
         },
         "timeout": "29"
      },
      {
         "destination": "127.0.0.1",
         "destination_port": "8090",
         "destination_stats": {
            "bytes": "2233",
            "packets": "5"
         },
         "id": "4275285926",
         "protocol": "tcp",
         "source": "127.0.0.1",
         "source_port": "53740",
         "source_stats": {
            "bytes": "741",
            "packets": "5"
         },
         "state": "TIME_WAIT",
         "timeout": "5"
      }
   ]
}
```

Fields that might miss from some entries:

- `start_port`
- `end_port`
- `unreplied`
- `state`

### drop

Drop a conntrack entry, use the `id` provided by the `list` command:

```bash
api-cli ns.conntrack drop --data '{"id": "3363877713"}'
```

Example response:

```json
{
   "message": "success"
}
```

Note: if the entry does not exist, the API will still return a `success`, this is to avoid the drop of connection that
already expired.

### drop_all

Drop all conntrack entries:

```bash
api-cli ns.conntrack drop_all
```

Example response:

```json
{
   "message": "success"
}
```

## ns.objects

Manage domain sets and host sets.

### list-domain-sets

List all domain sets:
```
api-cli ns.objects list-domain-sets
```

Response example:
```json
{
  "values": [
    {
      "domain": [
        "www.nethsecurity.org",
        "www.nethserver.org"
      ],
      "family": "ipv4",
      "id": "ns_71b3a490",
      "matches": [],
      "name": "myset",
      "timeout": "600",
      "used": false
    }
  ]
}
```

If `used` field is `true` the domain set is used and the `matches` field will contain the list of matched records where the domain set is used.

### list-hosts

List all hosts including host sets, VPN user, DHCP reservations and DNS records:
```
api-cli ns.objects list-hosts
```

Response example:
```json
{
  "values": [
    {
      "name": "h1",
      "family": "ipv4",
      "ipaddr": [
        "1.2.3.4"
      ],
      "id": "objects/ns_04fadb5c",
      "singleton": true,
      "subtype": "host",
      "used": true,
      "matches": [
        "firewall/ns_9addc806",
        "objects/ns_3cf75e0e"
      ]
    },
    {
      "name": "myset",
      "family": "ipv4",
      "ipaddr": [
        "1.2.3.4",
        "objects/ns_04fadb5c"
      ],
      "id": "objects/ns_3cf75e0e",
      "singleton": false,
      "subtype": "host_set",
      "used": false,
      "matches": []
    },
    {
      "id": "dhcp/ns_60a053b9",
      "name": "g1",
      "type": "dns_record",
      "subtype": "dns_record",
      "family": "ipv4",
      "ipaddr": [
        "8.8.8.8"
      ],
      "used": false,
      "matches": []
    }
  ]
}
```

Available subtypes are `host`, `cidr`, `range`, `dhcp_static_lease`, `dns_record`, `host_set`, `vpn_user`.

### add-domain-set

Create a new domain set:
```
api-cli ns.objects add-domain-set --data '{"name": "myset", "domain": ["www.nethsecurity.org", "www.nethserver.org"], "family": "ipv4"}'
```

Response example:
```json
{"id": "ns_21d2fee8"}
```

It can raise the following validation errors:
- `invalid_family` if the family is not `ipv4` or `ipv6`
- `name_too_long`: if the length of `name` is greater than 16 characters

### edit-domain-set

Edit an existing domain set:
```
api-cli ns.objects edit-domain-set --data '{"id": "ns_71b3a490", "name": "myset_new", "domain": ["www.test.org", "www.nethserver.org"], "family": "ipv4"}'
```

Response example:
```json
{"id": "ns_21d2fee8"}
```

It can raise the following validation errors:
- `invalid_family` if the family is not `ipv4` or `ipv6`
- `name_too_long`: if the length of `name` is greater than 16 characters
- `domain_set_does_not_exists` if the domain set does not exist

### delete-domain-set

Delete an existing domain set:
```
api-cli ns.objects delete-domain-set --data '{"id": "ns_71b3a490"}'
```

Response example:
```json
{"message": "success"}
```

It can raise the following validation errors:
- `invalid_family` if the family is not `ipv4` or `ipv6`
- `domain_set_is_used` if the domain set is used in a rule. Error example:
   ```json
  {"validation": {"errors": [{"parameter": "id", "message": "domain_set_is_used", "value": ["firewall/ns_xxx"]}]}}
  ```

### add-host-set

Create a new host set:
```
api-cli ns.objects add-host-set --data '{"name": "myset", "family": "ipv4", "ipaddr": ["1.2.3.4", "objects/ns_04fadb5c"]}'
```

Response example:
```json
{"id": "ns_21d2fee8"}
```

It can raise the following validation errors:
- `invalid_family` if the family is not `ipv4` or `ipv6`
- `name_too_long` if the length of `name` is greater than 16 characters
- `invalid_name` if the name contains special chars, it must contains onlu number and letters
- `object_does_not_exists` if the referenced object does not exist
- `loop_detected` if the object references itself
- `invalid_ipaddr` if the IP address is not a valid IPv4/IPv6 address depending on the family

### edit-host-set

Edit an existing host set:
```
api-cli ns.objects edit-host-set --data '{"id": "ns_71b3a490", "name": "myset_new", "family": "ipv4", "ipaddr": ["6.7.8.9"]}'
```

Response example:
```json
{"id": "ns_21d2fee8"}
```

It may raise the following validation errors:
- `host_set_does_not_exists` if the host set does not exist
- `invalid_family` if the family is not `ipv4` or `ipv6`
- `name_too_long` if the length of `name` is greater than 16 characters
- `invalid_name` if the name contains special chars, it must contains only number and letters
- `object_does_not_exists` if the referenced object does not exist
- `loop_detected` if the object references itself
- `invalid_ipaddr` if the IP address is not a valid IPv4/IPv6 address depending on the family

### delete-host-set

Delete an existing host set:
```
api-cli ns.objects delete-host-set --data '{"id": "ns_71b3a490"}'
```

Response example:
```json
{"message": "success"}
```

It may raise the following validation errors:
- `host_set_does_not_exists` if the host set does not exist
- `host_set_is_used` if the host set is used in a rule, error example:
  ```json
  {"validation": {"errors": [{"parameter": "id", "message": "host_set_is_used", "value": ["firewall/ns_allow_OpenVPNRW1"]}]}}
  ```
### get-info

Return the information about the object matches:
```
api-cli ns.objects get-info --data '{"ids": ["firewall/ns_71b3a490"]}'
```

Response example:
```json
{
  "info": {
    "firewall/ns_9addc806": {
      "database": "firewall",
      "id": "ns_9addc806",
      "name": "t1",
      "type": "rule"
    }
  }
}
```

## ns.nathelpers

List and manage NAT helpers.

### list-nat-helpers

List all NAT helpers and their configuration:
```bash
api-cli ns.nathelpers list-nat-helpers
```

Response example:
```json
{
  "values": [
    {
      "enabled": false,
      "loaded": false,
      "name": "nf_conntrack_amanda",
      "params": {
        "master_timeout": "300",
        "ts_algo": "kmp"
      }
    },
    {
      "enabled": false,
      "loaded": false,
      "name": "nf_conntrack_broadcast",
      "params": {}
    },
    {
      "enabled": false,
      "loaded": false,
      "name": "nf_nat_sip",
      "params": {}
    }
  ]
}
```

The `enabled` attribute tells if the user has activated the NAT helper; the `loaded` attribute tells if the module of the NAT helper is currently loaded in the kernel.

Every NAT helper has its own set of parameters; this API returns either the configured value for each parameter (if the helper is enabled) or the default value.

### edit-nat-helper

Enable or disable a NAT helper and set its parameters.
```bash
api-cli ns.nathelpers edit-nat-helper --data '{"name": "nf_conntrack_h323", "enabled": true, "params": {"callforward_filter": "N", "default_rrq_ttl": "600", "gkrouted_only": "1"}}'
```

Response example:
```json
{"reboot_needed": false}
```

Required parameters:
- `name`: name of the NAT helper
- `enabled`: `true` to activate the NAT helper, `false` to disable it

It may raise the following validation errors:
- `nat_helper_not_found`: if a NAT helper named `name` does not exist

The output attribute `reboot_needed` tells if a reboot of the unit is required to apply the changes to the NAT helper. A reboot is needed when:
- changing the parameters of a NAT helper already loaded in the kernel
- disabling a NAT helper

If `enabled` is `false`, all parameter changes are ignored and not applied.

## ns.report

Generate data for reports. Some reports are cached.

### tsip-malware-report

Report the number of blocked IPs by Threat Shield IP using the blocklists.
Data are searched from the last 24 hours, inside `/var/log/messages` and `/var/log/messages.1.gz` so data can be incomplete
if the logs do not contain the full 24 hours.
Result is cached for 15 minutes.
Usage example:
```
api-cli ns.report tsip-malware-report
```

Output example:
```json
{"first_seen":1723154401,"malware_count":84816,"malware_by_hour":[[0,5695],[1,5351],[2,5470],[3,6187],[4,5892],[5,5268],[6,5168],[7,5457],[8,6447],[9,5573],[10,5479],[11,5112],[12,4969],[13,4917],[14,4879],[15,2952],[16,0],[17,0],[18,0],[19,0],[20,0],[21,0],[22,0],[23,0]],"malware_by_category":{"nethesislvl3v4":76899,"yoroimallvl2v4":6979,"yoroisusplvl2v4":122,"blocklistv4":335},"malware_by_chain":{"fwd-wan":32933,"inp-wan":51402}}
```

### tsip-attack-report

Report the number of blocked IPs by Threat Shield IP using the regexp over the log (like fail2ban).
Data are searched from the last 24 hours, inside `/var/log/messages` and `/var/log/messages.1.gz` so data can be incomplete
if the logs do not contain the full 24 hours.
Result is cached for 15 minutes.
Usage example:
```
api-cli ns.report tsip-attack-report
```

Output example:
```json
{"first_seen": 1724021271, "attack_count": 149, "attack_by_ip": [["xx.xx.177.217", 30], ["xx.xx.60.242", 30], ], "attack_by_hour": [[0, 7], [1, 49], [2, 39], [3, 11], [4, 0], [5, 1], [6, 5], [7, 0], [8, 0], [9, 0], [10, 4], [11, 31], [12, 2], [13, 0], [14, 0], [15, 0], [16, 0], [17, 0], [18, 0], [19, 0], [20, 0], [21, 0], [22, 0], [23, 0]]}
```

### mwan-report

Report the online/offline events for each wan.
Data are searched from the last 24 hours, inside `/var/log/messages` and `/var/log/messages.1.gz` so data can be incomplete
if the logs do not contain the full 24 hours.
Result is cached for 5 minutes.
Usage example:
```
api-cli ns.report mwan-report
```

Output example:
```json
{
  "total_online": 5,
  "total_offline": 3,
  "events_by_wan": {
    "wan": [
      [
        1723185855,
        1
      ],
      [
        1723198098,
        0
      ],
    ],
    "wan2": [
      [
        1723185858,
        1
      ],
      [
        1723197224,
        0
      ],
      [
        1723197354,
        1
      ],
      [
        1723198098,
        0
    ]
  }
}
```

The `events_by_wan` object can be used to generate a scattered chart. Each element of the array is a pair of `timestamp,event`.
Where `event` is `1` when there is an `online` event, `0` otherwise.

### ovpnrw-list-days

OpenVPN stores data inside a sqlite datbase which is lost upon reboot. This command will list all the days where data is available.
Usage example:
```
api-cli ns.report ovpnrw-list-days --data '{"instance": "ns_roadwarrior1"}'
```

Output example:
```json
{
  "days": [
    "2024-08-07",
    "2024-08-08",
    "2024-08-09"
  ]
}
```

### ovpnrw-clients-by-day

Report the number of clients connected to the OpenVPN server for a specific day.
Usage example:
```
api-cli ns.report ovpnrw-clients-by-day --data '{"instance": "ns_roadwarrior1", "day": "2024-08-07"}'
```

Output example:
```json
{
  "clients": [
    {
      "common_name": "goofy",
      "virtual_ip_addr": "10.9.9.2",
      "remote_ip_addr": "93.41.xx.xx",
      "start_time": 1723119680,
      "duration": 2766,
      "bytes_received": 5532614,
      "bytes_sent": 15296388
    }
  ]
  ```

### ovpnrw-count-clients-by-hour

Report the number of clients connected to the OpenVPN server for a specific day, aggregated by hour.
Usage example:
```
api-cli ns.report ovpnrw-count-clients-by-hour --data '{"instance": "ns_roadwarrior1", "day": "2024-08-07"}'
```

Output example:
```json
{"hours":[["00",0],["01",0],["02",0],["03",0],["04",0],["05",0],["06",0],["07",0],["08",0],["09",0],["10",0],["11",0],["12",2],["13",0],["14",0],["15",0],["16",0],["17",0],["18",0],["19",0],["20",1],["21",0],["22",1],["23",0]]}
```

### ovpnrw-bytes-by-hour

Report the total traffic of clients connected to the OpenVPN server for a specific day, aggregated by hour.
Usage example:
```
api-cli ns.report ovpnrw-bytes-by-hour --data '{"instance": "ns_roadwarrior1", "day": "2024-08-07"}'
```

Output example:
```json
{"hours":[["00",0],["01",0],["02",0],["03",0],["04",0],["05",0],["06",0],["07",0],["08",0],["09",0],["10",0],["11",0],["12",7898738814],["13",0],["14",0],["15",0],["16",0],["17",0],["18",0],["19",0],["20",11086216],["21",0],["22",43658241],["23",0]]}
```

### ovpnrw-bytes-by-hour-and-user

Report the total traffic of a specific client connected to the OpenVPN server for a specific day, aggregated by hour.
Usage example:
```
api-cli ns.report ovpnrw-bytes-by-hour-and-user --data '{"instance": "ns_roadwarrior1", "day": "2024-08-07", "user": "goofy"}'
```

Output example:
```json
{"hours":[["00",0],["01",0],["02",0],["03",0],["04",0],["05",0],["06",0],["07",0],["08",0],["09",0],["10",0],["11",0],["12",7877909812],["13",0],["14",0],["15",0],["16",0],["17",0],["18",0],["19",0],["20",0],["21",0],["22",0],["23",0]]}
```

### latency-and-quality-report

Report latency metrics (minimum, maximum and average) and connectivy quality data (packet delivery rate) for every host configured in Netdata fping configuration file, located at `/etc/netdata/fping.conf`.
Usage example:
```
api-cli ns.report latency-and-quality-report
```

Output example:
```json
{
  "8.8.8.8": {
    "latency": {
      "labels": [
        "time",
        "minimum",
        "maximum",
        "average"
      ],
      "data": [
        [
          1731485630,
          9.2926149,
          17.3652723,
          11.2476048
        ],
        [
          1731485262,
          9.2831232,
          17.3944183,
          11.5604364
        ],
        [
          1731484894,
          9.294786,
          18.153445,
          11.376502
        ]
      ]
    },
    "quality": {
      "labels": [
        "time",
        "returned"
      ],
      "data": [
        [
          1731485630,
          100
        ],
        [
          1731485262,
          99.8152174
        ],
        [
          1731484894,
          100
        ]
      ]
    }
  },
  "1.1.1.1": {
    "latency": {
      "labels": [
        "time",
        "minimum",
        "maximum",
        "average"
      ],
      "data": [
        [
          1731485630,
          14.8992382,
          25.0276303,
          17.3071943
        ],
        [
          1731485262,
          14.8918498,
          23.8407958,
          17.3052552
        ],
        [
          1731484894,
          14.8776663,
          24.2058399,
          17.0578876
        ]
      ]
    },
    "quality": {
      "labels": [
        "time",
        "returned"
      ],
      "data": [
        [
          1731485630,
          100
        ],
        [
          1731485262,
          99.8152174
        ],
        [
          1731484894,
          100
        ]
      ]
    }
  }
}
```

## ns.snort

Configure Snort IDS.

### settings

Returns the configuration set for `snort`.

```bash
api-cli ns.snort settings
```

Response example:

```json
{
  "enabled": true,
  "ns_policy": "balanced",
  "oinkcode": "123456789"
}
```

### save-settings

Set `snort` configuration

```bash
api-cli ns.snort save-settings --data '{"enabled": true, "ns_policy": "balanced", "oinkcode": "123456789"}'
```

### check-oinkcode

Checks if the provided oinkcode is valid

```bash
api-cli ns.snort check-oinkcode --data '{"oinkcode": "123456789"}'
```

Response example:

```json
{
  "status": "success"
}
```

or

```json
{
  "validation": {
    "oinkcode": "invalid"
  }
}
```

### list-bypasses

List all configured bypasses for Snort IDS.

```bash
api-cli ns.snort list-bypasses
```

Response example:

```json
{
  "bypasses": [
    {
      "direction": "src",
      "protocol": "ipv4",
      "ip": "192.168.100.23",
      "description": "Description"
    },
    {
      "direction": "dst",
      "protocol": "ipv6",
      "ip": "2001:db8::1",
      "description": "Another description"
    }
  ]
}
```

### create-bypass

Create a new bypass rule for Snort IDS.

```bash
api-cli ns.snort create-bypass --data '{"protocol": "ipv4", "ip": "192.168.100.23", "direction": "src", "description": "Description"}'
```

Response example:

```json
{
  "status": "success"
}
```

### delete-bypass

Delete an existing bypass rule for Snort IDS.

```bash
api-cli ns.snort delete-bypass --data '{"protocol": "ipv4", "ip": "192.168.100.23", "direction": "src"}'
```

Response example:

```json
{
  "status": "success"
}
```

### list-disabled-rules

List all disabled rules:

```bash
api-cli ns.snort list-disabled-rules
```

Response example:
```json
{
  "rules": [
    {
      "gid": "1",
      "sid": "24225",
      "description": ""
    }
  ]
}
```

### disable-rule

Disable a specific rule:

```bash
api-cli ns.snort disable-rule --data '{"gid": 1, "sid": 24225, "description": "false_positive"}'
```

Response example:

```json
{
  "status": "success"
}
```

### enable-rule

Enable a previously disabled rule:

```bash
api-cli ns.snort enable-rule --data '{"gid": 1, "sid": 24225}'
```

Response example:

```json
{
  "status": "success"
}
```

### list-suppressed-alerts

List all suppressed alerts:

```bash
api-cli ns.snort list-suppressed-alerts
```

Response example:

```json
{
  "rules": [
    {
      "id": "1:24225",
      "gid": "1",
      "sid": "24225",
      "direction": "by_src",
      "ip": "*.*.*.*",
      "description": "false_positive"
    }
  ]
}
```

### suppress-alert

Suppress a specific alert:

```bash
api-cli ns.snort suppress-alert --data '{"gid": "1", "sid": "24225", "direction": "by_src", "ip": "*.*.*.*", "description": "false_positive"}'
```

Notes:
- `direction` can be `by_src` or `by_dst`
- `ip` and only be IPv4 or CIDR notation


Response example:

```json
{
  "status": "success"
}
```

### delete-suppression

Delete an existing suppression:

```bash
api-cli ns.snort delete-suppression --data '{"gid": "1", "sid": "24225", "direction": "by_dst", "ip": "*.*.*.*"}'
```

Response example:

```json
{
  "status": "success"
}
```

### status

Returns general status for `snort`.

```bash
api-cli ns.snort status
```

Response example:

```json
{
  "enabled": true,
  "alerts": 0,
  "drops": 1
}
```

## ns.wireguard

Configure WireGuard VPN both in Road Warrior and site-to-site mode.

### list-instances

List all WireGuard instances:
```
api-cli ns.wireguard list-instances
```

Response example:
```json
{"instances": ["wg1", "wg2"]}
```

### get-instance-defaults

Generate defaults for a new WireGuard instance:
```
api-cli ns.wireguard get-instance-defaults
```

Response example:
```json
{"listen_port": 51821, "instance": "wg2", "network": "10.210.112.0/24", "routes": ["192.168.100.0/24"], "public_endpoint": "185.96.1.1"}
```

### get-configuration

Return current instance configuration:
```
api-cli ns.wireguard get-configuration --data '{"instance": "wg1"}'
```

Response example:
```json
{"proto": "wireguard", "private_key": "oBwTyCkOgUz29UEvuJZstuAjB87SH4x26MVLxAj152M=", "listen_port": "51820", "addresses": ["10.103.1.1"], "ns_network": "10.103.1.0/24", "ns_public_endpoint": "192.168.122.49", "ns_routes": ["192.168.100.0/24"], "ns_name": "wg1", "disabled": "0", "ns_client_to_client": false, "ns_route_all_traffic": false, "enabled": true}
```

### set-instance

Create a new instance or configure an existing one:
```
api-cli ns.wireguard set-instance --data '{"listen_port": 51820, "name": "wg1", "instance": "wg1", "enabled": true, "network": "10.103.1.0/24", "routes": ["192.168.100.0/24"], "public_endpoint": "192.168.122.49", "dns": [], "user_db": ""}'
```

Response example:
```json
{"result": "success"}
```

Parameters:
- `listen_port`: the port where the WireGuard server listens
- `name`: the name of the instance, it must be unique and it's the name of the interface on the system, it must be a valid interface name and start with `wg`
- `enabled`: `true` to enable the instance, `false` to disable it
- `network`: the network of the WireGuard instance, this is the network where the clients will be connected
- `routes`: the routes that the clients will receive when connected, this parameter is used during the client configuration creation
- `public_endpoint`: the public endpoint of the WireGuard server, it can be an IP address or a domain name, it's used during the client configuration creation
- `dns`: the DNS servers that the clients will receive when connected, it's used during the client configuration creation; this option is honored only if the peer
   has the `ns_route_all_traffic` option set to `1`   
- `user_db`: the user database to use for authentication; if empty, the instance will not be connected to an existing user db and the WireGuard peer will be 
  indipendent; if the user db is set, each new peer must be have a user with the same name in the user db

### remove-instance

Remove an existing instance and all associated peers:
```
api-cli ns.wireguard remove-instance --data '{"instance": "wg1"}'
```

Response example:
```json
{"result": "success"}
```

### set-peer

Create or configure a peer.

Example to create a Road Warrior peer:
```
api-cli ns.wireguard set-peer --data '{"instance": "wg1", "account": "user1", "enabled": true, "route_all_traffic": false, "client_to_client": false, "ns_routes": [], "preshared_key": true}'
```

Example to create a Site-to-Site peer:
```
api-cli ns.wireguard set-peer --data '{"instance": "wg1", "account": "site1", "enabled": true, "route_all_traffic": true, "client_to_client": true, "ns_routes": ["192.168.100.0/24"], "preshared_key": true}'
```

Response example:
```json
{"result": "success"}
```

Parameters:
- `instance`: the name of the WireGuard instance, the instance must exist
- `account`: the name of the peer, it must be unique for the instance; if the instance is connected to a user db, the account must be the name of an existing user
- `enabled`: `true` to enable the peer, `false` to disable it
- `route_all_traffic`: `true` to route all the traffic of the peer through the WireGuard tunnel, `false` to route only the traffic for the `ns_routes` through the tunnel; if this option is set the `dns` option in the instance configuration will be honored
- `client_to_client`: `true` to allow the peer to communicate with other peers connected to the same instance, `false` to disallow it; it must be set to `true`
   if the `route_all_traffic` is set to `true` when the client is not a Road Warrior user but another firewall for a site-to-site connection
- `ns_routes`: the routes that the peer will receive when connected, this parameter is used during the client configuration creation
- `preshared_key`: `true` to generate a new preshared key for the peer, `false` to not use it

### remove-peer

Remove an existing peer:
```
api-cli ns.wireguard remove-peer --data '{"instance": "wg1", "account": "user1"}'
```

Response example:
```json
{"result": "success"}
```

### download-peer-config

Download the configuration of a peer:
```
api-cli ns.wireguard download-peer-config --data '{"instance": "wg1", "account": "user1"}'
```

Response example:
```json
{"config": "# Account: user1 for wg1\n[Interface]\nPrivateKey = 4OoVRqKW0Tur511IL6ttX6iz/EnxrbKzUcAX89bUxlU=\nAddress = 10.103.1.2\n# Custom DNS disabled\n\n[Peer]\nPublicKey = gm1cTae6ub4QGvQcknrb3FbN46x1tbaXJjOQbwX/siM=\nPreSharedKey = /3EbK9a8DW3D7vn0SFp3oK2XSoem05DpG4IxEZ4qoyU=\nAllowedIPs = 192.168.100.0/24,10.103.1.0/24\nEndpoint = 192.168.122.49:51820\nPersistentKeepalive = 25", "qrcode": "G1s0MDszNzs..."}
```

Output parameters:
- `config`: the configuration of the peer, it's in clear text; remember to encode it to base64 before importing it into another firewall
- `qrcode`: the QR code of the configuration, it's a base64 encoded image; it can be used to import the configuration into a mobile app

### import-configuration

Import a WireGuard configuration:
```
api-cli ns.wireguard import-configuration --data '{"config": "base64encodedconfig"}'
```

Response example:
```json
{"result": "success"}
```
