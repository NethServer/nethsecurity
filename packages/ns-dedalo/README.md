# Dedalo hotstpot

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


## First setup

1. Configure basic parameters.
   The `hotspot_id` van be found inside the Icaro portal.
   The `interface` should be a free physical interface (`eth2` in this example).
   ```shell
   uci set dedalo.config.unit_name=$(uci get system.@system[0].hostname)
   uci set dedalo.config.unit_uuid=$(uuidgen)
   uci set dedalo.config.secret=$(uuidgen | md5sum | awk '{print $1}')
   uci set dedalo.config.unit_description='My Dedalo hotspot'
   uci set dedalo.config.hotspot_id=1550
   uci set dedalo.config.interface=eth2
   uci set dedalo.config.disabled=0
   uci commit dedalo
   ```
 
2. Setup the firewall.
   ```shell
   uci add_list firewall.ns_dedalo.device=eth2
   uci commit firewall
   fw4 reload
   ```

3. Register the unit and start the service.
   ```shell
   /etc/init.d/dedalo reload
   dedalo register -u <your reseller username> -p <your reseller password>
   dedalo restart
   ```

## Notes

- Dedalo requires `coova-chilli` built-in with curl support otherwise `chilly_proxy` will hang
