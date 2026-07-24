import pathlib

import pytest
from euci import EUci

from nethsec import mwan, objects
from nethsec.utils import ValidationError

network_db = """
config interface 'loopback'
        option device 'lo'
        option proto 'static'
        option ipaddr '127.0.0.1'
        option netmask '255.0.0.0'

config interface 'GREEN_1'
        option proto 'static'
        option device 'eth0'
        option ipaddr '192.168.200.2'
        option netmask '255.255.255.0'

config interface 'RED_1'
        option proto 'static'
        option device 'eth1'
        option ipaddr '10.0.0.2'
        option netmask '255.255.255.0'
        option gateway '10.0.0.1'

config interface 'RED_2'
        option proto 'static'
        option device 'eth2'
        option ipaddr '10.0.1.2'
        option netmask '255.255.255.0'
        option gateway '10.0.1.1'

config interface 'RED_3'
        option proto 'static'
        option device 'eth3'
        option ipaddr '10.0.2.2'
        option netmask '255.255.255.0'
        option gateway '10.0.2.1'

config device
        option name 'eth0'

config device
        option name 'eth1'

config device
        option name 'eth2'

config device
        option name 'eth3'
"""

ns_api_db = """
config defaults_mwan 'defaults_mwan'
        option initial_state 'online'
        option protocol 'ipv4'
        list track_ip '8.8.8.8'
        list track_ip '208.67.222.222'
        option tracking_method 'ping'
        option tracking_reliability '1'
        option ping_count '1'
        option ping_size '56'
        option ping_max_ttl '60'
        option ping_timeout '4'
        option ping_interval '10'
        option ping_failure_interval '5'
        option ping_recovery_interval '5'
        option interface_down_threshold '5'
        option interface_up_threshold '5'
        option link_quality '0'
        option quality_failure_latency '1000'
        option quality_failure_packet_loss '40'
        option quality_recovery_latency '500'
        option quality_recovery_packet_loss '10'
"""

objects_db = """
"""

dhcp_db = """
config domain 'ns_domain_mwan'
	option ip '7.8.9.1'
	option name 'host1'
	option ns_description 'Host 1'

config host 'ns_host_mwan'
	option ip '192.168.100.5'
	option mac 'fe:54:00:6a:50:bf'
	option dns '1'
	option name 'host2'
	option ns_description 'host2'
"""

users_db = """
"""

firewall_db = """
"""

@pytest.fixture
def e_uci(tmp_path: pathlib.Path) -> EUci:
    conf_dir = tmp_path.joinpath('conf')
    conf_dir.mkdir()
    save_dir = tmp_path.joinpath('save')
    save_dir.mkdir()
    with conf_dir.joinpath('network').open('w') as fp:
        fp.write(network_db)
    with conf_dir.joinpath('ns-api').open('w') as fp:
        fp.write(ns_api_db)
    with conf_dir.joinpath('mwan3').open('w') as fp:
        fp.write('')
    with conf_dir.joinpath('objects').open('w') as fp:
        fp.write(objects_db)
    with conf_dir.joinpath('dhcp').open('w') as fp:
        fp.write(dhcp_db)
    with conf_dir.joinpath('users').open('w') as fp:
        fp.write(users_db)
    with conf_dir.joinpath('firewall').open('w') as fp:
        fp.write(firewall_db)
    return EUci(confdir=conf_dir.as_posix(), savedir=save_dir.as_posix())


def test_create_interface(e_uci):
    assert mwan.__store_interface(e_uci, 'RED_1') == (True, True)
    assert mwan.__store_interface(e_uci, 'RED_2') == (True, True)
    # assert every interface has defaults
    assert e_uci.get('mwan3', 'RED_1') == 'interface'
    assert e_uci.get('mwan3', 'RED_1', 'enabled') == '1'
    assert e_uci.get('mwan3', 'RED_1', 'initial_state') == 'online'
    assert e_uci.get('mwan3', 'RED_1', 'family') == 'ipv4'
    assert e_uci.get('mwan3', 'RED_1', 'track_ip', list=True) == ('8.8.8.8', '208.67.222.222')
    assert e_uci.get('mwan3', 'RED_1', 'track_method') == 'ping'
    assert e_uci.get('mwan3', 'RED_1', 'reliability') == '1'
    assert e_uci.get('mwan3', 'RED_1', 'count') == '1'
    assert e_uci.get('mwan3', 'RED_1', 'size') == '56'
    assert e_uci.get('mwan3', 'RED_1', 'max_ttl') == '60'
    assert e_uci.get('mwan3', 'RED_1', 'timeout') == '4'
    assert e_uci.get('mwan3', 'RED_1', 'interval') == '10'
    assert e_uci.get('mwan3', 'RED_1', 'failure_interval') == '5'
    assert e_uci.get('mwan3', 'RED_1', 'recovery_interval') == '5'
    assert e_uci.get('mwan3', 'RED_1', 'down') == '5'
    assert e_uci.get('mwan3', 'RED_1', 'up') == '5'
    # assert interface has metric
    assert e_uci.get('network', 'RED_1', 'metric') == '30'
    assert e_uci.get('network', 'RED_2', 'metric') == '40'
    assert mwan.__store_interface(e_uci, 'RED_1') == (False, False)


def test_fail_create_invalid_interface(e_uci):
    with pytest.raises(ValueError) as err:
        mwan.__store_interface(e_uci, 'RED_4')
    assert err.value.args[0] == 'name'
    assert err.value.args[1] == 'invalid'
    assert err.value.args[2] == 'RED_4'


def test_interface_avoid_edit_of_metric(e_uci):
    e_uci.set('network', 'RED_1', 'metric', '10')
    assert mwan.__store_interface(e_uci, 'RED_1') == (True, False)


def test_create_member(e_uci):
    assert mwan.__store_member(e_uci, 'RED_1', 10, 100) == ('ns_RED_1_M10_W100', True)
    assert mwan.__store_member(e_uci, 'RED_1', 10, 100) == ('ns_RED_1_M10_W100', False)
    assert mwan.__store_member(e_uci, 'RED_1', 1, 100) == ('ns_RED_1_M1_W100', True)


def test_create_default_mwan(e_uci, mocker):
    mocker.patch('subprocess.run')
    assert mwan.store_policy(e_uci, 'default', [
        {
            'name': 'RED_1',
            'metric': '10',
            'weight': '200',
        },
        {
            'name': 'RED_2',
            'metric': '20',
            'weight': '100',
        }
    ]) == ['mwan3.ns_default',
           'mwan3.RED_1',
           'network.RED_1',
           'mwan3.ns_RED_1_M10_W200',
           'mwan3.RED_2',
           'network.RED_2',
           'mwan3.ns_RED_2_M20_W100',
           'mwan3.ns_default_rule']

    assert e_uci.get('mwan3', 'ns_default') == 'policy'
    assert e_uci.get('mwan3', 'ns_default', 'label') == 'default'
    assert e_uci.get('mwan3', 'ns_default', 'use_member', list=True) == (
        'ns_RED_1_M10_W200', 'ns_RED_2_M20_W100')
    assert e_uci.get('mwan3', 'ns_default', 'last_resort') == 'default'


def test_create_unique_mwan(e_uci, mocker):
    mocker.patch('subprocess.run')
    mwan.store_policy(e_uci, 'this', [])
    with pytest.raises(ValueError):
        mwan.store_policy(e_uci, 'this', [])


def test_metric_generation(e_uci):
    assert mwan.__generate_metric(e_uci) == 30
    assert mwan.__store_interface(e_uci, 'RED_1') == (True, True)
    assert mwan.__generate_metric(e_uci) == 40
    assert mwan.__generate_metric(e_uci) == 40
    assert mwan.__store_interface(e_uci, 'RED_2') == (True, True)
    assert mwan.__generate_metric(e_uci) == 50


def test_list_policies(e_uci, mocker):
    mocker.patch('subprocess.run')
    mwan.store_policy(e_uci, 'backup', [
        {
            'name': 'RED_1',
            'metric': '10',
            'weight': '200',
        },
        {
            'name': 'RED_2',
            'metric': '20',
            'weight': '100',
        }
    ])
    mwan.store_policy(e_uci, 'balance', [
        {
            'name': 'RED_3',
            'metric': '10',
            'weight': '200',
        },
        {
            'name': 'RED_2',
            'metric': '10',
            'weight': '100',
        }
    ])
    mwan.store_policy(e_uci, 'custom', [
        {
            'name': 'RED_3',
            'metric': '10',
            'weight': '200',
        },
        {
            'name': 'RED_2',
            'metric': '10',
            'weight': '100',
        },
        {
            'name': 'RED_1',
            'metric': '20',
            'weight': '100',
        }
    ])
    index = mwan.index_policies(e_uci)
    # check backup policy
    assert index[0]['name'] == 'ns_backup'
    assert index[0]['label'] == 'backup'
    assert index[0]['type'] == 'backup'
    assert index[0]['members'][10][0]['name'] == 'ns_RED_1_M10_W200'
    assert index[0]['members'][10][0]['interface'] == 'RED_1'
    assert index[0]['members'][10][0]['metric'] == '10'
    assert index[0]['members'][10][0]['weight'] == '200'
    assert index[0]['members'][20][0]['name'] == 'ns_RED_2_M20_W100'
    assert index[0]['members'][20][0]['interface'] == 'RED_2'
    assert index[0]['members'][20][0]['metric'] == '20'
    assert index[0]['members'][20][0]['weight'] == '100'
    # check balance policy
    assert index[1]['name'] == 'ns_balance'
    assert index[1]['label'] == 'balance'
    assert index[1]['type'] == 'balance'
    assert index[1]['members'][10][0]['name'] == 'ns_RED_3_M10_W200'
    assert index[1]['members'][10][0]['interface'] == 'RED_3'
    assert index[1]['members'][10][0]['metric'] == '10'
    assert index[1]['members'][10][0]['weight'] == '200'
    assert index[1]['members'][10][1]['name'] == 'ns_RED_2_M10_W100'
    assert index[1]['members'][10][1]['interface'] == 'RED_2'
    assert index[1]['members'][10][1]['metric'] == '10'
    assert index[1]['members'][10][1]['weight'] == '100'
    # check custom policy
    assert index[2]['name'] == 'ns_custom'
    assert index[2]['label'] == 'custom'
    assert index[2]['type'] == 'custom'
    assert index[2]['members'][10][0]['name'] == 'ns_RED_3_M10_W200'
    assert index[2]['members'][10][0]['interface'] == 'RED_3'
    assert index[2]['members'][10][0]['metric'] == '10'
    assert index[2]['members'][10][0]['weight'] == '200'
    assert index[2]['members'][10][1]['name'] == 'ns_RED_2_M10_W100'
    assert index[2]['members'][10][1]['interface'] == 'RED_2'
    assert index[2]['members'][10][1]['metric'] == '10'
    assert index[2]['members'][10][1]['weight'] == '100'
    assert index[2]['members'][20][0]['name'] == 'ns_RED_1_M20_W100'
    assert index[2]['members'][20][0]['interface'] == 'RED_1'
    assert index[2]['members'][20][0]['metric'] == '20'
    assert index[2]['members'][20][0]['weight'] == '100'

def test_policy_length(e_uci, mocker):
    mocker.patch('subprocess.run')
    with pytest.raises(ValidationError) as e:
        assert mwan.store_policy(e_uci, 'nameisa15maxlength', [
            {
                'name': 'RED_1',
                'metric': '10',
                'weight': '200',
            },
            {
                'name': 'RED_2',
                'metric': '20',
                'weight': '100',
            }
        ])
    assert e.value.args[0] == 'name'
    assert e.value.args[1] == 'length_12_max'

def test_store_rule(e_uci, mocker):
    mocker.patch('subprocess.run')
    mwan.store_policy(e_uci, 'default', [
        {
            'name': 'RED_1',
            'metric': '20',
            'weight': '100',
        }
    ])
    assert mwan.store_rule(e_uci, 'rule 1', 'ns_default', 'udp', '192.168.1.1/24', '1-1024', '10.0.0.2/12',
                           '22,443', True) == 'mwan3.ns_rule_1'
    assert e_uci.get('mwan3', 'ns_rule_1') == 'rule'
    assert e_uci.get('mwan3', 'ns_rule_1', 'label') == 'rule 1'
    assert e_uci.get('mwan3', 'ns_rule_1', 'use_policy') == 'ns_default'
    assert e_uci.get('mwan3', 'ns_rule_1', 'proto') == 'udp'
    assert e_uci.get('mwan3', 'ns_rule_1', 'src_ip') == '192.168.1.1/24'
    assert e_uci.get('mwan3', 'ns_rule_1', 'src_port') == '1:1024'
    assert e_uci.get('mwan3', 'ns_rule_1', 'dest_ip') == '10.0.0.2/12'
    assert e_uci.get('mwan3', 'ns_rule_1', 'dest_port') == '22,443'
    assert e_uci.get('mwan3', 'ns_rule_1', 'sticky') == '1'

    domain_id = objects.add_domain_set(e_uci, "mydomainset6", "ipv4", ["test1.com", "test2.com"])
    with pytest.raises(ValueError):
        mwan.store_rule(e_uci, 'r_with_obj', 'ns_default', 'udp', ns_src="dhcp/ns_host_mwan", ns_dst=f"objects/{domain_id}")

    hostset_id = objects.add_host_set(e_uci, "myhostset", "ipv4", ["192.168.1.1"])
    id = mwan.store_rule(e_uci, 'r_with_obj', 'ns_default', 'udp', ns_src="dhcp/ns_host_mwan", ns_dst=f"objects/{hostset_id}")

    id = id.split('.')[1]
    assert e_uci.get('mwan3', id, 'ns_src') == "dhcp/ns_host_mwan"
    assert e_uci.get('mwan3', id, 'ns_dst') == f"objects/{hostset_id}"
    with pytest.raises(ValueError):
        mwan.store_rule(e_uci, 'rule_with_obj', 'ns_default', 'udp', ns_src="dhcp/ns_host_mwan", ns_dst="objects/invalid") 
    with pytest.raises(ValueError):
        mwan.store_rule(e_uci, 'rule_with_obj', 'ns_default', 'udp', ns_src=f"objects/{domain_id}")

def test_unique_rule(e_uci, mocker):
    mocker.patch('subprocess.run')
    mwan.store_policy(e_uci, 'default', [
        {
            'name': 'RED_1',
            'metric': '20',
            'weight': '100',
        }
    ])
    with pytest.raises(ValidationError) as e:
        mwan.store_rule(e_uci, 'rule 1', 'ns_default')
        mwan.store_rule(e_uci, 'rule 1', 'ns_default')

    assert e.value.args[0] == 'name'
    assert e.value.args[1] == 'unique'

def test_rule_length(e_uci, mocker):
    mocker.patch('subprocess.run')
    mwan.store_policy(e_uci, 'default', [
        {
            'name': 'RED_1',
            'metric': '20',
            'weight': '100',
        }
    ])
    with pytest.raises(ValidationError) as e:
        mwan.store_rule(e_uci, 'nameisa15maxlength', 'ns_default')
    assert e.value.args[0] == 'name'
    assert e.value.args[1] == 'length_12_max'


def test_missing_policy_rule(e_uci):
    with pytest.raises(ValidationError) as e:
        mwan.store_rule(e_uci, 'cool rule', 'ns_default')

    assert e.value.args[0] == 'policy'
    assert e.value.args[1] == 'invalid'
    assert e.value.args[2] == 'ns_default'


def test_delete_non_existent_policy(e_uci, mocker):
    mocker.patch('subprocess.run')
    with pytest.raises(ValidationError) as e:
        mwan.delete_policy(e_uci, 'ns_default')
    assert e.value.args[0] == 'name'
    assert e.value.args[1] == 'invalid'
    assert e.value.args[2] == 'ns_default'


def test_delete_policy(e_uci, mocker):
    mocker.patch('subprocess.run')
    mwan.store_policy(e_uci, 'default', [
        {
            'name': 'RED_1',
            'metric': '20',
            'weight': '100',
        }
    ])
    assert mwan.delete_policy(e_uci, 'ns_default') == ['mwan3.ns_default']
    assert e_uci.get('mwan3', 'ns_default', default=None) is None


def test_edit_policy(e_uci, mocker):
    mocker.patch('subprocess.run')
    mwan.store_policy(e_uci, 'default', [
        {
            'name': 'RED_1',
            'metric': '10',
            'weight': '100',
        },
        {
            'name': 'RED_2',
            'metric': '10',
            'weight': '100',
        }
    ])
    assert mwan.index_policies(e_uci)[0]['type'] == 'balance'
    assert mwan.edit_policy(e_uci, 'ns_default', 'new label', [
        {
            'name': 'RED_1',
            'metric': '20',
            'weight': '100',
        },
        {
            'name': 'RED_3',
            'metric': '10',
            'weight': '100',
        }
    ]) == ['mwan3.ns_default', 'mwan3.ns_RED_1_M20_W100', 'mwan3.RED_3', 'network.RED_3', 'mwan3.ns_RED_3_M10_W100']
    assert e_uci.get('mwan3', 'ns_default', 'label') == 'new label'
    assert mwan.index_policies(e_uci)[0]['type'] == 'backup'


def test_missing_policy(e_uci, mocker):
    mocker.patch('subprocess.run')
    with pytest.raises(ValidationError) as e:
        mwan.edit_policy(e_uci, 'dummy', '', [])
    assert e.value.args[0] == 'name'
    assert e.value.args[1] == 'invalid'
    assert e.value.args[2] == 'dummy'


def test_index_rules(e_uci, mocker):
    mocker.patch('subprocess.run')
    mwan.store_policy(e_uci, 'default', [
        {
            'name': 'RED_1',
            'metric': '10',
            'weight': '100',
        },
        {
            'name': 'RED_2',
            'metric': '10',
            'weight': '100',
        }
    ])
    mwan.store_rule(e_uci, 'rule 1', 'ns_default')
    index = mwan.index_rules(e_uci)
    assert index[0] == {
        'name': 'ns_default_rule',
        'label': 'Default Rule',
        'policy': {
            'name': 'ns_default',
            'label': 'default',
        },
        "sticky": False,
    }
    assert index[1] == {
        'name': 'ns_rule_1',
        'label': 'rule 1',
        'policy': {
            'name': 'ns_default',
            'label': 'default',
        },
        "sticky": False,
    }


def test_delete_rule(e_uci, mocker):
    mocker.patch('subprocess.run')
    mwan.store_policy(e_uci, 'default', [
        {
            'name': 'RED_1',
            'metric': '10',
            'weight': '100',
        },
        {
            'name': 'RED_2',
            'metric': '10',
            'weight': '100',
        }
    ])
    mwan.store_rule(e_uci, 'rule 1', 'ns_default')
    assert mwan.delete_rule(e_uci, 'ns_rule_1') == 'mwan3.ns_rule_1'
    assert 'ns_rule_1' not in e_uci.get_all('mwan3').keys()


def test_edit_rule(e_uci, mocker):
    mocker.patch('subprocess.run')
    mwan.store_policy(e_uci, 'hello world', [
        {
            'name': 'RED_1',
            'metric': '10',
            'weight': '100',
        },
        {
            'name': 'RED_2',
            'metric': '10',
            'weight': '100',
        }
    ])
    mwan.store_policy(e_uci, 'cool policy', [
        {
            'name': 'RED_3',
            'metric': '10',
            'weight': '100',
        },
        {
            'name': 'RED_1',
            'metric': '10',
            'weight': '100',
        }
    ])
    assert mwan.edit_rule(e_uci, 'ns_default_rule', 'ns_cool_policy', 'new label!', 'udp', '192.168.10.1/12', '80,443',
                          '0.0.0.0/0', '4040-8080') == 'mwan3.ns_default_rule'
    assert e_uci.get('mwan3', 'ns_default_rule', 'label') == 'new label!'
    assert e_uci.get('mwan3', 'ns_default_rule', 'use_policy') == 'ns_cool_policy'
    assert e_uci.get('mwan3', 'ns_default_rule', 'proto') == 'udp'
    assert e_uci.get('mwan3', 'ns_default_rule', 'src_ip') == '192.168.10.1/12'
    assert e_uci.get('mwan3', 'ns_default_rule', 'src_port') == '80,443'
    assert e_uci.get('mwan3', 'ns_default_rule', 'dest_ip') == '0.0.0.0/0'
    assert e_uci.get('mwan3', 'ns_default_rule', 'dest_port') == '4040:8080'

    assert mwan.edit_rule(e_uci, 'ns_default_rule', 'ns_cool_policy', 'new label2!', ns_src="dhcp/ns_host_mwan")
    assert e_uci.get('mwan3', 'ns_default_rule', 'ns_src') == "dhcp/ns_host_mwan"


def test_cant_edit_invalid_rule(e_uci, mocker):
    mocker.patch('subprocess.run')
    with pytest.raises(ValidationError) as e:
        mwan.edit_rule(e_uci, 'ns_default_rule', 'ns_cool_policy', 'new label!')
    assert e.value.args[0] == 'name'
    assert e.value.args[1] == 'invalid'
    assert e.value.args[2] == 'ns_default_rule'
    mwan.store_policy(e_uci, 'hello world', [
        {
            'name': 'RED_1',
            'metric': '10',
            'weight': '100',
        },
        {
            'name': 'RED_2',
            'metric': '10',
            'weight': '100',
        }
    ])
    with pytest.raises(ValidationError) as e:
        mwan.edit_rule(e_uci, 'ns_default_rule', 'ns_cool_policy', 'new label!')
    assert e.value.args[0] == 'policy'
    assert e.value.args[1] == 'invalid'
    assert e.value.args[2] == 'ns_cool_policy'

def test_policy_type(e_uci, mocker):
    mocker.patch('subprocess.run')
    mwan.store_policy(e_uci, 'custom', [
        {
            'name': 'RED_3',
            'metric': '10',
            'weight': '200',
        }
    ])
    assert mwan.index_policies(e_uci)[0]['type'] == 'custom'

def test_update_rules(e_uci, mocker):
    mocker.patch('subprocess.run')
    mwan.store_policy(e_uci, 'cool policy', [
        {
            'name': 'RED_3',
            'metric': '10',
            'weight': '100',
        },
        {
            'name': 'RED_1',
            'metric': '10',
            'weight': '100',
        }
    ])
    domain_id = objects.add_domain_set(e_uci, "mydomainset7", "ipv4", ["test1.com", "test2.com"])
    with pytest.raises(ValidationError):
        mwan.store_rule(e_uci, 'r_with_obj', 'ns_cool_policy', 'udp', ns_src="dhcp/ns_domain_mwan", ns_dst=f"objects/{domain_id}")

    id = mwan.store_rule(e_uci, 'r_with_obj', 'ns_cool_policy', 'udp', ns_src="dhcp/ns_domain_mwan", ns_dst=f"dhcp/ns_host_mwan")
    id = id.split('.')[1]
    mwan.update_rules(e_uci)
    assert e_uci.get('mwan3', id, 'src_ip') == '7.8.9.1'
    assert e_uci.get('mwan3', id, 'dest_ip') == '192.168.100.5'
