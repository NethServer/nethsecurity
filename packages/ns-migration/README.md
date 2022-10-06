# ns-migration

ns-migration imports the configuration from NethServer 7 (NS7).

Before proceed, make sure to export NS7 configuration using [nethserver-firwall-migration](https://github.com/NethServer/nethserver-firewall-migration/) package. 

## Usage

The main command is `ns-import`:
```
ns-import [-q] [-m oldmac=newmac] <exported_archive>
```

Usage example:
```
ns-import -m 'ae:12:3b:19:0a:2a=0b:64:31:69:ae:8a' export.tar.gz
```

The `ns-import` will:
- explode the archive inside a temporary directory
- invoke all the scripts inside `/usr/share/firewall-import/` directory
- pass the temporary directory as argument to each script

Scripts can also be invoked manually after extracting the archive.
Example:
```
cd /tmp
tar xvzf export.tar.gz
/usr/share/firewall-import/network /tmp/export
```

The `ns-import` script is verbose by default, use the `-q` option to suppress output to standard output.

### Remapping interfaces

When importing the configuration from an old machine to a new one, you need to remap
network interface hardware addresses.

Usage example:
```
ns-import -m 'ae:12:3b:19:0a:2a=0b:64:31:69:ae:8a' export.tar.gz
```

The `-m` option will be used by migration scripts to move the configuration from the old network
interface (`ae:12:3b:19:0a:2a`) to the new one (`0b:64:31:69:ae:8a`).

## Network

The `network` script will reset default configuration by deleting all wan and lan devices with associated firewall zones.
It will import:

- Ethernet interfaces
- VLAN devices
- Bridges
- Bonds
- Aliases
- Firewall roles using firewall zones and forwarding
- Source NAT rules

Differences since NS7:

- source NAT are connected to `wan` outbound zone and not to a specific interface;
  this configuration can be changed by setting `src` option to `*` and adding `device` option set to the WAN physical ethernet interface
- `green` zone has been renamed to `lan`
- `red` zone has been renamed to `wan`
- bridges over bonds are not supported since UCI requires to setup an IP address on bond devices

## Date and time

The `time` script will import:

- timezone
- NTP client status (enabled/disabled)
- NTP server list

If NTP client is disabled on NS7, you must re-configure the time manually after the import.

## DHCP

The `dhcp` script will import:

- global options like DHCP max lease time
- DHCP servers
- DHCP static leases (reservations)

Differences since NS7

- DHCP on non static interfaces like bonds, is [not supported](https://github.com/openwrt/openwrt/blob/openwrt-22.03/package/network/services/dnsmasq/files/dnsmasq.init#L538)

## DNS 

The `dns` script will import:

- system FQDN
- global DNS configuration like local domain and DNS forwarders
- static hosts
- static wild card hosts

TFTP options are migrated, but not the content of the tftp_root directory. To re-enable the service make sure to setup `tftp_root` option.

## Static routes

The `routes` script will import:

- all static routes

## Port forwarding

The `redirect` script will import:

- all port forwards

If `HairpinNat` option was enabled on NS7, all imported port forward will have hairpin enabled (see `reflection` option).

## Firewall rules

The `rules` script will import:

- all firewall rules

The following NS7 features are still not imported:

- rules using NDPI services

Differences since NS7:

- zones are migrated as CIDR networks
- rules using non-existing zones will be disabled
- NAT helpers are disabled by default
- wan interfaces will accept extra traffic:

  - DHCP replies (`Allow-DHCP-Renew` and `Allow-DHCPv6` rules)
  - Ping (`Allow-Ping`, `Allow-ICMPv6-Input` and `Allow-ICMPv6-Forward` rules)
  - IGMP traffic (`Allow-IGMP` rule)
  - Multicast traffic (`Allow-MLD` rule)
  - IPsec (`Allow-ISAKMP` and `Allow-IPSec-ESP` rules)

The following NS7 features will not be migrated:

- `State` option for rules: rules will be applied only to new connections
- `ExternalPing` option: ping to wan is always permitted; disable corresponding rules to block it (see above)
- `MACValidation` (MAC Binding), you can replicate the same behavior by deleting the forwarding from lan to wan and then creating 
   a rule accepting traffic from a list of MAC addresses (`src_mac` option, see [suggested solution](https://forum.openwrt.org/t/block-all-except-mac-address-list/124879/8?))
- `Policy` option: `strict` policy will be converted to `permissive`; you can replicate the same behavior by deleting forwarding rules for involved zones
- `SipAlg` option: application level gateway (ALG) are disabled by default; if you need to enable NAT helper see [suggested solution](https://forum.openwrt.org/t/solved-incoming-calls-not-reaching-hosts-on-the-network/77568/2)

## MultiWAN

The `wan` script will import:

- multiwan mode (balance/backup)
- provider weight
- IP to check WAN connectivity
- divert rules

The following NS7 features will not be migrated:

- time matches for rules (not supported by mwan3)
- mail notification on WAN status change
- `MaxNumberPacketLoss` and `MaxPercentPacketLoss` tracking options

Differences since NS7:

- rules are presented in reverse order

After the migration you should tune tracking options for each wan interface.

## QoS

The `network` script will also import:

- download and upload bandwidth of wan interfaces

The following NS7 features will not be migrated:

- QoS classes with reserved bandwidth
- QoS rules

## OpenVPN roadwarrior

The `openvpn` script will import:

- CA, server and users certificates and keys
- IP address reservation
- user names with enabled/disabled status

The following NS7 features are still not migrated:
- authentication based user and password
- authentication certificate and password
- authentication certificate and One Time password (OTP)
- mail notification

Existing data from connection database are not imported.

See also [ns-openvpn](../ns-openvpn).

## OpenVPN tunnels

The `openvpn_tunnels` script will import

- all OpenVPN tunnel servers
- all OpenVPN tunnel clients

The following NS7 features will not be migrated:

- `WanPriorities` option of  tunnel client
- bridged mode of tunnel clients

## IPSec

The `ipsec` script will import:

- IPSec tunnels with PSK authentication

Differences since NS7:

- IPSec tunnels uses `xfrm` interfaces;
  if the original WAN was an ethernet interface, the `xfrm` inteface will be bound to it,
  otherwise the `xfrm` interface will be bound to the first available WAN

The following NS7 features will not be migrated:

- `Custom_` properties

## Threat shield

The `threat_shield` script will import:

- IP blacklist configuration with status (enabled/disabled), categories and local white list
- DNS blacklist configuration with status (enabled/disabled), categories and host bypass

If the categories comes from a community repositories, you should reconfigure after the import.

See also [ns-threat_shield](../ns-threat_shield).

## Subscription

The `subscription` script will import:

- system identifier
- system secret

## Hotspot (Dedalo)

The `hotspot` script will import:

- all configuration options

Differences since NS7:

- the hotspot will work only on ethernet and vlan interfaces

If the migration has been executed on a new hardware, the hotspot interface will change
MAC address. In this case, the unit must be manually registered to the remote Icaro server:

1. access Icaro portal and delete the new unit
2. register the new one:
   ```
   /etc/init.d/dedalo reload
   dedalo register -u <your reseller username> -p <your reseller password>
   dedalo restart
   ```

## Other features

The following features will be migrated in the upcoming months:

- Cloud DNS filter (Flashstart)

The following features are not migrated to NextSecurity:

- Web proxy (Squid) and filter (ufdbGuard)
- IPS (Suricata) and IPS alerts (EveBox)
- UPS monitoring (NUT)
- System statistics (Collectd)
- Reports (Dante)
- Bandwidth monitor (ntopng)
- Fail2ban
