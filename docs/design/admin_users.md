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

## Two-Factor Authentication (2FA)

### How 2FA secrets are stored

When an administrator enables 2FA through the web interface, the API server stores the
credentials under `/etc/ns-api-server/<username>/`:

| File | Description |
|------|-------------|
| `secret` | Base32-encoded TOTP secret |
| `status` | `1` = 2FA active, `0` = 2FA disabled |
| `codes` | One-time recovery codes (newline-separated) |

### Disable 2FA via API

If the administrator still knows their password they can disable 2FA from an HTTPS call
(e.g. from another machine or from the firewall itself):

```shell
# 1. Authenticate and get a JWT token (OTP not required at this step)
TOKEN=$(curl -s -k -H 'Content-Type: application/json' \
  https://localhost/api/login \
  --data '{"username": "root", "password": "YOUR_PASSWORD"}' \
  | jq -r .token)

# 2. Delete the 2FA secret
curl -s -k -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  https://localhost/api/2fa
```

A `200` response confirms that 2FA has been removed.  The next login will no longer
require an OTP.

### Disable 2FA from the command line (emergency recovery)

If an administrator has lost both the OTP device and the recovery codes and can no
longer log in to the web interface, 2FA can be reset directly from the shell as `root`
over SSH.

Run the following commands, replacing `<username>` with the administrator account name
(use `root` for the default administrator):

```shell
SECRETS_DIR=/etc/ns-api-server
USERNAME=root   # change to the affected username

rm -f  "${SECRETS_DIR}/${USERNAME}/secret"
rm -f  "${SECRETS_DIR}/${USERNAME}/codes"
printf '0' > "${SECRETS_DIR}/${USERNAME}/status"
```

After these commands the user can log in with just their password.  2FA can be
re-enabled at any time from the web interface.

> **Note:** Only the `root` account has SSH access by default.  Non-root administrators
> cannot be recovered from SSH by the affected user themselves; an existing `root`
> session is required to run the commands above on their behalf.
