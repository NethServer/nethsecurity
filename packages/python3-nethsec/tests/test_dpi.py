import pathlib

import pytest
from euci import EUci
from pytest_mock import MockFixture

from nethsec import dpi, utils
from nethsec.utils import ValidationError

applications_file = """
# Comment to avoid

# another comment to avoid

app:133:netify.netflix
app:10119:netify.linkedin
app:10552:netify.tesla
app:10195:netify.avira
app:10194:netify.sophos
app:10244:netify.bbc
app:10362:netify.hulu
app:10118:netify.lets-encrypt
app:199:netify.snapchat
dom:133:dualstack.apiproxy-device-prod-nlb-1-4d12762d4ba53e45.elb.eu-west-1.amazonaws.com
net:10852:208.118.237.0/24
net:124:208.117.254.0/24
nsd:-1:39:YXBwID09ICduZXRpZnkuc2lnbmFsJyAmJiBwcm90b2NvbF9pZCA9PSA3OCAmJiAob3RoZXJfcG9ydCA9PSA0NDMgfHwgbG9jYWxfcG9ydCA9PSA0NDMpOw==
nsd:-1:67:YXBwID09ICduZXRpZnkuZ29vZ2xlLWNoYXQnICYmIHByb3RvY29sX2lkICE9IDY3ICYmIChvdGhlcl9wb3J0ID09IDUyMjggfHwgbG9jYWxfcG9ydCA9PSA1MjI4KTs=
"""

applications = {
    133: 'netify.netflix',
    10119: 'netify.linkedin',
    10552: 'netify.tesla',
    10195: 'netify.avira',
    10194: 'netify.sophos',
    10244: 'netify.bbc',
    10362: 'netify.hulu',
    10118: 'netify.lets-encrypt',
    199: 'netify.snapchat'
}

protocols = {
    116: 'Warcraft3',
    117: 'LotusNotes',
    121: 'Dropbox',
    127: 'RPC',
    128: 'NetFlow',
    129: 'SFlow',
    130: 'HTTP/Connect'
}

categories_file = """
{
    "application_index": [
        [
            3,
            [
                10362,
                10194,
                10552
            ]
        ],
        [
            33,
            [
                133,
                10119,
                10195,
                10244
            ]
        ],
        [
            20,
            [
                199
            ]
        ]
    ],
    "application_tag_index": {
        "first-category": 3,
        "unknown": 33,
        "last": 20
    },
    "protocol_index": [
        [
            1,
            [
                121,
                127,
                128
            ]
        ],
        [
            2,
            [
                116
            ]
        ],
        [
            4,
            [
                129,
                130
            ]
        ]
    ],
    "protocol_tag_index": {
        "base": 1,
        "games": 2,
        "low": 4
    }
}
"""

categories_file_old = """
{
  "last_update": 1696950440,
  "application_index": {
    "first-category": [
      10362,
      10194,
      10552
    ],
    "unknown": [
      133,
      10119,
      10195,
      10244
    ],
    "last": [
      199
    ]
  },
  "protocol_index": {
    "base": [
      121,
      127,
      128
    ],
    "games": [
      116
    ],
    "low": [
      129,
      130
    ]
  }
}
"""

application_categories = {
    10362: {
        'name': 'first-category'
    },
    10194: {
        'name': 'first-category'
    },
    10552: {
        'name': 'first-category'
    },
    133: {
        'name': 'unknown'
    },
    10119: {
        'name': 'unknown'
    },
    10195: {
        'name': 'unknown'
    },
    10244: {
        'name': 'unknown'
    },
    199: {
        'name': 'last'
    }
}

protocol_categories = {
    121: {
        'name': 'base'
    },
    127: {
        'name': 'base'
    },
    128: {
        'name': 'base'
    },
    116: {
        'name': 'games'
    },
    129: {
        'name': 'low'
    },
    130: {
        'name': 'low'
    }
}

application_output = """
   133: netify.netflix
 10119: netify.linkedin
 10552: netify.tesla
 10195: netify.avira
 10194: netify.sophos
 10244: netify.bbc
 10362: netify.hulu
 10118: netify.lets-encrypt
   199: netify.snapchat
"""

protocol_output = """
   116: Warcraft3
   117: LotusNotes
   121: Dropbox
   127: RPC
   128: NetFlow
   129: SFlow
   130: HTTP/Connect
"""

dpi_minimal_db = """
config main 'config'
    option log_blocked '0'
    option firewall_exemption '0'
    option enabled '0'
"""

dpi_db = """
config main 'config'
    option log_blocked '0'
    option firewall_exemption '0'
    option enabled '0'
    list popular_filters 'netify.netflix'
    list popular_filters 'netify.hulu'
    list popular_filters 'netify.whatsapp'
    list popular_filters 'netify.facebook'
    list popular_filters 'netify.sophos'
    list popular_filters 'HTTP/Connect'
    list popular_filters 'Dropbox'

config rule rule0
	option action 'block'
	list application 'netify.linkedin'
	list application 'netify.snapchat'
	list protocol 'HTTP/Connect'
	list source '192.168.100.1'
	list source '192.168.100.2'
	list source 'user:giacomo'
	list source 'group:g1'
	list category 'games'
	option device 'eth0'
	option enabled 1

config rule rule1
	option action 'block'
	list application 'netify.tesla'
	option device 'eth4'
	option enabled 0
	list exemption '192.168.100.3'

config rule rule2
	option action 'block'
	option criteria 'local_ip == 192.168.100.22 && application == "netify.facebook";'
	option enabled 1
	
config rule rule3
    option action 'video'
    list protocol 'HTTP/Connect'
    option device 'eth1'
    option enabled 1
"""

netifyd_config = """
config netifyd
	option enabled '1'
	option autoconfig '0'
	list internal_if 'br-lan'
	list internal_if 'eth0'
	list internal_if 'eth4'
	list internal_if 'tunrw1'
	list external_if 'eth2'
	list external_if 'eth1'
"""

network_config = """
config interface 'RED_1'
        option proto 'dhcp'
        option device 'eth1'
        option metric '1'

config interface 'RED_2'
        option proto 'dhcp'
        option device 'eth2'
        option metric '2'

config interface 'RED_3'
        option proto 'dhcp'
        option device 'eth3'
        option metric '3'

config interface 'GREEN_1'
        option proto 'static'
        option device 'eth0'
        option ipaddr '192.168.200.2'
        option netmask '255.255.255.0'
        option gateway '192.168.200.1'

config interface 'GREEN_2'
        option proto 'static'
        option device 'eth4'
        option ipaddr '10.0.3.1'
        option netmask '255.255.255.0'
        option gateway '10.0.3.0'

config interface 'GREEN_3'
        option proto 'static'
        option device 'br_lan'
        option ipaddr '10.1.1.1'
        option netmask '255.255.255.0'
        option gateway '10.1.1.0'
"""

firewall_config = """
config zone 'ns_lan'
        option name 'lan'
        option input 'ACCEPT'
        option output 'ACCEPT'
        option forward 'ACCEPT'
        list network 'GREEN_1'
        list network 'GREEN_2'

config zone 'ns_wan'
        option name 'wan'
        option input 'REJECT'
        option output 'ACCEPT'
        option forward 'REJECT'
        option masq '1'
        option mtu_fix '1'
        list network 'RED_1'
        list network 'RED_2'
        list network 'RED_3'
        
config zone 'ns_guests'
        option name 'guests'
        option input 'REJECT'
        option output 'ACCEPT'
        option forward 'REJECT'
        list network 'GREEN_1'
        
config zone 'ns_empty'
        option name 'guests'
        option input 'REJECT'
        option output 'ACCEPT'
        option forward 'REJECT'
"""


@pytest.fixture(autouse=True)
def mock_apply(mocker: MockFixture):
    """
    add/delete of rules and appgroups commit the dpi config and reload the dpi service right away;
    tests only care about the resulting uci state, not about actually reloading a system service.
    """
    return mocker.patch('nethsec.dpi.__apply')


@pytest.fixture
def e_uci(tmp_path: pathlib.Path) -> EUci:
    conf_dir = tmp_path.joinpath('conf')
    conf_dir.mkdir()
    save_dir = tmp_path.joinpath('save')
    save_dir.mkdir()
    with conf_dir.joinpath('dpi').open('w') as fp:
        fp.write(dpi_minimal_db)
    with conf_dir.joinpath('network').open('w') as fp:
        fp.write(network_config)
    with conf_dir.joinpath('firewall').open('w') as fp:
        fp.write(firewall_config)
    return EUci(confdir=conf_dir.as_posix(), savedir=save_dir.as_posix())


@pytest.fixture
def e_uci_with_data(e_uci: EUci):
    with pathlib.Path(e_uci.confdir()).joinpath('dpi').open('w') as fp:
        fp.write(dpi_db)
    with pathlib.Path(e_uci.confdir()).joinpath('netifyd').open('w') as fp:
        fp.write(netifyd_config)
    return e_uci


@pytest.fixture
def mock_load(mocker):
    mocker.patch('nethsec.dpi.__load_applications', return_value=applications)
    mocker.patch('nethsec.dpi.load_applications', return_value=applications)
    mocker.patch('nethsec.dpi.__load_application_categories', return_value=application_categories)
    mocker.patch('nethsec.dpi.load_protocols', return_value=protocols)
    mocker.patch('nethsec.dpi.__load_protocol_categories', return_value=protocol_categories)


def test_load_applications(mocker: MockFixture):
    mocker.patch('builtins.open', mocker.mock_open(read_data=applications_file))
    assert dpi.__load_applications() == applications


@pytest.mark.parametrize('data', [categories_file, categories_file_old])
def test_load_application_categories(mocker: MockFixture, data: str):
    mocker.patch('builtins.open', mocker.mock_open(read_data=data))
    assert dpi.__load_application_categories() == application_categories


@pytest.mark.parametrize('data', [categories_file, categories_file_old])
def test_load_protocol_categories(mocker: MockFixture, data: str):
    mocker.patch('builtins.open', mocker.mock_open(read_data=data))
    assert dpi.__load_protocol_categories() == protocol_categories


def test_load_applications_from_engine(mocker: MockFixture):
    process_result = mocker.stub('subprocess_return')
    process_result.stdout = bytes(application_output, 'utf-8')
    mocker.patch('subprocess.run', return_value=process_result)
    assert dpi.load_applications() == applications


def test_load_protocols(mocker: MockFixture):
    process_result = mocker.stub('subprocess_return')
    process_result.stdout = bytes(protocol_output, 'utf-8')
    mocker.patch('subprocess.run', return_value=process_result)
    assert dpi.load_protocols() == protocols


@pytest.mark.parametrize('search', [None, ''])
def test_index_applications(mock_load, search):
    assert dpi.list_applications(search) == {
        'data': [
            {
                'id': 133,
                'name': 'netify.netflix',
                'type': 'application',
                'category': {
                    'name': 'unknown'
                }
            },
            {
                'id': 10119,
                'name': 'netify.linkedin',
                'type': 'application',
                'category': {
                    'name': 'unknown'
                }
            },
            {
                'id': 10552,
                'name': 'netify.tesla',
                'type': 'application',
                'category': {
                    'name': 'first-category'
                }
            },
            {
                'id': 10195,
                'name': 'netify.avira',
                'type': 'application',
                'category': {
                    'name': 'unknown'
                }
            },
            {
                'id': 10194,
                'name': 'netify.sophos',
                'type': 'application',
                'category': {
                    'name': 'first-category'
                }
            },
            {
                'id': 10244,
                'name': 'netify.bbc',
                'type': 'application',
                'category': {
                    'name': 'unknown'
                }
            },
            {
                'id': 10362,
                'name': 'netify.hulu',
                'type': 'application',
                'category': {
                    'name': 'first-category'
                }
            },
            {
                'id': 10118,
                'name': 'netify.lets-encrypt',
                'type': 'application'
            },
            {
                'id': 199,
                'name': 'netify.snapchat',
                'type': 'application',
                'category': {
                    'name': 'last'
                }
            },
            {
                'id': 116,
                'name': 'Warcraft3',
                'type': 'protocol',
                'category': {
                    'name': 'games'
                }
            },
            {
                'id': 117,
                'name': 'LotusNotes',
                'type': 'protocol'
            },
            {
                'id': 121,
                'name': 'Dropbox',
                'type': 'protocol',
                'category': {
                    'name': 'base'
                }
            },
            {
                'id': 127,
                'name': 'RPC',
                'type': 'protocol',
                'category': {
                    'name': 'base'
                }
            },
            {
                'id': 128,
                'name': 'NetFlow',
                'type': 'protocol',
                'category': {
                    'name': 'base'
                }
            },
            {
                'id': 129,
                'name': 'SFlow',
                'type': 'protocol',
                'category': {
                    'name': 'low'
                }
            },
            {
                'id': 130,
                'name': 'HTTP/Connect',
                'type': 'protocol',
                'category': {
                    'name': 'low'
                }
            }
        ],
        'meta': {
            'last_page': 1,
            'total': 16
        }
    }


def test_index_applications_search(mock_load):
    assert dpi.list_applications(search='l') == {
        'data': [
            {
                'id': 133,
                'name': 'netify.netflix',
                'type': 'application',
                'category': {
                    'name': 'unknown'
                }
            },
            {
                'id': 10119,
                'name': 'netify.linkedin',
                'type': 'application',
                'category': {
                    'name': 'unknown'
                }
            },
            {
                'id': 10552,
                'name': 'netify.tesla',
                'type': 'application',
                'category': {
                    'name': 'first-category'
                }
            },
            {
                'id': 10362,
                'name': 'netify.hulu',
                'type': 'application',
                'category': {
                    'name': 'first-category'
                }
            },
            {
                'id': 10118,
                'name': 'netify.lets-encrypt',
                'type': 'application'
            },
            {
                'id': 199,
                'name': 'netify.snapchat',
                'type': 'application',
                'category': {
                    'name': 'last'
                }
            },
            {
                'id': 117,
                'name': 'LotusNotes',
                'type': 'protocol'
            },
            {
                'id': 128,
                'name': 'NetFlow',
                'type': 'protocol',
                'category': {
                    'name': 'base'
                }
            },
            {
                'id': 129,
                'name': 'SFlow',
                'type': 'protocol',
                'category': {
                    'name': 'low'
                }
            },
            {
                'id': 130,
                'name': 'HTTP/Connect',
                'type': 'protocol',
                'category': {
                    'name': 'low'
                }
            }
        ],
        'meta': {
            'last_page': 1,
            'total': 10
        }
    }


def test_index_applications_paginate(mock_load):
    assert dpi.list_applications(limit=2, page=2) == {
        'data': [
            {
                'id': 10552,
                'name': 'netify.tesla',
                'type': 'application',
                'category': {
                    'name': 'first-category'
                }
            },
            {
                'id': 10195,
                'name': 'netify.avira',
                'type': 'application',
                'category': {
                    'name': 'unknown'
                }
            }
        ],
        'meta': {
            'last_page': 8,
            'total': 16
        }
    }
    assert dpi.list_applications(limit=2, page=3) == {
        'data': [
            {
                'id': 10194,
                'name': 'netify.sophos',
                'type': 'application',
                'category': {
                    'name': 'first-category'
                }
            },
            {
                'id': 10244,
                'name': 'netify.bbc',
                'type': 'application',
                'category': {
                    'name': 'unknown'
                }
            }
        ],
        'meta': {
            'last_page': 8,
            'total': 16
        }
    }


# application groups

category_output = """
     1: application: adult
     5: application: cybersecurity
    12: application: games
     5: protocol: games
    18: protocol: web
"""

categories = {
    'application': {1: 'adult', 5: 'cybersecurity', 12: 'games'},
    'protocol': {5: 'games', 18: 'web'}
}


@pytest.fixture
def mock_vocabularies(mocker):
    """Every member kind resolves against the engine, the catalogs are never reached."""
    mocker.patch('nethsec.dpi.load_applications', return_value=applications)
    mocker.patch('nethsec.dpi.load_protocols', return_value=protocols)
    mocker.patch('nethsec.dpi.load_categories', return_value=categories)


@pytest.fixture
def e_uci_appgroups(e_uci_with_data, mock_vocabularies):
    return e_uci_with_data


def test_load_categories(mocker: MockFixture):
    process_result = mocker.stub('subprocess_return')
    process_result.stdout = bytes(category_output, 'utf-8')
    mocker.patch('subprocess.run', return_value=process_result)
    assert dpi.load_categories() == categories


def test_add_appgroup(e_uci_appgroups):
    group_id = dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'], ['cybersecurity'],
                                ['Dropbox'], ['web'])
    assert e_uci_appgroups.get('dpi', group_id) == 'appgroup'
    assert e_uci_appgroups.get('dpi', group_id, 'ns_name') == 'Group one'
    assert e_uci_appgroups.get('dpi', group_id, 'app', list=True) == ('netify.netflix',)
    assert e_uci_appgroups.get('dpi', group_id, 'app_category', list=True) == ('cybersecurity',)
    assert e_uci_appgroups.get('dpi', group_id, 'proto', list=True) == ('Dropbox',)
    assert e_uci_appgroups.get('dpi', group_id, 'proto_category', list=True) == ('web',)


def test_add_appgroup_strips_and_deduplicates(e_uci_appgroups):
    group_id = dpi.add_appgroup(e_uci_appgroups, '  Group one  ',
                                [' netify.netflix ', 'netify.netflix', 'NETIFY.NETFLIX'], [], [], [])
    assert e_uci_appgroups.get('dpi', group_id, 'ns_name') == 'Group one'
    assert e_uci_appgroups.get('dpi', group_id, 'app', list=True) == ('netify.netflix',)


def test_add_appgroup_with_one_kind_only(e_uci_appgroups):
    group_id = dpi.add_appgroup(e_uci_appgroups, 'Only protocols', protocols=['HTTP/Connect'])
    assert e_uci_appgroups.get('dpi', group_id, 'proto', list=True) == ('HTTP/Connect',)
    assert e_uci_appgroups.get('dpi', group_id, 'app', default=None) is None


def test_add_appgroup_requires_a_name(e_uci_appgroups):
    with pytest.raises(ValidationError) as err:
        dpi.add_appgroup(e_uci_appgroups, '   ', ['netify.netflix'])
    assert err.value.args[0] == 'name'
    assert err.value.args[1] == 'name_required'


def test_add_appgroup_refuses_a_long_name(e_uci_appgroups):
    with pytest.raises(ValidationError) as err:
        dpi.add_appgroup(e_uci_appgroups, 'x' * 65, ['netify.netflix'])
    assert err.value.args[1] == 'name_too_long'


def test_add_appgroup_refuses_a_duplicated_name(e_uci_appgroups):
    dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'])
    with pytest.raises(ValidationError) as err:
        dpi.add_appgroup(e_uci_appgroups, 'group ONE', ['netify.tesla'])
    assert err.value.args[1] == 'name_already_exists'


def test_add_appgroup_refuses_an_empty_group(e_uci_appgroups):
    with pytest.raises(ValidationError) as err:
        dpi.add_appgroup(e_uci_appgroups, 'Empty', [], [], [], [])
    assert err.value.args[0] == 'members'
    assert err.value.args[1] == 'appgroup_is_empty'


@pytest.mark.parametrize('value', ["netify.netflix'", 'netify.netflix;', 'netify.(netflix)',
                                   'netify.netflix\\', 'netify\nnetify.netflix', '   '])
def test_add_appgroup_refuses_expression_breaking_members(e_uci_appgroups, value):
    with pytest.raises(ValidationError) as err:
        dpi.add_appgroup(e_uci_appgroups, 'Group one', [value])
    assert err.value.args[0] == 'applications'
    assert err.value.args[1] == 'invalid_application'


def test_add_appgroup_refuses_unknown_members(e_uci_appgroups):
    with pytest.raises(ValidationError) as err:
        dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.nonexistent'])
    assert err.value.args[1] == 'invalid_application'
    with pytest.raises(ValidationError) as err:
        dpi.add_appgroup(e_uci_appgroups, 'Group one', protocols=['nonexistent'])
    assert err.value.args[1] == 'invalid_protocol'
    with pytest.raises(ValidationError) as err:
        dpi.add_appgroup(e_uci_appgroups, 'Group one', application_categories=['web'])
    assert err.value.args[1] == 'invalid_application_category'
    with pytest.raises(ValidationError) as err:
        dpi.add_appgroup(e_uci_appgroups, 'Group one', protocol_categories=['cybersecurity'])
    assert err.value.args[1] == 'invalid_protocol_category'


def test_add_appgroup_refuses_a_protocol_named_by_its_catalog_tag(e_uci_appgroups):
    # the catalog calls it "http-connect", but only the name the engine reports can be matched
    with pytest.raises(ValidationError) as err:
        dpi.add_appgroup(e_uci_appgroups, 'Group one', protocols=['http-connect'])
    assert err.value.args[1] == 'invalid_protocol'


def test_add_appgroup_matches_members_case_insensitively(e_uci_appgroups):
    group_id = dpi.add_appgroup(e_uci_appgroups, 'Group one', protocols=['http/connect'])
    assert e_uci_appgroups.get('dpi', group_id, 'proto', list=True) == ('http/connect',)


def test_add_appgroup_skips_validation_without_a_vocabulary(e_uci_with_data, mocker):
    mocker.patch('nethsec.dpi.load_applications', side_effect=FileNotFoundError)
    mocker.patch('nethsec.dpi.__load_catalog_tags', side_effect=FileNotFoundError)
    group_id = dpi.add_appgroup(e_uci_with_data, 'Group one', ['netify.unknown-to-everything'])
    assert e_uci_with_data.get('dpi', group_id, 'app', list=True) == ('netify.unknown-to-everything',)


def test_edit_appgroup(e_uci_appgroups):
    group_id = dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'], ['cybersecurity'])
    dpi.edit_appgroup(e_uci_appgroups, group_id, 'Group two', ['netify.tesla'])
    assert e_uci_appgroups.get('dpi', group_id, 'ns_name') == 'Group two'
    assert e_uci_appgroups.get('dpi', group_id, 'app', list=True) == ('netify.tesla',)
    # an emptied list is removed, not stored empty
    assert e_uci_appgroups.get('dpi', group_id, 'app_category', default=None) is None


def test_edit_appgroup_keeps_its_own_name(e_uci_appgroups):
    group_id = dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'])
    dpi.edit_appgroup(e_uci_appgroups, group_id, 'Group one', ['netify.tesla'])
    assert e_uci_appgroups.get('dpi', group_id, 'app', list=True) == ('netify.tesla',)


def test_edit_appgroup_of_unknown_id(e_uci_appgroups):
    with pytest.raises(ValidationError) as err:
        dpi.edit_appgroup(e_uci_appgroups, 'ns_nonexistent', 'Group one', ['netify.netflix'])
    assert err.value.args[1] == 'appgroup_does_not_exists'


def test_edit_appgroup_refuses_a_rule_id(e_uci_appgroups):
    with pytest.raises(ValidationError) as err:
        dpi.edit_appgroup(e_uci_appgroups, 'rule0', 'Group one', ['netify.netflix'])
    assert err.value.args[1] == 'appgroup_does_not_exists'


def test_delete_appgroup(e_uci_appgroups):
    group_id = dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'])
    dpi.delete_appgroup(e_uci_appgroups, group_id)
    assert e_uci_appgroups.get('dpi', group_id, default=None) is None


def test_add_appgroup_leaves_the_change_pending(e_uci_appgroups, mock_apply):
    dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'])
    mock_apply.assert_not_called()


def test_delete_appgroup_leaves_the_change_pending(e_uci_appgroups, mock_apply):
    group_id = dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'])
    mock_apply.reset_mock()
    dpi.delete_appgroup(e_uci_appgroups, group_id)
    mock_apply.assert_not_called()


def test_delete_appgroup_of_unknown_id(e_uci_appgroups):
    with pytest.raises(ValidationError) as err:
        dpi.delete_appgroup(e_uci_appgroups, 'ns_nonexistent')
    assert err.value.args[1] == 'appgroup_does_not_exists'


def test_delete_appgroup_in_use(e_uci_appgroups):
    group_id = dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'])
    e_uci_appgroups.set('dpi', 'rule0', 'appgroup', [group_id])
    with pytest.raises(ValidationError) as err:
        dpi.delete_appgroup(e_uci_appgroups, group_id)
    assert err.value.args[1] == 'appgroup_is_used'
    assert err.value.args[2] == ['dpi/rule0']


def test_is_used_appgroup(e_uci_appgroups):
    group_id = dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'])
    assert dpi.is_used_appgroup(e_uci_appgroups, group_id) == (False, [])
    e_uci_appgroups.set('dpi', 'rule0', 'appgroup', [group_id])
    e_uci_appgroups.set('dpi', 'rule1', 'appgroup', [group_id])
    used, matches = dpi.is_used_appgroup(e_uci_appgroups, group_id)
    assert used
    assert sorted(matches) == ['dpi/rule0', 'dpi/rule1']


def test_list_appgroups(e_uci_appgroups):
    group_id = dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'], ['cybersecurity'],
                                ['Dropbox'], ['web'])
    assert dpi.list_appgroups(e_uci_appgroups) == {
        'data': [
            {
                'id': group_id,
                'name': 'Group one',
                'applications': ['netify.netflix'],
                'application_categories': ['cybersecurity'],
                'protocols': ['Dropbox'],
                'protocol_categories': ['web'],
                'used': False,
                'matches': []
            }
        ],
        'meta': {
            'last_page': 1,
            'total': 1
        }
    }


def test_list_appgroups_when_empty(e_uci_appgroups):
    assert dpi.list_appgroups(e_uci_appgroups) == {'data': [], 'meta': {'last_page': 1, 'total': 0}}


def test_list_appgroups_is_ordered_by_name(e_uci_appgroups):
    dpi.add_appgroup(e_uci_appgroups, 'zeta', ['netify.netflix'])
    dpi.add_appgroup(e_uci_appgroups, 'Alpha', ['netify.tesla'])
    assert [group['name'] for group in dpi.list_appgroups(e_uci_appgroups)['data']] == ['Alpha', 'zeta']


def test_list_appgroups_pagination(e_uci_appgroups):
    for index in range(5):
        dpi.add_appgroup(e_uci_appgroups, f'Group {index}', ['netify.netflix'])
    result = dpi.list_appgroups(e_uci_appgroups, limit=2, page=2)
    assert [group['name'] for group in result['data']] == ['Group 2', 'Group 3']
    assert result['meta'] == {'last_page': 3, 'total': 5}


def test_list_appgroups_search(e_uci_appgroups):
    dpi.add_appgroup(e_uci_appgroups, 'Streaming', ['netify.netflix'])
    dpi.add_appgroup(e_uci_appgroups, 'Business', ['netify.tesla'])
    result = dpi.list_appgroups(e_uci_appgroups, search='STREAM')
    assert [group['name'] for group in result['data']] == ['Streaming']
    assert result['meta'] == {'last_page': 1, 'total': 1}


def test_list_appgroups_reports_usage(e_uci_appgroups):
    group_id = dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'])
    e_uci_appgroups.set('dpi', 'rule0', 'appgroup', [group_id])
    group = dpi.list_appgroups(e_uci_appgroups)['data'][0]
    assert group['used']
    assert group['matches'] == ['dpi/rule0']


def test_expand_appgroups(e_uci_appgroups):
    group_id = dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'], ['cybersecurity'],
                                ['HTTP/Connect'], ['web'])
    assert dpi.expand_appgroups(e_uci_appgroups, [group_id]) == (
        "(app == 'netify.netflix' || app_category == 'cybersecurity'"
        " || proto == 'http/connect' || proto_category == 'web')"
    )


def test_expand_appgroups_merges_and_deduplicates(e_uci_appgroups):
    first = dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'], [], ['Dropbox'])
    second = dpi.add_appgroup(e_uci_appgroups, 'Group two', ['netify.netflix', 'netify.tesla'])
    assert dpi.expand_appgroups(e_uci_appgroups, [first, second]) == (
        "(app == 'netify.netflix' || app == 'netify.tesla' || proto == 'dropbox')"
    )


def test_expand_appgroups_skips_unknown_groups(e_uci_appgroups):
    group_id = dpi.add_appgroup(e_uci_appgroups, 'Group one', ['netify.netflix'])
    assert dpi.expand_appgroups(e_uci_appgroups, [group_id, 'ns_nonexistent', 'rule0']) == (
        "(app == 'netify.netflix')"
    )


def test_expand_appgroups_without_groups(e_uci_appgroups):
    assert dpi.expand_appgroups(e_uci_appgroups, []) == ''


# rules

@pytest.fixture
def e_uci_rules(e_uci, mock_vocabularies):
    """A clean dpi config with one application group to build rules on."""
    with pathlib.Path(e_uci.confdir()).joinpath('dpi').open('w') as fp:
        fp.write(dpi_minimal_db)
    return e_uci


def group_of(e_uci, name='Group one'):
    return dpi.add_appgroup(e_uci, name, ['netify.netflix'])


def test_list_rules_when_empty(e_uci_rules):
    assert dpi.list_rules(e_uci_rules) == []


def test_add_rule(e_uci_rules):
    group = group_of(e_uci_rules)
    rule_id = dpi.add_rule(e_uci_rules, 'Block streaming', True, 'block', ['192.168.1.0/24'], [group])
    assert e_uci_rules.get('dpi', rule_id) == 'rule'
    assert e_uci_rules.get('dpi', rule_id, 'ns_name') == 'Block streaming'
    assert e_uci_rules.get('dpi', rule_id, 'ns_managed') == '1'
    assert e_uci_rules.get('dpi', rule_id, 'enabled') == '1'
    assert e_uci_rules.get('dpi', rule_id, 'action') == 'block'
    assert e_uci_rules.get('dpi', rule_id, 'priority') == '1'
    assert e_uci_rules.get('dpi', rule_id, 'source', list=True) == ('192.168.1.0/24',)
    assert e_uci_rules.get('dpi', rule_id, 'appgroup', list=True) == (group,)


def test_add_rule_without_source(e_uci_rules):
    group = group_of(e_uci_rules)
    rule_id = dpi.add_rule(e_uci_rules, 'Block everywhere', True, 'block', [], [group])
    assert e_uci_rules.get('dpi', rule_id, 'source', default=None) is None


def test_add_rule_enables_the_engine(e_uci_rules):
    group = group_of(e_uci_rules)
    dpi.add_rule(e_uci_rules, 'Block streaming', True, 'block', [], [group])
    assert e_uci_rules.get('dpi', 'config', 'enabled') == '1'


def test_add_rule_at_the_top(e_uci_rules):
    group = group_of(e_uci_rules)
    first = dpi.add_rule(e_uci_rules, 'First', True, 'block', [], [group])
    second = dpi.add_rule(e_uci_rules, 'Second', True, 'allow', [], [group], position='top')
    assert [rule['id'] for rule in dpi.list_rules(e_uci_rules)] == [second, first]
    assert e_uci_rules.get('dpi', second, 'priority') == '1'
    assert e_uci_rules.get('dpi', first, 'priority') == '2'


def test_add_rule_requires_a_group(e_uci_rules):
    with pytest.raises(ValidationError) as err:
        dpi.add_rule(e_uci_rules, 'No match', True, 'block', ['192.168.1.1'], [])
    assert err.value.args[0] == 'appgroups'
    assert err.value.args[1] == 'appgroups_required'


def test_add_rule_refuses_an_unknown_group(e_uci_rules):
    with pytest.raises(ValidationError) as err:
        dpi.add_rule(e_uci_rules, 'Bad group', True, 'block', [], ['ns_nonexistent'])
    assert err.value.args[1] == 'appgroup_does_not_exists'


def test_add_rule_refuses_an_unknown_action(e_uci_rules):
    group = group_of(e_uci_rules)
    with pytest.raises(ValidationError) as err:
        dpi.add_rule(e_uci_rules, 'Bad action', True, 'bulk', [], [group])
    assert err.value.args[0] == 'action'
    assert err.value.args[1] == 'invalid_action'


def test_add_rule_requires_a_name(e_uci_rules):
    group = group_of(e_uci_rules)
    with pytest.raises(ValidationError) as err:
        dpi.add_rule(e_uci_rules, '  ', True, 'block', [], [group])
    assert err.value.args[1] == 'name_required'


@pytest.mark.parametrize('source', ['192.168.1.1', '192.168.1.0/24', '192.168.1.10-192.168.1.20',
                                    '2001:db8::1', '2001:db8::/64'])
def test_add_rule_accepts_every_source_shape(e_uci_rules, source):
    group = group_of(e_uci_rules)
    rule_id = dpi.add_rule(e_uci_rules, f'Rule {source}', True, 'block', [source], [group])
    assert e_uci_rules.get('dpi', rule_id, 'source', list=True) == (source,)


@pytest.mark.parametrize('source', ['not-an-ip', '192.168.1.300', '192.168.1.20-192.168.1.10',
                                    '192.168.1.1-2001:db8::1', ''])
def test_add_rule_refuses_an_invalid_source(e_uci_rules, source):
    group = group_of(e_uci_rules)
    with pytest.raises(ValidationError) as err:
        dpi.add_rule(e_uci_rules, 'Bad source', True, 'block', [source], [group])
    assert err.value.args[0] == 'source'
    assert err.value.args[1] == 'invalid_source'


def test_edit_rule(e_uci_rules):
    group = group_of(e_uci_rules)
    other = group_of(e_uci_rules, 'Group two')
    rule_id = dpi.add_rule(e_uci_rules, 'Block streaming', True, 'block', ['192.168.1.1'], [group])
    dpi.edit_rule(e_uci_rules, rule_id, 'Allow streaming', False, 'allow', [], [other])
    assert e_uci_rules.get('dpi', rule_id, 'ns_name') == 'Allow streaming'
    assert e_uci_rules.get('dpi', rule_id, 'enabled') == '0'
    assert e_uci_rules.get('dpi', rule_id, 'action') == 'allow'
    assert e_uci_rules.get('dpi', rule_id, 'appgroup', list=True) == (other,)
    # an emptied source is removed, the rule matches every host again
    assert e_uci_rules.get('dpi', rule_id, 'source', default=None) is None


def test_edit_rule_keeps_the_priority(e_uci_rules):
    group = group_of(e_uci_rules)
    first = dpi.add_rule(e_uci_rules, 'First', True, 'block', [], [group])
    second = dpi.add_rule(e_uci_rules, 'Second', True, 'block', [], [group])
    dpi.edit_rule(e_uci_rules, first, 'First edited', True, 'block', [], [group])
    assert [rule['id'] for rule in dpi.list_rules(e_uci_rules)] == [first, second]


def test_edit_rule_of_unknown_id(e_uci_rules):
    group = group_of(e_uci_rules)
    with pytest.raises(ValidationError) as err:
        dpi.edit_rule(e_uci_rules, 'ns_nonexistent', 'Rule', True, 'block', [], [group])
    assert err.value.args[1] == 'rule_not_found'


def test_edit_rule_refuses_an_unmanaged_rule(e_uci_with_data, mock_vocabularies):
    group = dpi.add_appgroup(e_uci_with_data, 'Group one', ['netify.netflix'])
    with pytest.raises(ValidationError) as err:
        dpi.edit_rule(e_uci_with_data, 'rule0', 'Rule', True, 'block', [], [group])
    assert err.value.args[1] == 'rule_not_managed'


def test_delete_rule_closes_the_gap(e_uci_rules):
    group = group_of(e_uci_rules)
    first = dpi.add_rule(e_uci_rules, 'First', True, 'block', [], [group])
    second = dpi.add_rule(e_uci_rules, 'Second', True, 'block', [], [group])
    third = dpi.add_rule(e_uci_rules, 'Third', True, 'block', [], [group])
    dpi.delete_rule(e_uci_rules, second)
    assert e_uci_rules.get('dpi', first, 'priority') == '1'
    assert e_uci_rules.get('dpi', third, 'priority') == '2'


def test_add_rule_leaves_the_change_pending(e_uci_rules, mock_apply):
    group = group_of(e_uci_rules)
    mock_apply.reset_mock()
    dpi.add_rule(e_uci_rules, 'Block streaming', True, 'block', [], [group])
    mock_apply.assert_not_called()


def test_delete_rule_leaves_the_change_pending(e_uci_rules, mock_apply):
    group = group_of(e_uci_rules)
    rule_id = dpi.add_rule(e_uci_rules, 'Block streaming', True, 'block', [], [group])
    mock_apply.reset_mock()
    dpi.delete_rule(e_uci_rules, rule_id)
    mock_apply.assert_not_called()


def test_delete_rule_of_unknown_id(e_uci_rules):
    with pytest.raises(ValidationError) as err:
        dpi.delete_rule(e_uci_rules, 'ns_nonexistent')
    assert err.value.args[1] == 'rule_not_found'


def test_delete_last_enabled_rule_disables_the_engine(e_uci_rules):
    group = group_of(e_uci_rules)
    rule_id = dpi.add_rule(e_uci_rules, 'Only one', True, 'block', [], [group])
    dpi.delete_rule(e_uci_rules, rule_id)
    assert e_uci_rules.get('dpi', 'config', 'enabled') == '0'


def test_rename_and_toggle_rule(e_uci_rules):
    group = group_of(e_uci_rules)
    rule_id = dpi.add_rule(e_uci_rules, 'Block streaming', True, 'block', [], [group])
    dpi.rename_rule(e_uci_rules, rule_id, 'Renamed')
    assert e_uci_rules.get('dpi', rule_id, 'ns_name') == 'Renamed'
    dpi.disable_rule(e_uci_rules, rule_id)
    assert e_uci_rules.get('dpi', rule_id, 'enabled') == '0'
    assert e_uci_rules.get('dpi', 'config', 'enabled') == '0'
    dpi.enable_rule(e_uci_rules, rule_id)
    assert e_uci_rules.get('dpi', rule_id, 'enabled') == '1'
    assert e_uci_rules.get('dpi', 'config', 'enabled') == '1'


def test_rename_and_toggle_work_on_unmanaged_rules(e_uci_with_data):
    dpi.rename_rule(e_uci_with_data, 'rule0', 'Migrated rule')
    assert e_uci_with_data.get('dpi', 'rule0', 'ns_name') == 'Migrated rule'
    dpi.disable_rule(e_uci_with_data, 'rule0')
    assert e_uci_with_data.get('dpi', 'rule0', 'enabled') == '0'


def test_order_rules(e_uci_rules):
    group = group_of(e_uci_rules)
    first = dpi.add_rule(e_uci_rules, 'First', True, 'block', [], [group])
    second = dpi.add_rule(e_uci_rules, 'Second', True, 'block', [], [group])
    third = dpi.add_rule(e_uci_rules, 'Third', True, 'block', [], [group])
    dpi.order_rules(e_uci_rules, [third, first, second])
    assert [rule['id'] for rule in dpi.list_rules(e_uci_rules)] == [third, first, second]
    assert e_uci_rules.get('dpi', third, 'priority') == '1'


def test_order_rules_refuses_a_partial_order(e_uci_rules):
    group = group_of(e_uci_rules)
    first = dpi.add_rule(e_uci_rules, 'First', True, 'block', [], [group])
    dpi.add_rule(e_uci_rules, 'Second', True, 'block', [], [group])
    with pytest.raises(ValidationError) as err:
        dpi.order_rules(e_uci_rules, [first])
    assert err.value.args[1] == 'invalid_order'


def test_order_rules_refuses_an_unknown_rule(e_uci_rules):
    group = group_of(e_uci_rules)
    first = dpi.add_rule(e_uci_rules, 'First', True, 'block', [], [group])
    with pytest.raises(ValidationError) as err:
        dpi.order_rules(e_uci_rules, [first, 'ns_nonexistent'])
    assert err.value.args[1] == 'rule_not_found'


def test_list_rules(e_uci_rules):
    group = group_of(e_uci_rules)
    rule_id = dpi.add_rule(e_uci_rules, 'Block streaming', True, 'block', ['192.168.1.0/24'], [group])
    assert dpi.list_rules(e_uci_rules) == [
        {
            'id': rule_id,
            'name': 'Block streaming',
            'enabled': True,
            'action': 'block',
            'source': ['192.168.1.0/24'],
            'appgroups': [{'id': group, 'name': 'Group one'}],
            'managed': True,
            'index': 0
        }
    ]


def test_list_rules_reports_unmanaged_rules(e_uci_with_data):
    rules = {rule['id']: rule for rule in dpi.list_rules(e_uci_with_data)}
    assert rules['rule0']['managed'] is False
    assert rules['rule2']['criteria'] == 'local_ip == 192.168.100.22 && application == "netify.facebook";'
    assert 'criteria' not in rules['rule3']


def test_list_rules_hides_invisible_ones(e_uci_rules):
    group = group_of(e_uci_rules)
    rule_id = dpi.add_rule(e_uci_rules, 'Hidden', True, 'block', [], [group])
    e_uci_rules.set('dpi', rule_id, 'ns_visible', '0')
    assert dpi.list_rules(e_uci_rules) == []


def test_list_rules_is_complete_and_indexed(e_uci_rules):
    group = group_of(e_uci_rules)
    for index in range(5):
        dpi.add_rule(e_uci_rules, f'Rule {index}', True, 'block', [], [group])
    rules = dpi.list_rules(e_uci_rules)
    assert [rule['name'] for rule in rules] == ['Rule 0', 'Rule 1', 'Rule 2', 'Rule 3', 'Rule 4']
    assert [rule['index'] for rule in rules] == [0, 1, 2, 3, 4]


def test_expand_source():
    assert dpi.expand_source(['192.168.1.1', '192.168.1.0/24']) == ['192.168.1.1', '192.168.1.0/24']
    assert dpi.expand_source(['192.168.1.10-192.168.1.11']) == ['192.168.1.10/31']
    assert dpi.expand_source(['192.168.1.1-192.168.1.4']) == ['192.168.1.1/32', '192.168.1.2/31',
                                                              '192.168.1.4/32']
    assert dpi.expand_source(['10.0.0.1-10.0.0.2']) == ['10.0.0.1/32', '10.0.0.2/32']


def test_build_rule_criteria(e_uci_rules):
    group = group_of(e_uci_rules)
    rule_id = dpi.add_rule(e_uci_rules, 'Block streaming', True, 'block',
                           ['192.168.1.0/24', '10.0.0.1-10.0.0.2'], [group])
    rule = e_uci_rules.get_all('dpi', rule_id)
    assert dpi.build_rule_criteria(e_uci_rules, rule) == (
        "(local_ip == 192.168.1.0/24 || local_ip == 10.0.0.1/32 || local_ip == 10.0.0.2/32)"
        " && (app == 'netify.netflix');"
    )


def test_build_rule_criteria_without_source(e_uci_rules):
    group = group_of(e_uci_rules)
    rule_id = dpi.add_rule(e_uci_rules, 'Block streaming', True, 'block', [], [group])
    rule = e_uci_rules.get_all('dpi', rule_id)
    assert dpi.build_rule_criteria(e_uci_rules, rule) == "(app == 'netify.netflix');"


def test_build_rule_criteria_of_a_rule_matching_nothing(e_uci_rules):
    assert dpi.build_rule_criteria(e_uci_rules, {'source': ['192.168.1.1']}) == ''


def test_build_rule_criteria_source_only_when_appgroup_not_required(e_uci_rules):
    rule = {'source': ['192.168.1.1', '192.168.1.0/24']}
    assert dpi.build_rule_criteria(e_uci_rules, rule, require_appgroup=False) == (
        '(local_ip == 192.168.1.1 || local_ip == 192.168.1.0/24);'
    )


def test_build_rule_criteria_still_empty_without_source_or_appgroup(e_uci_rules):
    assert dpi.build_rule_criteria(e_uci_rules, {}, require_appgroup=False) == ''


def test_add_rule_without_appgroup_requires_the_flag(e_uci_rules):
    with pytest.raises(ValidationError) as err:
        dpi.add_rule(e_uci_rules, 'No group', True, 'allow', ['192.168.1.1'], [])
    assert err.value.args[1] == 'appgroups_required'


def test_add_rule_source_only_via_migration_flag(e_uci_rules):
    rule_id = dpi.add_rule(e_uci_rules, 'Migrated exception 1', True, 'allow', ['192.168.1.1'], [],
                           require_appgroup=False)
    assert e_uci_rules.get('dpi', rule_id, 'ns_managed') == '1'
    assert e_uci_rules.get('dpi', rule_id, 'source', list=True) == ('192.168.1.1',)
    assert e_uci_rules.get('dpi', rule_id, 'appgroup', default=None) is None


# Migration from the schema used before application groups existed

def test_freeze_legacy_criteria_from_application_and_device(e_uci: EUci):
    rule = {'device': 'eth0', 'application': ['netify.amazon-prime', 'netify.netflix']}
    assert dpi.freeze_legacy_criteria(e_uci, rule) == (
        "(iface_nfq_src == 'eth0' or iface_nfq_dst == 'eth0') && "
        "(app == 'netify.amazon-prime' or app == 'netify.netflix') ;"
    )


def test_freeze_legacy_criteria_prefers_hand_written_criteria(e_uci: EUci):
    rule = {'device': 'eth0', 'criteria': 'app == "netify.netflix";', 'application': ['netify.amazon-prime']}
    assert dpi.freeze_legacy_criteria(e_uci, rule) == "app == 'netify.netflix';"


def test_freeze_legacy_criteria_applies_vlan_rewrite(e_uci: EUci):
    with pathlib.Path(e_uci.confdir()).joinpath('network').open('a') as fp:
        fp.write("""
config device
    option name 'eth0.10'
    option ifname 'eth0'
    option type '8021q'
    option vid '10'
""")
    rule = {'device': 'eth0.10', 'application': ['netify.netflix']}
    assert dpi.freeze_legacy_criteria(e_uci, rule) == (
        "vlan_id == 10 && (iface_nfq_src == 'eth0.10' or iface_nfq_dst == 'eth0.10') && "
        "(app == 'netify.netflix') ;"
    )


legacy_dpi_db = """
config main 'config'
    option log_blocked '0'
    option firewall_exemption '1'
    option enabled '0'
    list popular_filters 'netify.facebook'

config rule 'ns_b01a0e73'
    option enabled '1'
    option device 'eth0'
    option action 'block'
    list application 'netify.amazon-prime'
    list application 'netify.netflix'

config rule 'ns_qos1'
    option enabled '1'
    option device 'eth1'
    option action 'bulk'
    list application 'netify.dropbox'

config rule 'ns_empty1'
    option enabled '1'
    option device 'eth2'
    option action 'block'

config rule 'ns_perrule_exempt'
    option enabled '1'
    option device 'eth3'
    option action 'block'
    list application 'netify.tesla'
    list exemption '192.168.100.3'

config exemption 'ns_2127b876'
    option enabled '1'
    option criteria '192.168.122.47'
    option description 'my exception'

config exemption 'ns_disabled_exempt'
    option enabled '0'
    option criteria '10.0.0.5'
    option description 'disabled one'

config exemption 'ns_bad_exempt'
    option enabled '1'
    option criteria 'not-an-address'
    option description ''
"""


@pytest.fixture
def e_uci_legacy(e_uci: EUci):
    with pathlib.Path(e_uci.confdir()).joinpath('dpi').open('w') as fp:
        fp.write(legacy_dpi_db)
    return e_uci


def test_migrate_schema_noop_when_nothing_to_migrate(e_uci, mock_apply):
    assert dpi.migrate_schema(e_uci) is False
    mock_apply.assert_not_called()


def test_migrate_schema_freezes_legacy_rule(e_uci_legacy):
    assert dpi.migrate_schema(e_uci_legacy) is True
    rule = e_uci_legacy.get_all('dpi', 'ns_b01a0e73')
    assert rule['criteria'] == (
        "(iface_nfq_src == 'eth0' or iface_nfq_dst == 'eth0') && "
        "(app == 'netify.amazon-prime' or app == 'netify.netflix') ;"
    )
    assert 'device' not in rule
    assert 'application' not in rule
    assert 'ns_managed' not in rule
    assert rule['action'] == 'block'
    assert 'priority' in rule


def test_migrate_schema_names_migrated_rules_and_exemptions_in_order(e_uci_legacy):
    dpi.migrate_schema(e_uci_legacy)
    assert e_uci_legacy.get('dpi', 'ns_b01a0e73', 'ns_name') == 'Migrated rule 1'
    # ns_qos1 is dropped (QoS), ns_empty1 is dropped (matches nothing): ns_perrule_exempt is next
    perrule_ids = [s for s, r in utils.get_all_by_type(e_uci_legacy, 'dpi', 'rule').items()
                   if r.get('ns_name') == 'Migrated rule 2']
    assert len(perrule_ids) == 1


def test_migrate_schema_drops_qos_rule(e_uci_legacy):
    dpi.migrate_schema(e_uci_legacy)
    assert e_uci_legacy.get('dpi', 'ns_qos1', default=None) is None


def test_migrate_schema_drops_rule_matching_nothing(e_uci_legacy):
    dpi.migrate_schema(e_uci_legacy)
    assert e_uci_legacy.get('dpi', 'ns_empty1', default=None) is None


def test_migrate_schema_drops_per_rule_exemption_but_keeps_the_rule(e_uci_legacy):
    dpi.migrate_schema(e_uci_legacy)
    rule = e_uci_legacy.get_all('dpi', 'ns_perrule_exempt')
    assert 'exemption' not in rule
    assert rule['action'] == 'block'
    assert 'criteria' in rule


def test_migrate_schema_converts_address_exemption_to_managed_allow_rule(e_uci_legacy):
    dpi.migrate_schema(e_uci_legacy)
    rules = dpi.list_rules(e_uci_legacy)
    exception1 = next(r for r in rules if r['name'] == 'Migrated exception 1')
    assert exception1['managed'] is True
    assert exception1['action'] == 'allow'
    assert exception1['source'] == ['192.168.122.47']
    assert exception1['appgroups'] == []
    assert exception1['enabled'] is True


def test_migrate_schema_keeps_a_disabled_exemption_disabled(e_uci_legacy):
    dpi.migrate_schema(e_uci_legacy)
    rules = dpi.list_rules(e_uci_legacy)
    exception2 = next(r for r in rules if r['name'] == 'Migrated exception 2')
    assert exception2['enabled'] is False


def test_migrate_schema_converts_non_address_exemption_to_unmanaged_allow_rule(e_uci_legacy):
    dpi.migrate_schema(e_uci_legacy)
    rules = dpi.list_rules(e_uci_legacy)
    exception3 = next(r for r in rules if r['name'] == 'Migrated exception 3')
    assert exception3['managed'] is False
    assert exception3['action'] == 'allow'
    assert exception3.get('criteria') == 'not-an-address;'


def test_migrate_schema_converts_object_exemption_via_expanded_addresses(e_uci, mocker):
    with pathlib.Path(e_uci.confdir()).joinpath('dpi').open('w') as fp:
        fp.write("""
config main 'config'
    option enabled '0'

config exemption 'ns_objex'
    option enabled '1'
    option criteria 'objects/ns_obj1'
    option description 'office subnet'
""")
    mocker.patch('nethsec.dpi.objects.is_object_id', return_value=True)
    mocker.patch('nethsec.dpi.objects.get_object_ips', return_value=['192.168.50.0/24'])
    assert dpi.migrate_schema(e_uci) is True
    rules = dpi.list_rules(e_uci)
    assert len(rules) == 1
    assert rules[0]['managed'] is True
    assert rules[0]['source'] == ['192.168.50.0/24']


def test_migrate_schema_removes_exemption_sections_and_legacy_globals(e_uci_legacy):
    dpi.migrate_schema(e_uci_legacy)
    assert utils.get_all_by_type(e_uci_legacy, 'dpi', 'exemption') == {}
    assert e_uci_legacy.get('dpi', 'config', 'firewall_exemption', default=None) is None
    assert e_uci_legacy.get('dpi', 'config', 'popular_filters', list=True, default=None) is None


def test_migrate_schema_puts_exemptions_before_migrated_rules(e_uci_legacy):
    dpi.migrate_schema(e_uci_legacy)
    rules = dpi.list_rules(e_uci_legacy)
    names_in_order = [r['name'] for r in rules]
    assert names_in_order.index('Migrated exception 1') < names_in_order.index('Migrated rule 1')


def test_migrate_schema_applies_immediately(e_uci_legacy, mock_apply):
    assert dpi.migrate_schema(e_uci_legacy) is True
    mock_apply.assert_called_with(e_uci_legacy)


def test_migrate_schema_is_idempotent(e_uci_legacy):
    dpi.migrate_schema(e_uci_legacy)
    rules_after_first_run = dpi.list_rules(e_uci_legacy)
    assert dpi.migrate_schema(e_uci_legacy) is False
    assert dpi.list_rules(e_uci_legacy) == rules_after_first_run
