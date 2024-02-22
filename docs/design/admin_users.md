---
layout: default
title: Administrator users
parent: Design
---

# Administrator users

NethSecurity is designed to allow the creation of multiple administrators, each with full control over the system
from the web interface.
Administrators are created using the rpcd interface of OpenWrt. 

To create a new administrator named "goodboy" with the password "mypassword" execute the following commands:
```shell
uci revert rpcd
uci set rpcd.goodboy=login
uci set rpcd.goodboy.username=goodboy
uci add_list rpcd.goodboy.read='*'
uci add_list rpcd.goodboy.write='*'
uci set rpcd.goodboy.password=$(uhttpd -m 'mypassword')
uci commit rpcd
```

Please note that the newly created user does not have SSH access.
Only `root` user can access the system using SSH.
