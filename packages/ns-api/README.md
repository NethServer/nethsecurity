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

# Creating a new API

Conventions:
- all APIs must start with `ns.` prefix
- all APIs must read JSON object input from standard input
- all APIs must write a JSON object to standard output: JSON arrays should always be wrapper d inside
  an object due to ubus limitations

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
