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

index_db = (
    "V\t360101000000Z\t\t0A\tunknown\t/CN=myhost\n"
    "V\t360101000000Z\t\t0B\tunknown\t/CN=alice\n"
    "R\t360101000000Z\t250101000000Z\t0C\tunknown\t/CN=alice\n"
    "V\t360101000000Z\t\t0D\tunknown\t/CN=alice\n"
    "V\t360101000000Z\t\t0E\tunknown\t/CN=bob\n"
)

def _setup_pki(tmp_path, certs):
    # certs: issued file name -> serial
    import subprocess
    tmp_path.joinpath('index.txt').write_text(index_db)
    tmp_path.joinpath('issued').mkdir()
    for name, serial in certs.items():
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-subj", f"/CN={name}",
                        "-set_serial", str(serial), "-days", "1", "-keyout", tmp_path.joinpath(f'{name}.key').as_posix(),
                        "-out", tmp_path.joinpath('issued', f'{name}.crt').as_posix()], check=True, capture_output=True)
    return tmp_path.as_posix()

def _index_status(pki_dir):
    with open(f"{pki_dir}/index.txt") as fp:
        return {f[3]: (f[0], f[2]) for f in (line.split("\t") for line in fp)}

def test_revoke_stale_certificates(tmp_path):
    # server certificate is saved as server.crt, but its common name is the hostname
    pki_dir = _setup_pki(tmp_path, {"server": 0x0A, "alice": 0x0D})
    # alice certificate from an older regeneration and bob certificate of a deleted user
    assert ovpn.revoke_stale_certificates(pki_dir) == ["0B", "0E"]
    status = _index_status(pki_dir)
    assert [status[s][0] for s in ["0A", "0B", "0C", "0D", "0E"]] == ["V", "R", "R", "V", "R"]
    assert status["0B"][1].endswith("Z")
    assert status["0C"][1] == "250101000000Z"
    # running it again does nothing
    assert ovpn.revoke_stale_certificates(pki_dir) == []

def test_revoke_stale_certificates_unreadable(tmp_path):
    pki_dir = _setup_pki(tmp_path, {"server": 0x0A, "alice": 0x0D})
    tmp_path.joinpath('issued', 'bob.crt').write_text("broken")
    with pytest.raises(RuntimeError, match="bob.crt"):
        ovpn.revoke_stale_certificates(pki_dir)
    assert tmp_path.joinpath('index.txt').read_text() == index_db

def test_revoke_stale_certificates_empty_issued(tmp_path):
    pki_dir = _setup_pki(tmp_path, {})
    assert ovpn.revoke_stale_certificates(pki_dir) == []
    assert tmp_path.joinpath('index.txt').read_text() == index_db
