# ns-api

NextSecurity APIs for `rpcd`.

Conventions:
- all APIs must start with `ns.` prefix
- all APIs must read JSON object input from standard input
- all APIs must write a JSON object to standard output: JSON arrays should always be wrapper d inside
  an object due to ubus limitations

List available APIs:
```
ubus -S list | grep '^ns.'
```

APIs can be called directly from ubus.
List 5 top talkers:
```
ubus -S call ns.talkers list '{"limit": 5}'
```

Scripts can be tested by passing arguments to standard input.
Example:
```
echo '{"limit": 5 }' | /usr/libexec/rpcd/ns.talkers call list
```

## Adding a new API

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

## References

External links:
- https://openwrt.org/docs/techref/rpcd
- https://github.com/openwrt/luci/wiki/JsonRpcHowTo
