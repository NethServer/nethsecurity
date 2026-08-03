from euci import EUci
from unittest.mock import patch, mock_open, MagicMock
import subprocess

from nethsec import inventory

netmap_db = """

config rule 'ns_b606fef5'
	option name 'foo'
	option dest '8.8.8.0/24'
	option map_from '12.0.0.0/24'
	option map_to '16.0.0.0/24'

config rule 'ns_003ff675'
	option name 'john'
	option src '12.0.0.0/24'
	option map_from '15.0.0.0/24'
	option map_to '14.0.0.0/24'
"""

firewall_db = """
config zone lan1
	option name 'lan'
	list network 'lan'
	option input 'ACCEPT'
	option output 'ACCEPT'
	option forward 'ACCEPT'
	list device 'eth0'

config zone grey
	option name 'grey'
	list network 'grey1'
	option input 'DROP'
	option output 'ACCEPT'
	option forward 'DROP'
	list device 'eth1'

config zone orange
	option name 'orange'
	list network 'orange1'
	option input 'DROP'
	option output 'DROP'
	option forward 'DROP'

config zone wan1f
	option name 'wan'
	list network 'wan'
	list network 'wan6'
	option input 'REJECT'
	option output 'ACCEPT'
	option forward 'REJECT'
	option masq '1'
	option mtu_fix '1'

config forwarding fw1
	option src 'lan'
	option dest 'wan'

config rule 'v6rule'
    option name 'Allow-DHCPv6'
    option src 'wan'
    option proto 'udp'
    option dest_port '546'
    option family 'ipv6'
    option target 'ACCEPT'

config rule 'manrule'
    option name 'Not-Automated'
    option src 'wan'
    option proto 'tcp'
    option dest_port '1234'
    option family 'ipv4'
    option target 'ACCEPT'

config rule 'f1'
	option name 'r1'
	option dest 'wan'
	option dest_port '22'
	option target 'ACCEPT'
	option src 'lan'
	list src_ip '192.168.100.1'
	list src_ip '192.168.100.238'
	list dest_ip '192.168.122.1'
	list dest_ip '192.168.122.49'
    option log '1'
 
config rule 'o1'
	option name 'output1'
	list dest_ip '192.168.100.1'
	option target 'ACCEPT'
	option dest 'wan'

config rule 'i1'
	option name 'Allow-OpenVPNRW1'
	option src 'wan'
	option dest_port '1194'
	option proto 'udp'
	option target 'ACCEPT'
	list ns_tag 'automated'
	option ns_link 'openvpn/ns_roadwarrior1'

config nat
	option name 'source_NAT1_vpm'
	option src '*'
	option src_ip '192.168.55.0/24'
	option dest_ip '10.20.30.0/24'
	option target 'SNAT'
	option snat_ip '10.44.44.1'
	list proto 'all'

config nat
	option name 'masquerade'
	list proto 'all'
	option src 'lan'
	option src_ip '192.168.1.0/24'
	option dest_ip '10.88.88.0/24'
	option target 'MASQUERADE'

config nat
	option name 'cdn_via_router'
	list proto 'all'
	option src 'lan'
	option src_ip '192.168.1.0/24'
	option dest_ip '192.168.50.0/24'
	option target 'ACCEPT'

config nat
	option name 'SNAT_NSEC7_style'
	list proto 'all'
	option src 'wan'
	option src_ip '192.168.1.44'
	option target 'SNAT'
	option snat_ip '10.20.30.5'

config redirect 'redirect3'
    option ns_src ''
    option ipset 'redirect3_ipset'

config ipset 'redirect3_ipset'
    option name 'redirect1_ipset'
    option match 'src_net'
    option enabled '1'
    list entry '6.7.8.9'

config redirect 'redirect4'
    option ns_src ''

config rule 'r1'
    option name 'r1'
    option ns_dst 'dhcp/ns_8dcab636'

config rule 'r2'
    option name 'r2'
    option ns_dst ''

config rule 'r3'
    option name 'r3'
    option ns_src ''

config rule 'r4'
    option ns_dst ''
    option ns_src ''

config rule 'ns_72004856'
        option name 'forward'
        option src '*'
        option dest 'lan'
        option target 'DROP'
        option ns_service '*'
        option proto 'all'
        option enabled '1'
        option log '0'
        list src_ip '1.1.1.1'
        option ns_dst 'objects/ns_7c9c0852'
        option ipset 'foo dst'

config rule 'ns_df2ca87c'
        option name 'output'
        option dest '*'
        option target 'DROP'
        option ns_service 'discard'
        option dest_port '9'
        option enabled '1'
        option log '0'
        list proto 'tcp'
        list proto 'udp'
        option ns_dst 'dhcp/ns_8d5d2cf4'
        list dest_ip '192.168.50.123'

config rule 'ns_a50bcca9'
        option name 'input'
        option src '*'
        option target 'DROP'
        option ns_service '*'
        option proto 'all'
        option enabled '1'
        option log '0'
        option ns_src 'objects/ns_bcfb447b'
        list src_ip '192.168.50.123'

"""

network_db = """
config interface 'lan'
	option device 'br-lan'
	option proto 'static'
	option ipaddr '192.168.50.1'
	option netmask '255.255.255.0'
            
config interface 'wan'
	option device 'eth1'
	option proto 'dhcp'

config interface 'wan6'
	option device 'eth1'
	option proto 'dhcpv6'

config interface 'bond1'
	option proto 'bonding'
	option ipaddr '10.0.0.22'
	option netmask '255.255.255.0'
	list slaves 'eth3'
	option bonding_policy 'balance-rr'
	option packets_per_slave '1'
	option all_slaves_active '0'
	option link_monitoring 'off'

config interface 'bond2'
	option proto 'bonding'
	option ipaddr '10.11.11.22'
	option netmask '255.255.255.0'
	option bonding_policy 'balance-rr'
	option packets_per_slave '1'
	list slaves 'eth3.2'

config device 'ns_3b3556cf'
	option name 'eth0.6'
	option type '8021q'
	option ifname 'eth0'
	option vid '6'
	option ipv6 '0'
config interface 'vlan6'
	option device 'eth0.6'
	option proto 'dhcp'

config device 'ns_c3c5206a'
        option name 'bond-foo'
        option ipv6 '0'
config interface 'bond1'
	option device 'bond-toto'
	option proto 'static'
	option ipaddr '125.12.12.12'
	option netmask '255.255.255.0'
config route 'ns_31de6ad0'
	option disabled '0'
	option gateway '1.1.1.1'
	option metric '0'
	option mtu '1500'
	option ns_description 'truc'
	option onlink '0'
	option target '1.1.1.0/24'
	option type 'unicast'

config route6 'ns_4a936870'
	option disabled '0'
	option gateway 'fe80::fc54:ff:fe70:2'
	option metric '0'
	option mtu '1500'
	option ns_description 'peolopopo'
	option onlink '0'
	option target 'fe80::fc54:ff:fe70:d2bc/64'
	option type 'unicast'

"""

dedalo_db = """
config dedalo 'config'
	option aaa_url 'https://my.nethspot.com/wax/aaa'
	option api_url 'https://my.nethspot.com/api'
	option network '192.168.82.0/24'
	option disabled '0'
	option splash_page 'http://my.nethspot.com/wings'
	option max_clients '253'
	option dhcp_end '250'
	option dhcp_start '2'
	option hotspot_id '51'
	option unit_name 'fw1.nethsecurity.org'
	option unit_description 'fw1 sede'
	option interface 'eth2.10'
	option secret 'xxxxxx'
	option unit_uuid 'yyyyy'
"""

flashstart_db = """
config main 'global'
	option enabled '0'
	option proplus '1'
	option password 'xxx'
	option username 'xxx@nethsecurity.org'
	list zones 'lan'
	list bypass '192.168.1.252'
	list bypass '192.168.1.211'
	list custom_servers '/www.google.com/1.1.1.1'
 """

openvpn_db = """
config openvpn 'sample_client'
	option client '1'
	option dev 'tun'
	option proto 'udp'
	list remote 'my_server_1 1194'
	option resolv_retry 'infinite'
	option nobind '1'
	option persist_key '1'
	option persist_tun '1'
	option user 'nobody'
	option ca '/etc/openvpn/ca.crt'
	option cert '/etc/openvpn/client.crt'
	option key '/etc/openvpn/client.key'
	option verb '3'

config openvpn 'ns_openvpn1'
	option dev 'tunopenvpn1'
	option dev_type 'tun'
	option enabled '1'
	option persist_tun '1'
	option float '1'
	option multihome '1'
	option passtos '1'
	option ping_timer_rem '1'
	option persist_key '1'
	option keepalive '10 60'
	option lport '1202'
	option proto 'udp'
	option topology 'subnet'
	option dh '/etc/openvpn/ns_openvpn1/pki/dh.pem'
	option ca '/etc/openvpn/ns_openvpn1/pki/ca.crt'
	option cert '/etc/openvpn/ns_openvpn1/pki/issued/server.crt'
	option key '/etc/openvpn/ns_openvpn1/pki/private/server.key'
	option server '10.7.57.0 255.255.255.0'
	list push 'topology subnet'
	list push 'route 192.168.50.0 255.255.255.0'
	list route '192.168.10.0 255.255.255.0'
	option cipher 'AES-256-GCM'
	option auth 'SHA256'
	list ns_public_ip '86.206.129.103'
	option ns_name 'openvpn1'
	option client_connect '"/usr/libexec/ns-openvpn/openvpn-connect ns_openvpn1"'
	option client_disconnect '"/usr/libexec/ns-openvpn/openvpn-disconnect ns_openvpn1"'
	option management '/var/run/openvpn_ns_openvpn1.socket unix'

config openvpn 'ns_roadwarrior1'
	option proto 'udp'
	option port '1194'
	option dev 'tunrw1'
	option dev_type 'tun'
	option topology 'subnet'
	option float '1'
	option passtos '1'
	option multihome '1'
	option verb '3'
	option enabled '1'
	option keepalive '20 120'
	option server '10.9.9.0 255.255.255.0'
	option client_connect '"/usr/libexec/ns-openvpn/openvpn-connect ns_roadwarrior1"'
	option client_disconnect '"/usr/libexec/ns-openvpn/openvpn-disconnect ns_roadwarrior1"'
	option dh '/etc/openvpn/ns_roadwarrior1/pki/dh.pem'
	option ca '/etc/openvpn/ns_roadwarrior1/pki/ca.crt'
	option cert '/etc/openvpn/ns_roadwarrior1/pki/issued/server.crt'
	option crl_verify '/etc/openvpn/ns_roadwarrior1/pki/crl.pem'
	option key '/etc/openvpn/ns_roadwarrior1/pki/private/server.key'
	option management '/var/run/openvpn_ns_roadwarrior1.socket unix'
	option client_to_client '0'
	option auth 'SHA256'
	option cipher 'AES-256-GCM'
	option tls_version_min '1.2'
	option ns_auth_mode 'username_password_certificate'
	list ns_tag 'automated'
	option ns_user_db 'NethService'
	option ns_description 'srv1'
	option auth_user_pass_verify '/usr/libexec/ns-openvpn/openvpn-remote-auth via-env'
	option script_security '3'
	list push 'redirect-gateway'
	list push 'route 192.168.1.0 255.255.255.0'
	list push 'route 172.2.2.0 255.255.254.0'
	list ns_public_ip 'vpn.test.org'

config user 'user1'
	option instance 'ns_roadwarrior1'
	option ipaddr '10.9.9.50'
	option enabled '1'
"""

ns_plug_db = """
config main 'config'
	option tls_verify '1'
	option backup_url 'https://backupd.nethsecurity.org/backup'
	option type 'enterprise'
	option alerts_url 'https://my.nethsecurity.org/isa/'
	option api_url 'https://my.nethsecurity.org/api/'
	option inventory_url 'https://my.nethsecurity.org/isa/inventory/store/'
	option system_id 'xxx'
	option secret 'yyy'
    option server ''
    option unit_id ''
    option token ''
"""

ban_ip_db = """
config banip 'global'
	option ban_enabled '1'
	option ban_debug '1'
	option ban_autodetect '0'
	list ban_logterm 'Exit before auth from'
	option ban_fetchcmd 'curl'
	option ban_protov4 '1'
	list ban_ifv4 'FIBER100M'
	list ban_ifv4 'FTTC_BCK'
	list ban_dev 'eth0'
	list ban_dev 'eth5'
    list ban_allowurl ''
	option ban_loginput '1'
	option ban_logforwardwan '1'
	option ban_logforwardlan '1'
	option ban_autoallowlist '1'
	option ban_autoblocklist '1'
	option ban_allowlistonly '0'
	option ban_nftexpiry '1d'
	option ban_logcount '3'
	list ban_feed 'nethesislvl3'
    list ban_feed 'test1'
"""

ns_ui_db = """
config main 'config'
	option luci_enable '0'
	option nsui_enable '1'
	option nsui_extra_port '9090'
	option nsui_extra_enable '1'
"""

fstab_db = """
config global
	option anon_swap '0'
	option anon_mount '0'
	option auto_swap '1'
	option auto_mount '1'
	option delay_root '5'
	option check_fs '0'

config mount
	option target '/rom'
	option uuid '520aae54-7d368ea4-c0a96e03-92927a0f'
	option enabled '0'

config mount 'ns_data'
	option target '/mnt/data'
	option uuid '523ba406-b2b6-4a3c-b071-ac1bf6acf4c6'
	option enabled '1'
"""

nginx_db = """
config main 'global'
	option uci_enable 'true'

config server '_lan'
	list listen '443 ssl default_server'
	list listen '[::]:443 ssl default_server'
	option server_name '_lan'
	list include 'conf.d/*.locations'
	option uci_manage_ssl 'custom'
	option ssl_certificate '/etc/ssl/acme/test.nethsecurity.org.fullchain.crt'
	option ssl_certificate_key '/etc/ssl/acme/test.nethsecurity.org.key'
	option ssl_session_cache 'shared:SSL:32k'
	option ssl_session_timeout '64m'
	option error_log 'syslog:server=unix:/dev/log'
	option access_log 'syslog:server=unix:/dev/log'

config location 'ns_server2_location1'
	option uci_server 'ns_server2'
	option location '/'
	option proxy_pass 'https://172.4.5.4'

config server 'ns_server1'
	option uci_description 'Test 1'
	option ssl_session_timeout '64m'
	list proxy_set_header 'Host $http_host'
	list listen '443 ssl'
	list listen '[::]:443 ssl'
	option ssl_session_cache 'shared:SSL:32k'
	option server_name 'metrics.nethsecurity.org'
	list include 'conf.d/ns_server1.proxy'
	option uci_manage_ssl 'acme'
	option ssl_certificate '/etc/ssl/acme/test.nethsecurity.org.fullchain.crt'
	option ssl_certificate_key '/etc/ssl/acme/test.nethsecurity.org.key'

config location 'ns_server1_location1'
	option uci_server 'ns_server1'
	option location '/'
	option proxy_pass 'https://172.3.3.3'
"""

ipsec_db = """
config ipsec 'ns_ipsec_global'
	option debug '1'
	option zone 'ipsec'

config crypto_proposal 'ns_6fd94f07_ike'
	option encryption_algorithm 'aes256'
	option hash_algorithm 'sha256'
	option dh_group 'modp2048'
	option ns_link 'ipsec/ns_6fd94f07'

config crypto_proposal 'ns_6fd94f07_esp'
	option encryption_algorithm 'aes256'
	option hash_algorithm 'sha256'
	option dh_group 'modp2048'
	option ns_link 'ipsec/ns_6fd94f07'

config tunnel 'ns_6fd94f07_tunnel_1'
	option ipcomp 'false'
	option dpdaction 'none'
	list local_subnet '192.168.1.0/24'
	list remote_subnet '192.168.3.0/24'
	option rekeytime '3600'
	list crypto_proposal 'ns_6fd94f07_esp'
	option closeaction 'none'
	option startaction 'start'
	option if_id '1'
	option ns_link 'ipsec/ns_6fd94f07'

config tunnel 'ns_6fd94f07_tunnel_2'
	option ipcomp 'false'
	option dpdaction 'none'
	list local_subnet '172.4.4.0/24'
	list remote_subnet '192.168.3.0/24'
	option rekeytime '3600'
	list crypto_proposal 'ns_6fd94f07_esp'
	option closeaction 'none'
	option startaction 'start'
	option if_id '1'
	option ns_link 'ipsec/ns_6fd94f07'

config remote 'ns_6fd94f07'
	option ns_name 't1'
	option authentication_method 'psk'
	option gateway '1.2.3.4'
	option keyexchange 'ikev1'
	option local_identifier '@l1'
	option local_ip '5.6.7.8'
	option enabled '1'
	option remote_identifier '@r1'
	option pre_shared_key 'xxx'
	list crypto_proposal 'ns_6fd94f07_ike'
	option rekeytime '3600'
	list tunnel 'ns_6fd94f07_tunnel_1'
	list tunnel 'ns_6fd94f07_tunnel_2'
"""

dpi_db = """
config main 'config'
	option log_blocked '0'
	option enabled '1'
	option firewall_exemption '0'

config rule 'ns_2b170d05'
	option enabled '1'
	option device 'br-lan'
	option action 'block'
	list application 'netify.facebook'
"""

dhcp_db = """
config dnsmasq
	option domainneeded '1'
	option boguspriv '1'
	option filterwin2k '0'
	option localise_queries '1'
	option rebind_protection '1'
	option rebind_localhost '1'
	option local '/lan/'
	option domain 'nethesis.it'
	option expandhosts '1'
	option nonegcache '0'
	option cachesize '1000'
	option authoritative '1'
	option readethers '1'
	option leasefile '/tmp/dhcp.leases'
	option resolvfile '/tmp/resolv.conf.d/resolv.conf.auto'
	option nonwildcard '1'
	option localservice '1'
	option ednspacket_max '1232'
	option filter_aaaa '0'
	option filter_a '0'
	option logqueries '0'
	list server '8.8.8.8'
	list server '8.8.4.4'
	list rebind_domain 'nethsecurity.org'

config dhcp 'lan'
	option interface 'lan'
	option start '100'
	option limit '150'
	option leasetime '12h'
	option dhcpv4 'server'
	option dhcpv6 'server'
	option ra 'server'
	option ra_slaac '1'
	list ra_flags 'managed-config'
	list ra_flags 'other-config'
"""

mwan3_db = """
config globals 'globals'
	option mmx_mask '0x3F00'

config policy 'ns_default'
	option label 'Default'
	list use_member 'ns_FIBER100M_M10_W100'
	list use_member 'ns_FTTC_BCK_M20_W100'

config interface 'FIBER100M'
	option enabled '1'
	option initial_state 'online'
	option family 'ipv4'
	list track_ip '8.8.8.8'
	list track_ip '208.67.222.222'
	option track_method 'ping'
	option reliability '1'
	option count '1'
	option size '56'
	option max_ttl '60'
	option timeout '4'
	option interval '10'
	option failure_interval '5'
	option recovery_interval '5'
	option down '5'
	option up '5'

config member 'ns_FIBER100M_M10_W100'
	option interface 'FIBER100M'
	option metric '10'
	option weight '100'

config interface 'FTTC_BCK'
	option enabled '1'
	option initial_state 'online'
	option family 'ipv4'
	list track_ip '8.8.8.8'
	list track_ip '208.67.222.222'
	option track_method 'ping'
	option reliability '1'
	option count '1'
	option size '56'
	option max_ttl '60'
	option timeout '4'
	option interval '10'
	option failure_interval '5'
	option recovery_interval '5'
	option down '5'
	option up '5'

config member 'ns_FTTC_BCK_M20_W100'
	option interface 'FTTC_BCK'
	option metric '20'
	option weight '100'

config rule 'ns_default_rule'
	option label 'Default Rule'
	option use_policy 'ns_default'
	option sticky '1'
"""

qosify_db = """
config interface 'wan'
	option name 'wan'
	option disabled '1'
	option bandwidth_up '100mbit'
	option bandwidth_down '100mbit'
	option overhead_type 'none'
	option ingress '1'
	option egress '1'
	option mode 'diffserv4'
	option nat '1'
	option host_isolate '1'
	option autorate_ingress '0'

config device 'wandev'
	option disabled '1'
	option name 'wan'
	option bandwidth '100mbit'

config interface 'FIBER100M'
	option name 'FIBER100M'
	option disabled '0'
	option bandwidth_up '85mbit'
	option bandwidth_down '85mbit'

config interface 'FTTC_BCK'
	option name 'FTTC_BCK'
	option disabled '0'
	option bandwidth_up '20mbit'
	option bandwidth_down '40mbit'
"""

objects_db = """

config rule 'ns_b606fef5'
	option name 'object1'
	option dest '8.8.8.0/24'
	option map_from '12.0.0.0/24'
	option map_to '16.0.0.0/24'

config rule 'ns_003ff675'
	option name 'object2'
	option src '12.0.0.0/24'
	option map_from '15.0.0.0/24'
	option map_to '14.0.0.0/24'

config domain 'ns_7c9c0852'
	option name 'object3'
	option family 'ipv4'
	option timeout '660'
	list domain 'foo.com'

config host 'ns_bcfb447b'
	option name 'object4'
	option family 'ipv4'
	list ipaddr 'dhcp/ns_8d5d2cf4'
"""

adblock_db = """
config adblock 'global'
	option adb_enabled '1'
	option adb_debug '0'
	option adb_forcedns '1'
	option adb_safesearch '0'
	option adb_dnsfilereset '0'
	option adb_mail '0'
	option adb_report '0'
	option adb_backup '1'
	option adb_fetchutil 'wget'
	option adb_dns 'dnsmasq'
	option ts_enabled '1'
	list adb_zonelist 'lan'
	list adb_portlist '53'
	list adb_portlist '853'
	option adb_srcarc '/etc/adblock/combined.sources.gz'
	option adb_dnsinstance '0'
	option adb_fetchparm '--compression=gzip --no-cache --no-cookies --max-redirect=0 --timeout=20 -O'
	list adb_sources 'adaway'
	list adb_sources 'adguard'
	list adb_sources 'disconnect'
	list adb_sources 'yoyo'
	list adb_sources 'malware_lvl2'
	list adb_sources 'yoroi_susp_level2'
	list adb_sources 'yoroi_malware_level1'
"""

rpcd_db = """
config rpcd
	option dummy 'to get ignored'

config login
	option username 'root'

config login 'controller'
	option username 'gibblerish'

config login 'ns_7fe3e016'
	option username 'example'
"""

def _setup_db(tmp_path):
     # setup fake db
    with tmp_path.joinpath('network').open('w') as fp:
        fp.write(network_db)
    with tmp_path.joinpath('firewall').open('w') as fp:
        fp.write(firewall_db)
    with tmp_path.joinpath('dedalo').open('w') as fp:
        fp.write(dedalo_db)
    with tmp_path.joinpath('flashstart').open('w') as fp:
        fp.write(flashstart_db)
    with tmp_path.joinpath('openvpn').open('w') as fp:
        fp.write(openvpn_db)
    with tmp_path.joinpath('ns-plug').open('w') as fp:
        fp.write(ns_plug_db)
    with tmp_path.joinpath('banip').open('w') as fp:
        fp.write(ban_ip_db)
    with tmp_path.joinpath('ns-ui').open('w') as fp:
        fp.write(ns_ui_db)
    with tmp_path.joinpath('fstab').open('w') as fp:
        fp.write(fstab_db)
    with tmp_path.joinpath('nginx').open('w') as fp:
        fp.write(nginx_db)
    with tmp_path.joinpath('ipsec').open('w') as fp:
        fp.write(ipsec_db)
    with tmp_path.joinpath('dpi').open('w') as fp:
        fp.write(dpi_db)
    with tmp_path.joinpath('dhcp').open('w') as fp:
        fp.write(dhcp_db)
    with tmp_path.joinpath('mwan3').open('w') as fp:
        fp.write(mwan3_db)
    with tmp_path.joinpath('qosify').open('w') as fp:
        fp.write(qosify_db)
    with tmp_path.joinpath('netmap').open('w') as fp:
        fp.write(netmap_db)
    with tmp_path.joinpath('objects').open('w') as fp:
        fp.write(objects_db)
    with tmp_path.joinpath('adblock').open('w') as fp:
        fp.write(adblock_db)
    with tmp_path.joinpath('rpcd').open('w') as fp:
        fp.write(rpcd_db)
    return EUci(confdir=tmp_path.as_posix())

def test_fact_hotspot(tmp_path):
    u = _setup_db(tmp_path)
    assert inventory.fact_hotspot(u) == {"enabled": True, "server": "https://my.nethspot.com/api", "interface": "eth2.10"}

def test_fact_flashstart(tmp_path):
    u = _setup_db(tmp_path)
    assert inventory.fact_flashstart(u) == {"enabled": False, "bypass": 2, "custom_servers": 1, "pro_plus": True}
    
def test_fact_openvpn_rw(tmp_path):
	u = _setup_db(tmp_path)
	assert inventory.fact_openvpn_rw(u) == {
		"enabled": 1,
		"server": 1,
		"instances": [
			{
				"section": "ns_roadwarrior1",
				"authentication": "username_password_certificate",
				"user_database": "NethService",
				"mode": "tun"
			}
		]
	}

def test_fact_openvpn_tun(tmp_path):
	u = _setup_db(tmp_path)
	result = inventory.fact_openvpn_tun(u)
	assert result == {
		"client": 0,
		"server": 1,
		"tunnels": [
			{
				"section": "ns_openvpn1",
				"mode": "tun"
			}
		]
	}
     
def test_fact_subscription_status(tmp_path):
	u = _setup_db(tmp_path)
	assert inventory.fact_subscription_status(u) == {"status": "enterprise"}
     
def test_fact_controller(tmp_path):
	u = _setup_db(tmp_path)
	assert inventory.fact_controller(u) == {"enabled": False}

def test_fact_rpcd_users(tmp_path):
	u = _setup_db(tmp_path)
	assert inventory.fact_rpcd_users(u) == {"count": 1}
     
def test_fact_threat_shield(tmp_path):
	u = _setup_db(tmp_path)
	assert inventory.fact_threat_shield(u) == {"enabled": True, "community": 1, "enterprise": 1}
     
def test_fact_ui(tmp_path):
	u = _setup_db(tmp_path)
	assert inventory.fact_ui(u) == {"luci": False, "port443": True, "port9090": True}
     
def test_fact_storage(tmp_path):
	u = _setup_db(tmp_path)
	assert inventory.fact_storage(u) == {"enabled": True}
     
def test_fact_network(tmp_path):
	u = _setup_db(tmp_path)
	result = inventory.fact_network(u)
	assert result['zones'][0]['name'] == 'lan'
	assert result['zones'][0]['ipv4'] == 1
	assert result['zones'][0]['ipv6'] == 0
	assert result['zones'][1]['name'] == 'grey'
	assert result['zones'][1]['ipv4'] == 1
	assert result['zones'][1]['ipv6'] == 0
	assert result['zones'][2]['name'] == 'orange'
	assert result['zones'][2]['ipv4'] == 0
	assert result['zones'][2]['ipv6'] == 0
	assert result['zones'][3]['name'] == 'wan'
	assert result['zones'][3]['ipv4'] == 1
	assert result['zones'][3]['ipv6'] == 0
	assert result['zones'][4]['name'] == 'mytrusted'
	assert result['zones'][4]['ipv4'] == 0
	assert result['zones'][4]['ipv6'] == 0
	assert result['zones'][5]['name'] == 'mylinked'
	assert result['zones'][5]['ipv4'] == 0
	assert result['zones'][5]['ipv6'] == 0
	assert result['zones'][6]['name'] == 'mytrusted2'
	assert result['zones'][6]['ipv4'] == 0
	assert result['zones'][6]['ipv6'] == 0
	assert result['zones'][7]['name'] == 'blue'
	assert result['zones'][7]['ipv4'] == 1
	assert result['zones'][7]['ipv6'] == 0
	assert result['interface_counts']['vlans'] == 0
	assert result['interface_counts']['bridges'] == 2
	assert result['interface_counts']['bonds'] == 0
	assert result['zone_network_counts']['lan'] == 2
	assert result['zone_network_counts']['grey'] == 1
	assert result['zone_network_counts']['orange'] == 0
	assert result['zone_network_counts']['wan'] == 2
	assert result['zone_network_counts']['mytrusted'] == 0
	assert result['zone_network_counts']['mylinked'] == 0
	assert result['zone_network_counts']['mytrusted2'] == 0
	assert result['zone_network_counts']['blue'] == 1
	assert result['route_info']['count_ipv6_route'] == 1
	assert result['route_info']['count_ipv4_route'] == 1

def test_fact_proxy_pass(tmp_path):
	u = _setup_db(tmp_path)
	assert inventory.fact_proxy_pass(u) == {"count": 2}
      
def test_fact_ipsec(tmp_path):
	u = _setup_db(tmp_path)
	assert inventory.fact_ipsec(u) == {"count": 1}
      
def test_fact_dpi(tmp_path):
	u = _setup_db(tmp_path)
	assert inventory.fact_dpi(u) == {"enabled": True, "rules": 1}
      
def test_fact_dhcp_server(tmp_path):
	u = _setup_db(tmp_path)
	assert inventory.fact_dhcp_server(u) == {"count": 1, "static_leases": 0, "dynamic_leases": 0, "dns_records_count": 0, "dns_forwarder_enabled": True }
      
def test_fact_multiwan(tmp_path):
	u = _setup_db(tmp_path)
	result = inventory.fact_multiwan(u)
	assert result['enabled']
	assert result['policies']['backup'] == 1
	assert result['policies']['balance'] == 0
	assert result['policies']['custom'] == 0
	assert result['rules'] == 1
      
def test_fact_qos(tmp_path):
	u = _setup_db(tmp_path)
	result = inventory.fact_qos(u)
	assert result['count'] == 2
	assert result['rules'][0]['enabled'] == True
	assert result['rules'][0]['upload'] == 85
	assert result['rules'][0]['download'] == 85
	assert result['rules'][1]['enabled'] == True
	assert result['rules'][1]['upload'] == 20
	assert result['rules'][1]['download'] == 40
      
def test_fact_certificates_info(tmp_path):
	u = _setup_db(tmp_path)
	result = inventory.fact_certificates_info(u)
	assert result['custom_certificates']['count'] == 0
	assert result['acme_certificates']['count'] == 0
	assert result['acme_certificates']['issued'] == 0
	assert result['acme_certificates']['pending'] == 0

def test_fact_firewall_stats(tmp_path):
    u = _setup_db(tmp_path)
    result = inventory.fact_firewall_stats(u)
    
    # Validate the 'firewall' section
    assert result['firewall']['port_forward'] == 2
    assert result['firewall']['nat']['masquerade'] == 1
    assert result['firewall']['nat']['snat'] == 4
    assert result['firewall']['nat']['accept'] == 2
    assert result['firewall']['netmap']['source'] == 3
    assert result['firewall']['netmap']['destination'] == 2
    assert result['firewall']['rules']['forward'] == 19
    assert result['firewall']['rules']['input'] == 7
    assert result['firewall']['rules']['output'] == 2
    
    # Validate the 'objects' section
    assert result['objects']['domains'] == 3
    assert result['objects']['hosts'] == 3
    assert result['objects']['port_forward']['allowed_from'] == 2
    assert result['objects']['port_forward']['destination_to'] == 2
    assert result['objects']['mwan_rules'] == 0
    assert result['objects']['rules']['forward'] == 1
    assert result['objects']['rules']['input'] == 1
    assert result['objects']['rules']['output'] == 1

def test_fact_adblock(tmp_path):
	u = _setup_db(tmp_path)
	result = inventory.fact_adblock(u)
	assert result == {"enabled": True, "community": 5, "enterprise": 2}

# Tests for info_* helper functions

def test_info_kernel_version():
	"""Test info_kernel_version reads from /proc/version"""
	u = EUci()
	
	# Test successful read
	mock_version = "Linux version 5.10.176 (builder@nethsec) (gcc version 11.2.0) #0 SMP Mon Jan 1 00:00:00 2024\n"
	with patch('builtins.open', mock_open(read_data=mock_version)):
		result = inventory.info_kernel_version(u)
		assert result == "5.10.176"
	
	# Test exception handling (file not found)
	with patch('builtins.open', side_effect=FileNotFoundError):
		result = inventory.info_kernel_version(u)
		assert result == ''

def test_info_uptime_seconds():
	"""Test info_uptime_seconds reads from /proc/uptime"""
	u = EUci()
	
	# Test successful read
	mock_uptime = "12345.67 98765.43\n"
	with patch('builtins.open', mock_open(read_data=mock_uptime)):
		result = inventory.info_uptime_seconds(u)
		assert result == 12345
	
	# Test exception handling
	with patch('builtins.open', side_effect=FileNotFoundError):
		result = inventory.info_uptime_seconds(u)
		assert result == 0

def test_info_fqdn(tmp_path):
	"""Test info_fqdn retrieves hostname from UCI"""
	# Setup system config
	system_db = """
config system
	option hostname 'myhost'
	option domain 'example.com'
"""
	with tmp_path.joinpath('system').open('w') as fp:
		fp.write(system_db)
	with tmp_path.joinpath('ns-plug').open('w') as fp:
		fp.write("config config\n\toption type 'no'\n")
	
	u = EUci(confdir=tmp_path.as_posix())
	result = inventory.info_fqdn(u)
	# Should be anonymized since no subscription
	assert result.startswith('anon-')

def test_info_default_ipv4_dig_method(tmp_path):
	"""Test info_default_ipv4 with dig method"""
	with tmp_path.joinpath('ns-plug').open('w') as fp:
		fp.write("config config\n\toption type 'no'\n")
	u = EUci(confdir=tmp_path.as_posix())
	
	# Mock successful dig command
	mock_result = MagicMock()
	mock_result.returncode = 0
	mock_result.stdout = '"192.0.2.1"\n'
	
	with patch('subprocess.run', return_value=mock_result):
		result = inventory.info_default_ipv4(u)
		assert result.startswith('anon-')  # Should be anonymized

def test_info_default_ipv4_curl_fallback(tmp_path):
	"""Test info_default_ipv4 falls back to curl when dig fails"""
	with tmp_path.joinpath('ns-plug').open('w') as fp:
		fp.write("config config\n\toption type 'no'\n")
	u = EUci(confdir=tmp_path.as_posix())
	
	# Mock dig failure and curl success
	def mock_subprocess_run(cmd, **kwargs):
		result = MagicMock()
		if 'dig' in cmd:
			result.returncode = 1
			result.stdout = ''
		elif 'curl' in cmd:
			result.returncode = 0
			result.stdout = '203.0.113.1\n'
		else:
			result.returncode = 1
			result.stdout = ''
		return result
	
	with patch('subprocess.run', side_effect=mock_subprocess_run):
		result = inventory.info_default_ipv4(u)
		assert result.startswith('anon-')

def test_info_default_ipv4_ip_command_fallback(tmp_path):
	"""Test info_default_ipv4 falls back to ip command when dig and curl fail"""
	with tmp_path.joinpath('network').open('w') as fp:
		fp.write(network_db)
	with tmp_path.joinpath('firewall').open('w') as fp:
		fp.write(firewall_db)
	with tmp_path.joinpath('ns-plug').open('w') as fp:
		fp.write("config config\n\toption type 'no'\n")
	u = EUci(confdir=tmp_path.as_posix())
	
	# Mock dig and curl failure, ip command success
	def mock_subprocess_run(cmd, **kwargs):
		result = MagicMock()
		if isinstance(cmd, list) and 'ip' in cmd:
			result.returncode = 0
			result.stdout = '[{"addr_info": [{"family": "inet", "local": "198.51.100.1"}]}]'
		else:
			result.returncode = 1
			result.stdout = ''
		return result
	
	with patch('subprocess.run', side_effect=mock_subprocess_run):
		with patch('nethsec.utils.get_all_wan_devices', return_value=['eth0']):
			result = inventory.info_default_ipv4(u)
			assert result.startswith('anon-')

def test_info_default_ipv4_all_methods_fail(tmp_path):
	"""Test info_default_ipv4 returns empty string when all methods fail"""
	with tmp_path.joinpath('ns-plug').open('w') as fp:
		fp.write("config config\n\toption type 'no'\n")
	u = EUci(confdir=tmp_path.as_posix())
	
	# Mock all methods failing
	mock_result = MagicMock()
	mock_result.returncode = 1
	mock_result.stdout = ''
	
	with patch('subprocess.run', return_value=mock_result):
		with patch('nethsec.utils.get_all_wan_devices', return_value=[]):
			result = inventory.info_default_ipv4(u)
			assert result == ''

def test_info_default_ipv6_no_wan_ipv6(tmp_path):
	"""Test info_default_ipv6 returns empty when no IPv6 on WAN"""
	with tmp_path.joinpath('ns-plug').open('w') as fp:
		fp.write("config config\n\toption type 'no'\n")
	u = EUci(confdir=tmp_path.as_posix())
	
	# Mock no WAN devices or no IPv6
	mock_result = MagicMock()
	mock_result.returncode = 0
	mock_result.stdout = '[]'
	
	with patch('subprocess.run', return_value=mock_result):
		with patch('nethsec.utils.get_all_wan_devices', return_value=['eth0']):
			result = inventory.info_default_ipv6(u)
			assert result == ''

def test_info_default_ipv6_with_wan_ipv6(tmp_path):
	"""Test info_default_ipv6 with IPv6 on WAN"""
	with tmp_path.joinpath('ns-plug').open('w') as fp:
		fp.write("config config\n\toption type 'no'\n")
	u = EUci(confdir=tmp_path.as_posix())
	
	# Mock WAN with IPv6
	def mock_subprocess_run(cmd, **kwargs):
		result = MagicMock()
		if isinstance(cmd, list) and 'ip' in cmd and '-6' in cmd:
			result.returncode = 0
			result.stdout = '[{"addr_info": [{"family": "inet6", "local": "2001:db8::1", "scope": "global"}]}]'
		elif isinstance(cmd, list) and 'dig' in cmd:
			result.returncode = 0
			result.stdout = '"2001:db8::2"\n'
		else:
			result.returncode = 1
			result.stdout = ''
		return result
	
	with patch('subprocess.run', side_effect=mock_subprocess_run):
		with patch('nethsec.utils.get_all_wan_devices', return_value=['eth0']):
			result = inventory.info_default_ipv6(u)
			assert result.startswith('anon-')

def test_info_default_ipv6_fallback_to_curl(tmp_path):
	"""Test info_default_ipv6 falls back to curl when dig fails"""
	with tmp_path.joinpath('ns-plug').open('w') as fp:
		fp.write("config config\n\toption type 'no'\n")
	u = EUci(confdir=tmp_path.as_posix())
	
	# Mock WAN with IPv6, dig fails, curl succeeds
	def mock_subprocess_run(cmd, **kwargs):
		result = MagicMock()
		if isinstance(cmd, list) and 'ip' in cmd and '-6' in cmd:
			result.returncode = 0
			result.stdout = '[{"addr_info": [{"family": "inet6", "local": "2001:db8::1", "scope": "global"}]}]'
		elif isinstance(cmd, list) and 'curl' in cmd:
			result.returncode = 0
			result.stdout = '2001:db8::3\n'
		else:
			result.returncode = 1
			result.stdout = ''
		return result
	
	with patch('subprocess.run', side_effect=mock_subprocess_run):
		with patch('nethsec.utils.get_all_wan_devices', return_value=['eth0']):
			result = inventory.info_default_ipv6(u)
			assert result.startswith('anon-')

def test_info_package_updates_available_with_updates():
	"""Test info_package_updates_available when updates are available"""
	u = EUci()
	
	mock_result = MagicMock()
	mock_result.returncode = 0
	mock_result.stdout = '{"updates": ["package1", "package2"]}'
	
	with patch('subprocess.run', return_value=mock_result):
		result = inventory.info_package_updates_available(u)
		assert result is True

def test_info_package_updates_available_no_updates():
	"""Test info_package_updates_available when no updates available"""
	u = EUci()
	
	mock_result = MagicMock()
	mock_result.returncode = 0
	mock_result.stdout = '{"updates": []}'
	
	with patch('subprocess.run', return_value=mock_result):
		result = inventory.info_package_updates_available(u)
		assert result is False

def test_info_package_updates_available_command_fails():
	"""Test info_package_updates_available when command fails"""
	u = EUci()
	
	mock_result = MagicMock()
	mock_result.returncode = 1
	mock_result.stdout = ''
	
	with patch('subprocess.run', return_value=mock_result):
		result = inventory.info_package_updates_available(u)
		assert result is False

def test_parse_version_with_prefix():
	"""Test parse_version removes NethSecurity prefix"""
	assert inventory.parse_version('NethSecurity 8.1.0-dev') == (8, 1, 0)
	assert inventory.parse_version('NethSecurity 8.2.1') == (8, 2, 1)

def test_parse_version_without_prefix():
	"""Test parse_version handles versions without prefix"""
	assert inventory.parse_version('8.1.0-dev') == (8, 1, 0)
	assert inventory.parse_version('8.2.1') == (8, 2, 1)

def test_parse_version_comparison():
	"""Test parse_version version comparison logic"""
	v1 = inventory.parse_version('8.1.0')
	v2 = inventory.parse_version('8.2.0')
	v3 = inventory.parse_version('8.1.1')
	
	assert v2 > v1
	assert v3 > v1
	assert v2 > v3

def test_parse_version_invalid():
	"""Test parse_version handles invalid input"""
	result = inventory.parse_version('invalid')
	assert result == ()
	
	result = inventory.parse_version('')
	assert result == ()

def test_info_image_updates_available_update_exists():
	"""Test info_image_updates_available when newer version exists"""
	u = EUci()
	
	mock_result = MagicMock()
	mock_result.returncode = 0
	mock_result.stdout = '{"currentVersion": "NethSecurity 8.1.0", "lastVersion": "NethSecurity 8.2.0"}'
	
	with patch('subprocess.run', return_value=mock_result):
		result = inventory.info_image_updates_available(u)
		assert result is True

def test_info_image_updates_available_no_update():
	"""Test info_image_updates_available when current version is latest"""
	u = EUci()
	
	mock_result = MagicMock()
	mock_result.returncode = 0
	mock_result.stdout = '{"currentVersion": "NethSecurity 8.2.0", "lastVersion": "NethSecurity 8.2.0"}'
	
	with patch('subprocess.run', return_value=mock_result):
		result = inventory.info_image_updates_available(u)
		assert result is False

def test_info_image_updates_available_patch_update():
	"""Test info_image_updates_available when a patch update is available"""
	u = EUci()
	
	mock_result = MagicMock()
	mock_result.returncode = 0
	mock_result.stdout = '{"currentVersion": "NethSecurity 8.2.0", "lastVersion": "NethSecurity 8.2.1"}'
	
	with patch('subprocess.run', return_value=mock_result):
		result = inventory.info_image_updates_available(u)
		assert result is True

def test_info_image_updates_available_minor_update():
	"""Test info_image_updates_available when a minor update is available"""
	u = EUci()
	
	mock_result = MagicMock()
	mock_result.returncode = 0
	mock_result.stdout = '{"currentVersion": "NethSecurity 8.2.0", "lastVersion": "NethSecurity 8.3.0"}'
	
	with patch('subprocess.run', return_value=mock_result):
		result = inventory.info_image_updates_available(u)
		assert result is True

def test_info_image_updates_available_current_newer():
	"""Test info_image_updates_available when current version is newer than last"""
	u = EUci()
	
	mock_result = MagicMock()
	mock_result.returncode = 0
	mock_result.stdout = '{"currentVersion": "NethSecurity 8.3.0", "lastVersion": "NethSecurity 8.2.0"}'
	
	with patch('subprocess.run', return_value=mock_result):
		result = inventory.info_image_updates_available(u)
		assert result is False

def test_info_image_updates_available_command_fails():
	"""Test info_image_updates_available when command fails"""
	u = EUci()

	mock_result = MagicMock()
	mock_result.returncode = 1
	mock_result.stdout = ''

	with patch('subprocess.run', return_value=mock_result):
		result = inventory.info_image_updates_available(u)
		assert result is False

def test_fact_extra_packages_with_extras(tmp_path):
	"""Test fact_extra_packages reports packages present in current world but not in base world"""
	u = EUci()

	base_file = tmp_path.joinpath('apk_world_base')
	base_file.write_text("bash\nlibc\nnginx-ssl\n")

	cur_file = tmp_path.joinpath('apk_world')
	cur_file.write_text("bash\nlibc\nnginx-ssl\ncheckmk-agent\nnut-server\n")

	with patch('nethsec.inventory.APK_WORLD', str(cur_file)), patch('nethsec.inventory.APK_WORLD_BASE', str(base_file)):
		result = inventory.fact_extra_packages(u)
		assert result == {'count': 2, 'packages': ['checkmk-agent', 'nut-server']}

def test_fact_extra_packages_no_extras(tmp_path):
	"""Test fact_extra_packages reports no extras when current and base worlds match"""
	u = EUci()

	base_file = tmp_path.joinpath('apk_world_base')
	base_file.write_text("bash\nlibc\nnginx-ssl\n")

	cur_file = tmp_path.joinpath('apk_world')
	cur_file.write_text("bash\nlibc\nnginx-ssl\n")

	with patch('nethsec.inventory.APK_WORLD', str(cur_file)), patch('nethsec.inventory.APK_WORLD_BASE', str(base_file)):
		result = inventory.fact_extra_packages(u)
		assert result == {'count': 0, 'packages': []}

def test_fact_extra_packages_missing_base_world(tmp_path):
	"""Test fact_extra_packages returns empty result when the base world file is missing"""
	u = EUci()

	base_file = tmp_path.joinpath('apk_world_base_missing')

	cur_file = tmp_path.joinpath('apk_world')
	cur_file.write_text("bash\nlibc\nnginx-ssl\ncheckmk-agent\n")

	with patch('nethsec.inventory.APK_WORLD', str(cur_file)), patch('nethsec.inventory.APK_WORLD_BASE', str(base_file)):
		result = inventory.fact_extra_packages(u)
		assert result == {'count': 0, 'packages': []}

def test_fact_extra_packages_strips_version_constraints(tmp_path):
	"""Test fact_extra_packages strips version constraints before comparing package names"""
	u = EUci()

	base_file = tmp_path.joinpath('apk_world_base')
	base_file.write_text("base-files=1711~f5dae5ece4\nlibc=1.2.5-r5\n")

	cur_file = tmp_path.joinpath('apk_world')
	cur_file.write_text("base-files=1712~aaaaaaaaaa\nlibc=1.2.6-r0\ncheckmk-agent\n")

	with patch('nethsec.inventory.APK_WORLD', str(cur_file)), patch('nethsec.inventory.APK_WORLD_BASE', str(base_file)):
		result = inventory.fact_extra_packages(u)
		assert result == {'count': 1, 'packages': ['checkmk-agent']}

def test_fact_extra_packages_ignores_noise_lines(tmp_path):
	"""Test fact_extra_packages ignores blank lines, comments, and '!' lines in the current world"""
	u = EUci()

	base_file = tmp_path.joinpath('apk_world_base')
	base_file.write_text("bash\nlibc\nnginx-ssl\n")

	cur_file = tmp_path.joinpath('apk_world')
	cur_file.write_text("bash\nlibc\nnginx-ssl\n\n# comment\n!conflictpkg\n")

	with patch('nethsec.inventory.APK_WORLD', str(cur_file)), patch('nethsec.inventory.APK_WORLD_BASE', str(base_file)):
		result = inventory.fact_extra_packages(u)
		assert result == {'count': 0, 'packages': []}
