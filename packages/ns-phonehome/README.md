# ns-phonehome

The phonehome feature sends anonymous statistical data to a remote server every night.
These data do not contain any personal information and are used solely for the purpose of 
creating an installation map at [https://phonehome.nethserver.org/](https://phonehome.nethserver.org/)
and generating an inventory of hardware compatible with NethSecurity. 

See also the [Master Data Privacy Agreement](https://www.nethesis.it/info/data-privacy-agreement-servizi) for more info.

To inspect the sent data, you can use the following command:
```
phonehome | jq
```

To disable the phonehome and stop sending statistical data, you can use the following commands:
```
uci set phonehome.config.enabled=0
uci commit phonehome
```
