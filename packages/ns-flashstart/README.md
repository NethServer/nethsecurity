# ns-flashstart

ns-flashstart is the client configuration for [FlashStart](https://flashstart.com) DNS filter.

The client is composed by 3 main parts:

- `/usr/sbin/flashstart`: script to enable and disable flashstart
- `/usr/share/ns-flashstart/flashtart-auth`: authentication script
- `/etc/config/flashstart`: UCI configuration file

The `ns-plug` service needs the `username` and `password` options.. Example:
```
uci set flashstart.global.username="myuser@nethserver.org"
uci set flashstart.global.password="mypassword"
uci set flashstart.global.enabled="1"
uci commit flashstart
``` 
