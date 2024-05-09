---
layout: default
title: APIs
parent: Design
---

# APIs

* TOC
{:toc}

## Reference

All APIs are documented inside the [ns-api](../../packages/ns-api) package.

## Usage

APIs can be called using 4 different methods:
- using `curl` and invoking the API server
- using `api-cli` wrapper that talks with ubus over HTTP
- directly invoking the scripts
- using `ubus` client

### curl

The APIs should always be invoked through the API server on a production environment.
The server will handle the authentication and invoke APIs using ubus.
It also add some extra logic for 2FA and error handling.

First, authenticate the user and obtain a JWT token:
```
curl -s -H 'Content-Type: application/json' -k https://localhost/api/login --data '{"username": "root", "password": "Nethesis,1234"}' | jq -r .token
```

Use the obtained token, to invoke an API:
```
curl -s -H 'Content-Type: application/json' -k  https://localhost/api/ubus/call -H 'Authorization: Bearer <jwt_token>' --data '{"path": "ns.dashboard", "method": "system-info", "payload": {}}' | jq
```

If you need to pass parameters to the API, add them inside the `payload` field:
```
curl -s -H 'Content-Type: application/json' -k  https://localhost/api/ubus/call -H 'Authorization: Bearer <jwt_token>' --data '{"path": "ns.dashboard", "method": "counter", "payload": {"service": "hosts"}}'
```

### api-cli

The `api-cli` wrapper needs valid user credentials.
If no credentials are given, it uses the default ones:

- user: `root`
- password: `Nethesis,1234`

You can use this method to automate the configuration and to test existing APIs.

Exit statuses:
- 0 on success
- 1 on error
- 2 on authentication error

The api-cli command outputs the results on standard output and HTTP errors on standard error.

Example with default credentials:
```
api-cli ns.dashboard system-info
```

If you changed the `root` password, use:
```
api-cli --password mypass ns.dashboard system-info
```

You can pass parameters to the APIs:
```
/usr/bin/api-cli ns.dashboard counter --data '{"service": "hosts"}'
```

Example of bash script:
```bash
hosts=$(echo '{"service": "hosts"}' | /usr/bin/api-cli ns.dashboard counter --data - | jq .result.count)
echo "Known hosts: $hosts"
```

## Conventions

APIs are invoked using the [api-server](../packages/ns-api-server).
The server uses ubus to call the scripts that actually implement the real APIs.
Each script must be executable and follow [RPCD rules](https://openwrt.org/docs/techref/rpcd).
See also [JSONRPC](https://github.com/openwrt/luci/wiki/JsonRpcHowTo) for more info.
 
Each API script should also respect the following conventions:
- all APIs must start with `ns.` prefix
- all APIs must read JSON object input from standard input
- all APIs must write a JSON object to standard output: JSON arrays should always be wrapped inside
  an object due to ubus limitations
- APIs should not commit changes to the configuration database: it's up to the user (or the UI) to commit them and restart the services
- all APIs must follow the error and validation protocols described below

### Error protocol

If the API raises an error, it should return an object like:
```json
{
    "error": "command_failed"
}
```

The `error` field should contain an error message which can be translated inside the UI.
As general rule, the message:

- should describe the error
- should be written in lower case
- should not contain special characters nor spaces

The API server will parse the error and return a 500 HTTP status code and a full response like:
```json
{
  "code": 500,
  "data": {
    "error": "command_failed"
  },
  "message": "command_failed"
}
```

If the API server can't catch the exact error, or the called method does not exists, the API server will return a response like:
```json
{
  "code": 500,
  "data": "exit status 3",
  "message": "ubus call action failed"
}
```

### Validation protocol

The APIs should validate all data that can lead to a service failure.
If the validation fails, it should return an object like:
```json
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

The `errors` fields contains all validation errors.
Fields of the error:
- `parameter`: name of the parameter that threw the error
- `message`: a valuable description of the error, see `error` field above for how to format the message 
- `value`: the value that raised the error (optional)

The API server will catch the validation and return a 400 HTTP code with a response like:
```json
{
  "code": 400,
  "data": {
    "validation": {
      "errors": [
        {
          "message": "mac_already_reserved",
          "parameter": "mac",
          "value": "80:5e:c0:d9:c6:9b"
        }
      ]
    }
  },
  "message": "validation_failed"
}
```

## Create a new API

To add a new API, follow these steps:
1. create an executable file inside `/usr/libexec/rpcd/` directory, like `ns.example`, and restart RPCD
2. create an ACL JSON file inside `/usr/share/rpcd/acl.d`, like `ns.example.json`

APIs can be written using any available programming language.
In this example we are going to use python.

Example for `/usr/libexec/rpcd/ns.example`:
```python
#!/usr/bin/python3

#
# Copyright (C) 2023 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Return the same message given as input parameter

import sys
import json
from nethsec import utils

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
    print(param)
else:
    print(json.dumps(utils.generic_error("invalid_action")))
```

Make the file executable and restart rpcd:
```
chmod a+x /usr/libexec/rpcd/ns.example
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
```json
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

Restart `rpcd`:
```
/etc/init.d/rpcd restart
```

Test the new API:
```
api-cli ns.example say --data '{"message": "hello world"}'
```

