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

### Disable 2FA via the web interface

If the administrator can still log in to the web interface:

1. Click the user icon in the top-right corner and select **Account settings**.
2. Scroll to the **Two-factor authentication** section.
3. Click **Revoke 2FA**.
4. A confirmation dialog appears warning that the security level will be reduced.
   Click **Revoke 2FA** to confirm.
5. If prompted, enter your current password to authorize the change.

After the confirmation the status badge changes to disabled and the next login will no
longer require an OTP.

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
