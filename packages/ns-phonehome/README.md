# ns-phonehome

The phonehome sends every night some statistical data to a remote server.
These data are used to:
- create an installation map [https://phonehome.nethserver.org/](https://phonehome.nethserver.org/)
- create an inventory of hardware compatibile with NethSecurity

Sent data can be inspected using the following command:
```
phonehome | jq
```

To disable the phonehome:
```
uci set phonehome.config.enabled=0
uci commit phonehome
```
