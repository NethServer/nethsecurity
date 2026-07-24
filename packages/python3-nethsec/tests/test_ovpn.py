import pytest
import ipaddress
from nethsec import ovpn
from euci import EUci

openvpn_db = """
config openvpn 'custom_config'
    option port '1194'

config openvpn 'custom_config2'
    option port '1300'
    option server '10.10.10.0 255.255.255.0'

config openvpn 'custom_config3'
    option port '1301'
    option server_bridge '10.8.0.4 255.255.255.0 10.8.0.128 10.8.0.254'

config openvpn 'custom_config4'
    option lport '1302'

config openvpn 'custom_config5'
    option lport '1303'
    option ifconfig '10.7.0.1 10.7.0.2'
"""

def _setup_db(tmp_path):
     # setup fake db
    with tmp_path.joinpath('openvpn').open('w') as fp:
        fp.write(openvpn_db)
    return EUci(confdir=tmp_path.as_posix())

def test_to_cidr():
    assert ovpn.to_cidr("255.255.255.0") == 24
    
def test_to_netmask():
    assert ovpn.to_netmask(24) == "255.255.255.0"

def test_is_used_network(tmp_path):
    u = _setup_db(tmp_path)
    assert ovpn.is_used_network(u, "10.10.10.0/24") == True
    assert ovpn.is_used_network(u, "10.8.0.0/24") == True
    assert ovpn.is_used_network(u, "10.7.0.0/24") == True
    assert ovpn.is_used_network(u, "192.168.1.0/24") == False

def test_generate_random_network(tmp_path):
    u = _setup_db(tmp_path)
    assert ipaddress.ip_network(ovpn.generate_random_network(u)).is_private

def test_opt2cidr():
    assert ovpn.opt2cidr("192.168.1.0 255.255.255.0") == "192.168.1.0/24"

def test_is_used_port(tmp_path):
    u = _setup_db(tmp_path)
    assert ovpn.is_used_port(u, 1194) == True
    assert ovpn.is_used_port(u, 1300) == True
    assert ovpn.is_used_port(u, 1301) == True
    assert ovpn.is_used_port(u, 1302) == True
    assert ovpn.is_used_port(u, 1303) == True
    assert ovpn.is_used_port(u, 1200) == False

def test_generate_random_port(tmp_path):
    u = _setup_db(tmp_path)
    assert type(ovpn.generate_random_port(u, 1200, 1210)) == type(1)