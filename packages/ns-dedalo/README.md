# ns-dedalo

This is the client part of [Icaro hotspot](https://github.com/nethesis/icaro).

## Configuration

Available options:

- `disabled`: Enable/disable dedalo service (default true)
- `network`: network for clients connected to Dedalo eg: `192.168.69.0/24`
- `splash_page`: Wings (capitve portal) URL hosted on your Icaro installation, eg: ``http://icaro.mydomain.com/wings``
- `aaa_url`:  Wax (Radius over HTTP) URL hosted on your Icaro installation, eg: ``https://icaro.mydomain.com/wax/aaa``
- `api_url`: Sun APIs URL hosted on your Icaro installation, eg: ``https://icaro.mydomain.com/api``
- `hotspot_id`:  the id of the Hotspot already present inside Icaro
- `unit_name`: hostname of local installation, eg: ``hotelthesea.example.org``
- `unit_description`: a descriptive name of local installation, eg: ``MyHotelAtTheSea``
- `unit_uuid`:  a unique unit idenifier, usually a UUID, eg ``161fre6d-8578-4247-b4a2-c40dced94bdd``
- `secret`: a shared secret between this unit and Icaro installation, eg: ``My$uperS3cret``


## Configuration

Use the APIs to configure dedalo and the firewall:
```
echo '{"network":"192.168.182.0/24","hotspot_id":"1787","unit_name":"NethSec","unit_description":"t1","interface":"eth3","dhcp_limit":"253"}'\
  | /usr/libexec/rpcd/ns.dedalo call set-configuration
```

The `hotspot_id` van be found inside the Icaro portal.
The `interface` should be a free physical interface (`eth3` in this example).

## Unregister

To disable dedalo and unregister the unit from Icaro server, execute:
```
unregister_dedalo <your reseller username> <your reseller password>
```

## Notes
 
- Dedalo requires `coova-chilli` built-in with curl support otherwise `chilly_proxy` will hang
