<!-- markdownlint-disable -->

# banIP - ban incoming and outgoing IP addresses/subnets via Sets in nftables

<a id="description"></a>
## Description
IP address blocking is commonly used to protect against brute force attacks, prevent disruptive or unauthorized address(es) from access or it can be used to restrict access to or from a particular geographic area — for example. Further more banIP scans the log file via logread and bans IPs that make too many password failures, e.g. via ssh.

<a id="main-features"></a>
## Main Features
* banIP supports the following fully pre-configured IP blocklist feeds (free for private usage, for commercial use please check their individual licenses).
**Please note:** By default, each feed blocks the packet flow in the chain shown in the table below. _Inbound_ combines the chains WAN-Input and WAN-Forward, _Outbound_ represents the LAN-FWD chain:
  * WAN-INP chain applies to packets from internet to your router
  * WAN-FWD chain applies to packets from internet to other local devices (not your router)
  * LAN-FWD chain applies to local packets going out to the internet (not your router)
  The listed standard assignments can be changed to your needs under the 'Feed/Set Settings' config tab.

| Feed                | Focus                          | Inbound | Outbound | Proto/Port        | Information                                                  |
| :------------------ | :----------------------------- | :-----: | :------: | :---------------: | :----------------------------------------------------------- |
| asn                 | ASN segments                   |    x    |          |                   | [Link](https://asn.ipinfo.app)                               |
| backscatterer       | backscatterer IPs              |    x    |          |                   | [Link](https://www.uceprotect.net/en/index.php)              |
| becyber             | malicious attacker IPs         |    x    |          |                   | [Link](https://github.com/duggytuxy/malicious_ip_addresses)  |
| binarydefense       | binary defense banlist         |    x    |          |                   | [Link](https://iplists.firehol.org/?ipset=bds_atif)          |
| bogon               | bogon prefixes                 |    x    |          |                   | [Link](https://team-cymru.com)                               |
| bruteforceblock     | bruteforceblocker IPs          |    x    |          |                   | [Link](https://danger.rulez.sk/index.php/bruteforceblocker/) |
| country             | country blocks                 |    x    |          |                   | [Link](https://www.ipdeny.com/ipblocks)                      |
| cinsscore           | suspicious attacker IPs        |    x    |          |                   | [Link](https://cinsscore.com/#list)                          |
| debl                | fail2ban IP blacklist          |    x    |          |                   | [Link](https://www.blocklist.de)                             |
| dns                 | public DNS-Server              |         |    x     | tcp, udp: 53, 853 | [Link](https://public-dns.info)                              |
| doh                 | public DoH-Server              |         |    x     | tcp, udp: 80, 443 | [Link](https://github.com/dibdot/DoH-IP-blocklists)          |
| drop                | spamhaus drop compilation      |    x    |          |                   | [Link](https://www.spamhaus.org)                             |
| dshield             | dshield IP blocklist           |    x    |          |                   | [Link](https://www.dshield.org)                              |
| etcompromised       | ET compromised hosts           |    x    |          |                   | [Link](https://iplists.firehol.org/?ipset=et_compromised)    |
| feodo               | feodo tracker                  |    x    |          |                   | [Link](https://feodotracker.abuse.ch)                        |
| firehol1            | firehol level 1 compilation    |    x    |          |                   | [Link](https://iplists.firehol.org/?ipset=firehol_level1)    |
| firehol2            | firehol level 2 compilation    |    x    |          |                   | [Link](https://iplists.firehol.org/?ipset=firehol_level2)    |
| firehol3            | firehol level 3 compilation    |    x    |          |                   | [Link](https://iplists.firehol.org/?ipset=firehol_level3)    |
| firehol4            | firehol level 4 compilation    |    x    |          |                   | [Link](https://iplists.firehol.org/?ipset=firehol_level4)    |
| greensnow           | suspicious server IPs          |    x    |          |                   | [Link](https://greensnow.co)                                 |
| hagezi              | Threat IP blocklist            |         |    x     | tcp, udp: 80, 443 | [Link](https://github.com/hagezi/dns-blocklists)             |
| ipblackhole         | blackhole IPs                  |    x    |          |                   | [Link](https://github.com/BlackHoleMonster/IP-BlackHole)     |
| ipexdbl             | IPEX dynamic blocklists        |    x    |          |                   | [Link](https://github.com/ZEROF/ipextractor)                 |
| ipsum               | malicious IPs                  |    x    |          |                   | [Link](https://github.com/stamparm/ipsum)                    |
| ipthreat            | hacker and botnet IPs          |    x    |          |                   | [Link](https://ipthreat.net)                                 |
| myip                | real-time IP blocklist         |    x    |          |                   | [Link](https://myip.ms)                                      |
| proxy               | open proxies                   |    x    |          |                   | [Link](https://iplists.firehol.org/?ipset=proxylists)        |
| threat              | emerging threats               |    x    |          |                   | [Link](https://rules.emergingthreats.net)                    |
| threatview          | malicious IPs                  |    x    |          |                   | [Link](https://threatview.io)                                |
| tor                 | tor exit nodes                 |    x    |          |                   | [Link](https://www.dan.me.uk)                                |
| turris              | turris sentinel blocklist      |    x    |          |                   | [Link](https://view.sentinel.turris.cz)                      |
| uceprotect1         | spam protection level 1        |    x    |          |                   | [Link](https://www.uceprotect.net/en/index.php)              |
| uceprotect2         | spam protection level 2        |    x    |          |                   | [Link](https://www.uceprotect.net/en/index.php)              |
| uceprotect3         | spam protection level 3        |    x    |          |                   | [Link](https://www.uceprotect.net/en/index.php)              |
| urlhaus             | urlhaus IDS IPs                |    x    |          |                   | [Link](https://urlhaus.abuse.ch)                             |
| urlvir              | malware related IPs            |    x    |          |                   | [Link](https://iplists.firehol.org/?ipset=urlvir)            |
| webclient           | malware related IPs            |    x    |          |                   | [Link](https://iplists.firehol.org/?ipset=firehol_webclient) |
| voip                | VoIP fraud blocklist           |    x    |          |                   | [Link](https://voipbl.org)                                   |
| vpn                 | vpn IPs                        |    x    |          |                   | [Link](https://github.com/X4BNet/lists_vpn)                  |
| vpndc               | vpn datacenter IPs             |    x    |          |                   | [Link](https://github.com/X4BNet/lists_vpn)                  |

* Zero-conf like automatic installation & setup, usually no manual changes needed
* All Sets are handled in a separate nft table/namespace 'banIP'
* Full IPv4 and IPv6 support
* Supports nft atomic Set loading
* Supports blocking by ASN numbers and by iso country codes
* Block countries dynamically by Regional Internet Registry (RIR), e.g. all countries related to ARIN. Supported service regions are: AFRINIC, ARIN, APNIC, LACNIC and RIPE
* Supports local allow- and blocklist with MAC/IPv4/IPv6 addresses or domain names
* Supports concatenation of local MAC addresses with IPv4/IPv6 addresses, e.g. to enforce dhcp assignments
* All local input types support ranges in CIDR notation
* Auto-add the uplink subnet or uplink IP to the local allowlist
* Prevent common ICMP, UDP and SYN flood attacks and drop spoofed tcp flags & invalid conntrack packets (DoS attacks) in an additional prerouting chain
* Provides a small background log monitor to ban unsuccessful login attempts in real-time (like fail2ban, crowdsec etc.)
* Auto-add unsuccessful LuCI, nginx, Asterisk or ssh login attempts to the local blocklist
* Auto-add entire subnets to the blocklist Set based on an additional RDAP request with the monitored suspicious IP
* Fast feed processing as they are handled in parallel as background jobs (on capable multi-core hardware)
* Per feed it can be defined whether the inbound chain (wan-input, wan-forward) or the outbound chain (lan-forward) should be blocked
* Automatic blocklist backup & restore, the backups will be used in case of download errors or during startup
* Automatically selects one of the following download utilities with ssl support: curl, uclient-fetch or full wget
* Provides HTTP ETag support to download only ressources that have been updated on the server side, to speed up banIP reloads and to save bandwith
* Supports an 'allowlist only' mode, this option restricts the internet access only to specific, explicitly allowed IP segments
* Supports external allowlist URLs to reference additional IPv4/IPv6 feeds
* Optionally always allow certain protocols/destination ports in the inbound chain
* Deduplicate IPs accross all Sets (single IPs only, no intervals)
* Implements BCP38 ingress filtering to prevent IP address spoofing
* Provides comprehensive runtime information
* Provides a detailed Set report, incl. a map that shows the geolocation of your own uplink addresses (in green) and the location of potential attackers (in red)
* Provides a Set search engine for certain IPs
* Feed parsing by fast & flexible regex rulesets
* Minimal status & error logging to syslog, enable debug logging to receive more output
* Procd based init system support (start/stop/restart/reload/status/report/search/content)
* Procd network interface trigger support
* Add new or edit existing banIP feeds on your own with the LuCI integrated custom feed editor
* Supports destination port & protocol limitations for external feeds (see the feed list above). To change the default assignments just use the custom feed editor
* Supports allowing / blocking of certain VLAN forwards
* Provides an option to transfer logging events on remote servers via cgi interface

<a id="prerequisites"></a>
## Prerequisites
* **[OpenWrt](https://openwrt.org)**, latest stable release or a development snapshot with nft/firewall 4 support
* A download utility with SSL support: 'curl', full 'wget' or 'uclient-fetch' with one of the 'libustream-*' SSL libraries, the latter one doesn't provide support for ETag HTTP header
* A certificate store like 'ca-bundle', as banIP checks the validity of the SSL certificates of all download sites by default
* For E-Mail notifications you need to install and setup the additional 'msmtp' package

**Please note:**
* Devices with less than 256MB of RAM are **_not_** supported
* After system upgrades it's recommended to start with a fresh banIP default config

For more information and documentation, please visit the official [banIP GitHub repository](https://github.com/openwrt/packages/tree/master/net/banip).
