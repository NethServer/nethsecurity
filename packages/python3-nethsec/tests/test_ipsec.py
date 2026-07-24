import pathlib

import pytest
from euci import EUci
from pytest_mock import MockFixture
from nethsec import ipsec, utils

templates_db = """
config template_rule 'ns_ipsec_esp'
	option name 'Allow-IPSec-ESP'
	option src 'wan'
	option proto 'esp'
	option target 'ACCEPT'

config template_rule 'ns_ipsec_ike'
	option name 'Allow-IPSec-IKE'
	option src 'wan'
	option dest_port '500'
	option proto 'udp'
	option target 'ACCEPT'

config template_rule 'ns_ipsec_nat'
	option name 'Allow-IPSec-NAT'
	option src 'wan'
	option dest_port '500'
	option proto 'udp'
	option target 'ACCEPT'
"""

@pytest.fixture
def e_uci(tmp_path: pathlib.Path) -> EUci:
    conf_dir = tmp_path.joinpath('conf')
    conf_dir.mkdir()
    save_dir = tmp_path.joinpath('save')
    save_dir.mkdir()
    return EUci(confdir=conf_dir.as_posix(), savedir=save_dir.as_posix())


@pytest.fixture
def e_uci_with_data(e_uci: EUci):
    with pathlib.Path(e_uci.confdir()).joinpath('templates').open('w') as fp:
        fp.write(templates_db)
    with pathlib.Path(e_uci.confdir()).joinpath('firewall').open('a') as fp:
        pass
    return e_uci

def test_init_ipsec(e_uci):
    ipsec.init_ipsec(e_uci)
    assert(e_uci.get('ipsec', 'ns_ipsec_global') == 'ipsec')
    assert(e_uci.get('ipsec', 'ns_ipsec_global', 'debug') == '0')
    assert(e_uci.get('ipsec', 'ns_ipsec_global', 'zone') == ipsec.IPSEC_ZONE)

def test_open_firewall_ports(e_uci_with_data):
    ipsec.open_firewall_ports(e_uci_with_data)
    nat = ike = esp = False
    for r in utils.get_all_by_type(e_uci_with_data, 'firewall', 'rule'):
        name = e_uci_with_data.get('firewall', r, 'name')
        if name == 'Allow-IPSec-NAT':
            nat = True
        elif name == 'Allow-IPSec-IKE':
            ike = True
        elif name == 'Allow-IPSec-ESP':
            esp = True
    assert (nat and ipsec and esp)

def test_add_trusted_interface(e_uci_with_data):
    ipsec.add_trusted_interface(e_uci_with_data, 'ipsec1')
    count = 0
    zid = ''
    # check the zone has been created
    for section in e_uci_with_data.get_all('firewall'):
        if e_uci_with_data.get('firewall', section) == 'zone':
            if e_uci_with_data.get('firewall', section, 'name') == ipsec.IPSEC_ZONE:
                count = count + 1
                zid = section
    assert(count == 1)
    assert(zid)
    assert(e_uci_with_data.get_all('firewall', zid, 'network') == ('ipsec1',))
    # check the zone has not been duplicated
    count = 0
    ipsec.add_trusted_interface(e_uci_with_data, 'ipsec2')
    for section in e_uci_with_data.get_all('firewall'):
        if e_uci_with_data.get('firewall', section) == 'zone':
            if e_uci_with_data.get('firewall', section, 'name') == ipsec.IPSEC_ZONE:
                count = count + 1
    assert(count == 1)
    assert('ipsec1' in e_uci_with_data.get_all('firewall', zid, 'network'))
    assert('ipsec2' in e_uci_with_data.get_all('firewall', zid, 'network'))

