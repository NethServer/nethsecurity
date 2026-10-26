---
layout: default
title: Administrator users
parent: Design
---

# Administrator users

NethSecurity allows multiple administrators, each one logging in to the web interface with a personal account.
An administrator is a local user of the `main` database with a `login` section in the `rpcd` configuration,
created by `ns.users set-admin`. The `rpcd` login has the same password hash as the local user.

To create an administrator named `goodboy` with the password `mypassword`, run as `root`:
```shell
api-cli ns.users add-local-user --data '{"name": "goodboy", "password": "mypassword", "description": "Good boy", "database": "main", "extra": {}}'
api-cli ns.users set-admin --data '{"name": "goodboy", "database": "main"}'
api-cli ns.commit commit --data "{\"changes\": $(ubus call uci changes | jq -c .changes)}"
```

Administrators have no system account, so only `root` can access the system using SSH.

## Superusers

`root` is the superuser, together with two service accounts that act on its behalf:
- the controller account, whose username is in `rpcd.controller.username`
- the remote support account, whose username is in `rpcd.ns_don.username`, present only while remote support is enabled

Only superusers can:
- create, edit or delete administrators, or change their password (`ns.users`)
- promote or demote users (`ns.users set-admin` and `remove-admin`)
- delete a local database that contains administrators
- change the password of another account (`ns.account set-password`)
- change SSH settings and keys (`ns.ssh`), with the controller account kept read-only here
- download, delete or restore from file a backup, and set the backup passphrase (`ns.backup`)
- migrate from NethServer 7 (`ns.migration migrate`)
- install an uploaded image (`ns.update install-uploaded-image`)

Other administrators can manage non-administrator users and change their own password.
Denied calls return `{"error": "forbidden"}`.

Usernames of the superusers and `nethsupport` are reserved and can't be used for local users.

## Checking the caller

`ns-api-server` authenticates the user and runs `ns.*` scripts directly, so it passes the username of the
caller to them in the `NS_API_USER` environment variable.
Authorization is done in Python with the `nethsec.users` library:
- `is_superuser(uci, username)` tells whether a username belongs to a superuser
- `caller_is_superuser(uci)` checks `NS_API_USER`, trusting callers that don't set it (like `ubus` or scripts run as `root`) as `root`

The UI reads the role of the logged user from `ns.account get-info`, which also returns whether `root` still uses the
default password and how many non-superuser administrators exist.

`ns-api-server` refuses generic `uci get` and `uci set` calls on the `rpcd`, `users` and `dropbear` configurations, so
these can be changed only through `ns.users` and `ns.ssh`. `uci changes` and `uci revert` are still allowed.

## Sessions and 2FA

The post-commit hook `clear-user-tokens.py` runs on every commit that changes `rpcd`: for each username that has no `rpcd`
login anymore, because it was demoted or deleted, it removes the session tokens from `/var/run/ns-api-server/tokens` and
the 2FA secret from `/etc/ns-api-server`.
Password changes don't touch the active sessions.

## Limitations

Administrators can still change the rest of the configuration, so administrator access should be given only to trusted operators.
