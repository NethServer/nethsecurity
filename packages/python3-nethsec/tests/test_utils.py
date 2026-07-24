import pytest
from nethsec import utils
from euci import EUci
from unittest.mock import MagicMock, patch

# Setup fake ip command output
ip_json='[{"ifindex":9,"ifname":"vnet3","flags":["BROADCAST","MULTICAST","UP","LOWER_UP"],"mtu":1500,"qdisc":"noqueue","master":"virbr2","operstate":"UNKNOWN","group":"default","txqlen":1000,"link_type":"ether","address":"fe:62:31:19:0b:29","broadcast":"ff:ff:ff:ff:ff:ff","addr_info":[{"family":"inet6","local":"fe80::fc62:31ff:fe19:b29","prefixlen":64,"scope":"link","valid_life_time":4294967295,"preferred_life_time":4294967295}]},{"ifindex":2,"ifname":"eth0","flags":["BROADCAST","MULTICAST","UP","LOWER_UP"],"mtu":1500,"qdisc":"fq_codel","master":"br-lan","operstate":"UP","linkmode":"DEFAULT","group":"default","txqlen":1000,"link_type":"ether","address":"52:54:00:6a:50:bf","broadcast":"ff:ff:ff:ff:ff:ff"},{"ifindex":3,"ifname":"eth1","flags":["BROADCAST","MULTICAST","UP","LOWER_UP"],"mtu":1500,"qdisc":"fq_codel","operstate":"UP","linkmode":"DEFAULT","group":"default","txqlen":1000,"link_type":"ether","address":"52:54:00:20:82:a6","broadcast":"ff:ff:ff:ff:ff:ff"},{"ifindex":4,"ifname":"eth2","flags":["BROADCAST","MULTICAST"],"mtu":1500,"qdisc":"noop","operstate":"DOWN","linkmode":"DEFAULT","group":"default","txqlen":1000,"link_type":"ether","address":"52:54:00:75:1c:c1","broadcast":"ff:ff:ff:ff:ff:ff"},{"ifindex":5,"ifname":"eth3","flags":["BROADCAST","MULTICAST"],"mtu":1500,"qdisc":"noop","operstate":"DOWN","linkmode":"DEFAULT","group":"default","txqlen":1000,"link_type":"ether","address":"52:54:00:ad:6f:63","broadcast":"ff:ff:ff:ff:ff:ff"},{"ifindex":6,"ifname":"ifb-dns","flags":["BROADCAST","NOARP","UP","LOWER_UP"],"mtu":1500,"qdisc":"fq_codel","operstate":"UNKNOWN","linkmode":"DEFAULT","group":"default","txqlen":32,"link_type":"ether","address":"72:79:65:12:07:07","broadcast":"ff:ff:ff:ff:ff:ff"},{"ifindex":7,"ifname":"br-lan","flags":["BROADCAST","MULTICAST","UP","LOWER_UP"],"mtu":1500,"qdisc":"noqueue","operstate":"UP","linkmode":"DEFAULT","group":"default","txqlen":1000,"link_type":"ether","address":"52:54:00:6a:50:bf","broadcast":"ff:ff:ff:ff:ff:ff"},{"ifindex":9,"ifname":"bond-bond1","flags":["BROADCAST","MULTICAST","MASTER","UP","LOWER_UP"],"mtu":1500,"qdisc":"noqueue","operstate":"UP","linkmode":"DEFAULT","group":"default","txqlen":1000,"link_type":"ether","address":"52:54:00:ad:6f:63","broadcast":"ff:ff:ff:ff:ff:ff"},{"ifindex":8,"ifname":"tuntunsubnet","flags":["POINTOPOINT","MULTICAST","NOARP","UP","LOWER_UP"],"mtu":1500,"qdisc":"fq_codel","operstate":"UNKNOWN","linkmode":"DEFAULT","group":"default","txqlen":500,"link_type":"none"}, {"ifindex":69,"ifname":"pppoe-w1","flags":["POINTOPOINT","MULTICAST","NOARP","UP","LOWER_UP"],"mtu":1492,"qdisc":"fq_codel","operstate":"UNKNOWN","linkmode":"DEFAULT","group":"default","txqlen":3,"link_type":"ppp"},{"ifindex":20,"link":"eth1","ifname":"eth1.4","flags":["BROADCAST","MULTICAST","UP","LOWER_UP"],"mtu":1500,"qdisc":"noqueue","master":"br-lan","operstate":"UP","linkmode":"DEFAULT","group":"default","txqlen":1000,"link_type":"ether","address":"52:54:00:20:82:a6","broadcast":"ff:ff:ff:ff:ff:ff"}]'
mock_ip_stdout = MagicMock()
mock_ip_stdout.configure_mock(**{"stdout": ip_json})

test_db = """
config mytype section1
	option name 'myname1'
	option opt2 'value2'

config mytype section2
	option name 'myname2'
	list opt1 'val1'
	list opt1 'val2'
	option opt2 'value2'

config mytype2 section3
	option name 'myname3'
"""

firewall_db = """
config zone wan1
	option name 'wan'
	list network 'wan'
	list network 'wan6'
	option input 'REJECT'
	option output 'ACCEPT'
	option forward 'REJECT'
	option masq '1'
	option mtu_fix '1'
	list device 'eth2.1'

config zone
	option name 'lan'
	list network 'lan'
	list network 'br-lan'
	option input 'ACCEPT'
	option output 'ACCEPT'
	option forward 'ACCEPT'
	list device 'tunrw1'
	list device 'ipsec2'
"""

network_db = """
config interface lan
	option device 'vnet3'
	option proto 'static'

config device
	option name 'br-lan'
	option type 'bridge'
	list ports 'eth0'

config device
	option type '8021q'
	option ifname 'eth2'
	option vid '1'
	option name 'eth2.1'

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

config device
	option ifname 'eth0'
	option name 'eth0.1'
	option type '8021q'
	option vid '45'

config device 'ns_29a705ea'
	option name 'eth3.2'
	option type '8021q'
	option ifname 'eth3'
	option vid '2'
"""

dedalo_db = """
config dedalo 'config'
	option disabled '0'
	option interface 'eth2'
"""

def _setup_db(tmp_path):
     # setup fake db
    with tmp_path.joinpath('test').open('w') as fp:
        fp.write(test_db)
    with tmp_path.joinpath('network').open('w') as fp:
        fp.write(network_db)
    with tmp_path.joinpath('firewall').open('w') as fp:
        fp.write(firewall_db)
    with tmp_path.joinpath('dedalo').open('w') as fp:
        fp.write(dedalo_db)
    return EUci(confdir=tmp_path.as_posix())

def test_sanitize():
    assert utils.sanitize("good") == "good"
    assert utils.sanitize("with-dash") == "with_dash"
    assert utils.sanitize('$%_()') == '____'
    assert utils.sanitize('UPPER') == 'UPPER'
    assert utils.sanitize('numb3r') == 'numb3r'
    assert utils.sanitize('newline\n') == 'newline'
    assert utils.sanitize('newline\r') == 'newline'

def test_get_id():
    assert utils.get_id('no-good') == 'ns_no_good'
    assert utils.get_id('nospace ') == 'ns_nospace'
    assert utils.get_id('t1234') == 'ns_t1234'
    # str with 97 chars
    long_str = "ihTSEf2Y5rl8TX96pWFFPMty9LFgH3GezhVueGoDB6_aaIFhDSKe1ZR64cV41iSVhfrm5wJCUPFfMGx2fBZyhDIW9cl9SCI43"
    assert utils.get_id(long_str) == f'ns_{long_str}'
    assert utils.get_id(long_str+"123") == f'ns_{long_str}'

def test_get_id_length():
    assert utils.get_id("123456789012345", 15) == "ns_123456789012"

def test_get_all_by_type(tmp_path):
    u = _setup_db(tmp_path)
    records = utils.get_all_by_type(u, 'test', 'mytype')
    assert records != None
    assert 'section1' in records.keys()
    assert 'section2' in records.keys()
    assert 'section3' not in records.keys()
    assert records['section1']['name'] == 'myname1'
    assert records['section2']['name'] == 'myname2'
    assert records['section2']['opt1'] == ('val1', 'val2')

@patch("nethsec.utils.subprocess.run")
def test_get_device_name_valid(mock_run):
    # setup mock
    mock_run.return_value = mock_ip_stdout

    assert utils.get_device_name("fe:62:31:19:0b:29") == 'vnet3'

def test_get_device_name_not_valid():
    assert utils.get_device_name("aa:bb:cc:dd:66:55") == None

@patch("nethsec.utils.subprocess.run")
def test_get_interface_from_mac(mock_run2, tmp_path):
    # setup mock
    mock_run2.return_value = mock_ip_stdout
    u = _setup_db(tmp_path)

    assert utils.get_interface_from_mac(u, "fe:62:31:19:0b:29") == 'lan'
    assert utils.get_interface_from_mac(u, "aa:bb:cc:dd:66:55") == None

def test_get_interface_from_device(tmp_path):
    u = _setup_db(tmp_path)

    assert utils.get_interface_from_device(u, "vnet3") == 'lan'
    assert utils.get_interface_from_device(u, "vnet4") == None

def test_get_all_by_option(tmp_path):
    u = _setup_db(tmp_path)
    return_map = {"section1": u.get_all("test", "section1"), "section2": u.get_all("test", "section2")}
    assert(utils.get_all_by_option(u, 'test', 'opt2', 'value2') == return_map)
    assert(utils.get_all_by_option(u, 'test', 'opt2', 'value2', deep = False) == list(return_map.keys()))

def test_get_all_wan_devices(tmp_path):
    u = _setup_db(tmp_path)
    assert(set(utils.get_all_wan_devices(u)) == set(['eth1', 'eth2.1']))

def test_get_all_lan_devices(tmp_path):
    u = _setup_db(tmp_path)
    assert(set(utils.get_all_lan_devices(u)) == set(['vnet3']))

def test_get_random_id():
    id1 = utils.get_random_id()
    id2 = utils.get_random_id()
    assert len(id1) == 11
    assert id1[0:3] == "ns_"
    assert id1 != id2

def test_error():
    obj = utils.generic_error("my Error ")
    assert obj == {"error": "my_error"}

def test_validation_error():
    er1 = utils.validation_error("param1", "my Error ", "val1")
    assert er1 == {"validation": {"errors": [{"parameter": "param1", "message": "my_error", "value": "val1"}]}}
    er2 = utils.validation_error("param1")
    assert er2 == {"validation": {"errors": [{"parameter": "param1", "message": "", "value": ""}]}}

def test_validation_errors():
    er1 = utils.validation_errors([
        ["param1", " my Error ", "val1"],
        ["param2", " invalid_value ", False],
        ])
    assert er1 == {"validation": {"errors": [{"parameter": "param1", "message": "my_error", "value": "val1"}, {"parameter": "param2", "message": "invalid_value", "value": False}]}}

@patch("nethsec.utils.subprocess.run")
def test_get_unassigned_devices(mock_run_ip, tmp_path):
    # setup mock
    mock_run_ip.return_value = mock_ip_stdout

    u = _setup_db(tmp_path)
    assert utils.get_unassigned_devices(u) == ['eth0.1']

def test_check_password():
    password = "my_password"
    shadow = utils.shadow_password(password)
    assert utils.check_password(password, shadow) == True
    assert utils.check_password("wrong_password", shadow) == False
