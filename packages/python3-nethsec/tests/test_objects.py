import pathlib
from nethsec.utils import ValidationError
import pytest
from euci import EUci, UciExceptionNotFound
from nethsec import firewall, objects

objects_db = """
config domain 'myset'
	option name 'MySet'
	option description 'Mydomain set'
	option family 'ipv4'
	option timeout '600'
	list domain 'www.nethsecurity.org'
	list domain 'www.nethserver.org'

config host 'ns_04fadb5c'
	option name 'h1'
	option family 'ipv4'
	list ipaddr '1.2.3.4'

config host 'ns_12345'
	option name 'h1'
	option family 'ipv4'
	list ipaddr 'dhcp/ns_112233'

config host 'ns_a7439990'
	option name 'h1v6'
	option family 'ipv6'
	list ipaddr 'fd:618c:d80a:dc82:2380:54c7:7a17:1013'
"""

firewall_db = """
config rule 'r5'
    option name 'r5'
    option ns_dst 'dhcp/ns_8dcab636'

config rule 'r6'
    option name 'r6'

config rule 'r7'
    option name 'r7'
    option ns_src 'objects/ns_04fadb5c'

config rule 'r8'
    option name 'r8'

config redirect 'redirect1'
    option ns_src ''
    option ipset 'redirect1_ipset'

config ipset 'redirect1_ipset'
    option name 'redirect1_ipset'
    option match 'src_net'
    option enabled '1'
    list entry '6.7.8.9'

config redirect 'redirect2'
    option ns_src ''
"""

dhcp_db = """
config domain 'ns_8bec5896'
	option ip '7.8.9.1'
	option name 'host1'
	option ns_description 'Host 1'

config domain 'ns_112233'
	option ip '7.8.9.1'
	option name 'used_host'
	option ns_description 'Used Host'

config host 'ns_8dcab636'
	option ip '192.168.100.5'
	option mac 'fe:54:00:6a:50:bf'
	option dns '1'
	option name 'host2'
	option ns_description 'host2'

config domain 'ns_9e7f705e'
	option ip '1.2.3.4'
	option name 'test1.domain'

config host 'ns_271ca281'
	option ip '192.168.100.22'
	option mac 'fe:54:00:6a:4a:a1'
	option dns '1'
	option name 'reserve1'
	option ns_description 'reserve1'
"""

user_db = """
config user 'ns_user1'
	option name "john"
	option database "main"
	option label "John Doe"
	option openvpn_ipaddr "10.10.10.22"

config user 'ns_user2'
	option name "user2"
"""

mwan3_db = """
config rule 'ns_r1'
	option label 'r1'
	option use_policy 'ns_default'
	option sticky '0'
	option proto 'tcp'
	option src_ip '1.2.3.4'
	option dest_ip '1.1.1.1'
    option ns_src 'users/ns_user2'
"""

dpi_db = """
config rule
	option action 'block'
	list application 'netify.twitter'
	list source 'dhcp/ns_9e7f705e'
	option description 'Block Twitter for user Goofy'
	option enabled '1'

config exemption
	option criteria 'dhcp/ns_271ca281'
	option description 'Important host'
	option enabled '1'

config rule 'ns_e775b8a7'
	option enabled '1'
	option device 'br-lan'
	option action 'block'
	list application 'netify.amazon-prime'

"""

@pytest.fixture
def u(tmp_path: pathlib.Path) -> EUci:
    conf_dir = tmp_path.joinpath('conf')
    conf_dir.mkdir()
    save_dir = tmp_path.joinpath('save')
    save_dir.mkdir()
    with tmp_path.joinpath('objects').open('w') as fp:
        fp.write(objects_db)
    with tmp_path.joinpath('firewall').open('w') as fp:
        fp.write(firewall_db)
    with tmp_path.joinpath('dhcp').open('w') as fp:
        fp.write(dhcp_db)
    with tmp_path.joinpath('users').open('w') as fp:
        fp.write(user_db)
    with tmp_path.joinpath('mwan3').open('w') as fp:
        fp.write(mwan3_db)
    with tmp_path.joinpath('dpi').open('w') as fp:
        fp.write(dpi_db)
    return EUci(confdir=tmp_path.as_posix())

def test_add_doman_set(u):
    id1 = objects.add_domain_set(u, "mydomainset", "ipv4", ["test1.com", "test2.com"])
    assert u.get("objects", id1, "name") == "mydomainset"
    assert u.get("objects", id1, "family") == "ipv4"
    assert u.get_all("objects", id1, "domain") == ("test1.com", "test2.com")
    assert u.get("objects", id1, "timeout") == "660"

    linked = firewall.get_all_linked(u, f"objects/{id1}")
    assert linked['firewall'] is not None
    assert u.get('firewall', linked['firewall'][0], 'ns_link') == f"objects/{id1}"
    assert u.get('firewall', linked['firewall'][0], 'name') == "mydomainset"
    assert u.get('firewall', linked['firewall'][0], 'family') == 'ipv4'
    assert u.get('firewall', linked['firewall'][0], 'timeout') == '660'

    assert linked['dhcp'] is not None
    assert u.get('dhcp', linked['dhcp'][0], 'ns_link') == f"objects/{id1}"
    assert u.get_all('dhcp', linked['dhcp'][0], 'name') == ("mydomainset",)
    assert u.get_all('dhcp', linked['dhcp'][0], 'domain') == ("test1.com", "test2.com")

    id2 = objects.add_domain_set(u, "mydomainset2", "ipv6", ["test3.com", "test4.com"], 300)
    assert u.get("objects", id2, "name") == "mydomainset2"
    assert u.get("objects", id2, "family") == "ipv6"
    assert u.get_all("objects", id2, "domain") == ("test3.com", "test4.com")
    assert u.get("objects", id2, "timeout") == "300"
    linked = firewall.get_all_linked(u, f"objects/{id2}")
    assert u.get('firewall', linked['firewall'][0], 'name') == "mydomainset2"
    assert u.get_all('dhcp', linked['dhcp'][0], 'name') == ("mydomainset2",)

def test_edit_domain_set(u):
    id = objects.add_domain_set(u, "mydomainset3", "ipv4", ["test1.com", "test2.com"])
    objects.edit_domain_set(u, id, "mydomainset3b", "ipv6", ["test3.com", "test4.com"], 600)
    assert u.get("objects", id, "name") == "mydomainset3b"
    assert u.get("objects", id, "family") == "ipv6"
    assert u.get_all("objects", id, "domain") == ("test3.com", "test4.com")
    assert u.get("objects", id, "timeout") == "600"
    
def test_delete_domain_set(u):
    with pytest.raises(ValidationError):
        objects.delete_domain_set(u, "notpresent")
    id = objects.add_domain_set(u, "mydomainset4", "ipv4", ["test1.com", "test2.com"])
    assert objects.delete_domain_set(u, id) == id
    linked = firewall.get_all_linked(u, f"objects/{id}")
    assert linked['firewall'] == []
    assert linked['dhcp'] == []
    id = objects.add_domain_set(u, "mydomainsettd", "ipv4", ["test1.com", "test2.com"])
    u.set('firewall', 'r8', 'ns_dst', f"objects/{id}")
    with pytest.raises(ValidationError):
        objects.delete_domain_set(u, id)

def test_is_used_domain_set(u):
    id = objects.add_domain_set(u, "used1", "ipv4", ["test1.com", "test2.com"])
    u.set('firewall', 'r5', 'ns_dst', f"objects/{id}")
    used, matches = objects.is_used_domain_set(u, id)
    assert used
    assert matches == ["firewall/r5"]

def test_list_domain_sets(u):
    sets = objects.list_domain_sets(u)
    assert len(sets) == 8

def test_add_host_set(u):
    with pytest.raises(ValidationError):
        objects.add_host_set(u, "myhostset", "ipv4", ["a.b.c.d", "e.f.g.h"])
    id1 = objects.add_host_set(u, "myhostset", "ipv4", ["1.2.3.4", "4.5.6.0/24", "192.168.1.3-192.168.1.10"])
    assert u.get("objects", id1, "name") == "myhostset"
    assert u.get_all("objects", id1, "ipaddr") == ("1.2.3.4", "4.5.6.0/24", "192.168.1.3-192.168.1.10")
    assert u.get("objects", id1, "family") == "ipv4"
    id2 = objects.add_host_set(u, "myhostset2", "ipv6", ["2001:db8:3333:4444:5555:6666:7777:8888", "2001:db8::/95", "2001:db8:3333:4444:5555:6666:7777:8888-2001:db8:3333:4444:5555:6666:7777:8890"])
    assert u.get("objects", id2, "name") == "myhostset2"
    assert u.get("objects", id2, "family") == "ipv6"
    assert u.get_all("objects", id2, "ipaddr") == ("2001:db8:3333:4444:5555:6666:7777:8888", "2001:db8::/95", "2001:db8:3333:4444:5555:6666:7777:8888-2001:db8:3333:4444:5555:6666:7777:8890")

def test_edit_host_set(u):
    id = objects.add_host_set(u, "myhostset3", "ipv4", ["6.7.8.9"])
    objects.edit_host_set(u, id, "myhostset3b", "ipv4", ["1.1.1.1", "2.2.2.2"])
    assert u.get("objects", id, "name") == "myhostset3b"
    assert u.get_all("objects", id, "ipaddr") == ("1.1.1.1", "2.2.2.2")

def test_delete_host_set(u):
    with pytest.raises(ValidationError):
        objects.delete_host_set(u, "notpresent")
    id = objects.add_host_set(u, "myhostset4", "ipv4", ["6.7.8.9"])
    assert objects.delete_host_set(u, id) == id
    id = objects.add_host_set(u, "myhostsettd", "ipv4", ["2.2.2.2"])
    u.set('firewall', 'r8', 'ns_dst', f"objects/{id}")
    with pytest.raises(ValidationError):
        objects.delete_host_set(u, id)

def test_is_used_host_set(u):
    id = objects.add_host_set(u, "myhostset", "ipv4", ["1.1.1.1"])
    u.set('firewall', 'r6', 'ns_src', f"objects/{id}")
    used, matches = objects.is_used_host_set(u, id)
    assert used
    assert matches == ["firewall/r6"]

def test_list_host_sets(u):
    sets = objects.list_host_sets(u)
    assert len(sets) == 10

def test_is_singleton_host_set(u):
    id1 = objects.add_host_set(u, "myhostset", "ipv4", ["1.2.3.4", "5.6.7.8"])
    assert objects.is_singleton_host_set(u, f"objects/{id1}") == False
    id2 = objects.add_host_set(u, "myhostset2", "ipv4", ["8.8.8.8"])
    assert objects.is_singleton_host_set(u, f"objects/{id2}") == True
    id3 = objects.add_host_set(u, "myhostset3", "ipv4", ["192.168.7.2-192.168.7.3"])
    assert objects.is_singleton_host_set(u, f"objects/{id3}") == False
    id4 = objects.add_host_set(u, "myhostset4", "ipv4", ["192.168.0.0/24"])
    assert objects.is_singleton_host_set(u, f"objects/{id4}") == False
    assert objects.is_singleton_host_set(u, f"objects/{id4}", allow_cidr=True)

def test_add_host_set_loopback(u):
    id1 = objects.add_host_set(u, "myhostset", "ipv4", ["1.2.3.4"])
    id2 = objects.add_host_set(u, "myhostset2", "ipv4", [f"objects/{id1}"])
    with pytest.raises(ValidationError):
        objects.edit_host_set(u, id1, "myhostset", "ipv4", [f"objects/{id2}"])

def test_is_used_object(u):
    used, matches = objects.is_used_object(u, "dhcp/ns_8dcab636")
    assert used
    assert matches == ["firewall/r5"]
    assert objects.is_used_object(u, "dhcp/ns_8bec5896")[0] == False
    assert objects.is_used_object(u, "users/ns_user2")[0] == True
    used, matches = objects.is_used_object(u, "objects/ns_04fadb5c")
    assert used
    assert matches == ["firewall/r7"]
    used, matches = objects.is_used_object(u, "dhcp/ns_112233")
    assert used
    assert matches == ["objects/ns_12345"]

def test_object_exists(u):
    assert objects.object_exists(u, "users/ns_user1")
    assert objects.object_exists(u, "uknown") == False

def test_get_object(u):
    id = objects.add_host_set(u, "myhostset", "ipv4", ["1.2.3.4"])
    obj = objects.get_object(u, id)

def test_get_object_ips(u):
    id0 = objects.add_host_set(u, "myhostset0", "ipv4", ["4.5.6.7"])
    id = objects.add_host_set(u, "myhostset", "ipv4", ["1.2.3.4", "dhcp/ns_8bec5896", "users/ns_user1", f"objects/{id0}"])
    ips = objects.get_object_ips(u, f"objects/{id}")
    assert set(ips) == set(["1.2.3.4", "7.8.9.1", "10.10.10.22", "4.5.6.7"]) # check with set to ignore order

def test_is_domain_set(u):
    id = objects.add_domain_set(u, "mydomainset6", "ipv4", ["test1.com", "test2.com"])
    assert objects.is_domain_set(u, f"objects/{id}") == True
    assert objects.is_domain_set(u, "dhcp/ns_8dcab636") == False
    assert objects.is_domain_set(u, "users/ns_user1") == False

def test_is_domain(u):
    id = objects.add_domain_set(u, "mydomainset6", "ipv4", ["test1.com", "test2.com"])
    assert objects.is_domain(u, f"objects/{id}") == False
    assert objects.is_domain(u, "dhcp/ns_8bec5896")

def test_is_host(u):
    assert objects.is_host(u, "dhcp/ns_8bec5896") == False
    assert objects.is_host(u, "dhcp/ns_8dcab636")

def test_is_vpn_user(u):
    assert objects.is_vpn_user(u, "users/ns_user1")
    assert objects.is_vpn_user(u, "users/ns_user2") == False

def test_is_host_set(u):
    id = objects.add_host_set(u, "myhostset", "ipv4", ["1.2.3.4"])
    assert objects.is_host_set(u, f"objects/{id}")
    assert objects.is_host_set(u, "dhcp/ns_8dcab636") == False

def test_list_vpn_users(u):
    users = objects.list_vpn_users(u)
    assert len(users) == 1
    users = objects.list_vpn_users(u, True)
    assert 'ipaddr' in users[0]

def test_list_dns_records(u):
    records = objects.list_dns_records(u)
    assert len(records) == 3
    records = objects.list_dns_records(u, True)
    for r in records:
        assert 'ipaddr' in r

def test_list_dhcp_static_leases(u):
    leases = objects.list_dhcp_static_leases(u)
    assert len(leases) == 2
    leases = objects.list_dhcp_static_leases(u, True)
    for l in leases:
        assert 'ipaddr' in l

def test_list_objects(u):
    objs = objects.list_objects(u)
    assert len(objs) == len(objects.list_domain_sets(u)) + len(objects.list_host_sets(u)) + len(objects.list_vpn_users(u)) + len(objects.list_dhcp_static_leases(u)) + len(objects.list_dns_records(u))
    objs = objects.list_objects(u, expand=True)
    for o in objs:
        if o['type'] == 'host_set':
            assert 'ipaddr' in o
        elif o['type'] == 'domain_set':
            assert 'domain' in o
        elif o['type'] == 'vpn_user':
            assert 'ipaddr' in o
        elif o['type'] == 'dhcp_static_lease':
            assert 'ipaddr' in o
        elif o['type'] == 'dns_record':
            assert 'ipaddr' in o
    objs = objects.list_objects(u, include_domain_sets=False)
    for o in objs:
        assert o['type'] != 'domain_set'
    objs = objects.list_objects(u, singleton_only=True)
    for o in objs:
        if o['type'] == 'host_set':
            assert o['singleton']
            assert o['subtype']

def test_get_reference_info(u):
    ref = objects.get_info(u, "dhcp/ns_8dcab636")
    assert ref['type'] == 'host'
    assert ref['name'] == 'host2'
    assert ref['id'] == 'ns_8dcab636'
    assert ref['family'] == 'ipv4'
    assert objects.get_info(u, "unknown") == None
    ref2 = objects.get_info(u, "objects/ns_a7439990")
    assert ref2['type'] == 'host'
    assert ref2['name'] == 'h1v6'
    assert ref2['id'] == 'ns_a7439990'
    assert ref2['family'] == 'ipv6'
 
def test_is_object_with_invalid_is(u):
    assert objects.is_object_id(None) == False
    assert objects.is_object_id(1) == False