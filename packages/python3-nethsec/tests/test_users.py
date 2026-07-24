import pytest
from nethsec import utils, users
from euci import EUci, UciExceptionNotFound
from unittest.mock import MagicMock, patch


users_db = """
config local 'main'
	option description 'Main local database'

config local 'second'
	option description 'Secondary local database'

config local 'third'
    option description 'Third local database'

config ldap 'ldap1'
	option description 'Remote OpenLDAP server'
	option uri 'ldaps://192.168.100.234'
	option tls_reqcert 'never'
	option base_dn 'dc=directory,dc=nh'
	option user_dn 'ou=People,dc=directory,dc=nh'
	option user_attr 'uid'
	option user_display_attr 'cn'
    option starttls '0'
   	option schema 'rfc2307'

config ldap 'ldap2'
	option description 'Remote OpenLDAP server'
	option uri 'ldap://192.168.1.1'
	option tls_reqcert 'always'
	option base_dn 'dc=directory,dc=nh'
	option user_dn 'ou=People,dc=directory,dc=nh'
	option user_attr 'uid'
	option user_display_attr 'cn'
	option starttls '1'
   	option schema 'rfc2307'

config ldap 'ad1'
	option description 'Remote AD server'
	option uri 'ldaps://ad.nethserver.org'
	option tls_reqcert 'always'
	option base_dn 'dc=ad,dc=nethserver,dc=org'
	option user_dn 'cn=users,dc=ad,dc=nethserver,dc=org'
	option user_display_attr 'cn'
	option user_attr 'uid'
    option starttls '0'
   	option schema 'ad'

config user 'u1'
    option name "goofy"
    option database "main"
	option description 'Goofy Doe'
	list macaddr '52:54:00:9d:3d:e5'
	list ipaddr '192.168.100.23'
	list domain 'ns_goofy_name'
	list host 'ns_goofy_pc'
	option openvpn_ipaddr '10.9.9.38'

config user 'u2'
    option name "daisy"
    option database "main"
	option description "Daisy"
	list ipaddr '192.168.100.22'
	list ipaddr '2001:db8:3333:4444:5555:6666:7777:8888'

config user 'u3'
    option name "goofy"
    option database "second"
	option description 'Another Goofy'

config user 'u4'
    option name "goofy"
    option database "ldap1"

config user 'u5'
    option name "john"
    option database "ad1"

config group 'g1'
    option name "vip"
    option database "main"
	option description 'Very Important People'
	list user 'goofy'
	list user 'daisy'

config group 'g2'
    option name "vip"
    option database "ldap1"
"""

dhcp_db = """
config host 'ns_goofy_pc'
	option name 'goofypc'
    option mac '00:00:8c:16:b3:bd'
    option ip '192.168.100.36'
    option dns '1'

config domain 'ns_goofy_pc_nethserver_org'
	option ip '192.168.100.30'
    option name 'goofy.nethserver.org'
    option description 'Goofy Workstation'
"""

rpcd_db = ""

def _setup_db(tmp_path):
     # setup fake db
    with tmp_path.joinpath('users').open('w') as fp:
        fp.write(users_db)
    with tmp_path.joinpath('dhcp').open('w') as fp:
        fp.write(dhcp_db)
    with tmp_path.joinpath('rpcd').open('w') as fp:
        fp.write(rpcd_db)

    return EUci(confdir=tmp_path.as_posix())

def test_get_user_addresses(tmp_path):
    u = _setup_db(tmp_path)
    (ipv4, ipv6) = users.get_user_addresses(u, 'goofy')
    for ip in ipv4:
        assert(ip in ["192.168.100.36", "10.9.9.38", "192.168.100.30", "192.168.100.23"])
    (ipv4, ipv6) = users.get_user_addresses(u, 'daisy')
    assert(ipv6 == ["2001:db8:3333:4444:5555:6666:7777:8888"])

def test_get_user_macs(tmp_path):
    u = _setup_db(tmp_path)
    assert(users.get_user_macs(u, 'goofy') == ["52:54:00:9d:3d:e5"])
    assert(users.get_user_macs(u, 'daisy') == [])

def test_get_group_addresses(tmp_path):
    u = _setup_db(tmp_path)
    (ipv4, ipv6) = users.get_group_addresses(u, 'vip')
    for ip in ipv4:
        assert(ip in ["192.168.100.36", "10.9.9.38", "192.168.100.30", "192.168.100.23", "192.168.100.22"])
    assert(ipv6 == ["2001:db8:3333:4444:5555:6666:7777:8888"])

def test_get_group_macs(tmp_path):
    u = _setup_db(tmp_path)
    assert(users.get_group_macs(u, 'vip') == ["52:54:00:9d:3d:e5"])

def test_get_user_addresses(tmp_path):
    u = _setup_db(tmp_path)
    (ipv4, ipv6) = users.get_user_addresses(u, 'goofy')
    for ip in ipv4:
        assert(ip in ["192.168.100.36", "10.9.9.38", "192.168.100.30", "192.168.100.23"])
    (ipv4, ipv6) = users.get_user_addresses(u, 'daisy')
    assert(ipv6 == ["2001:db8:3333:4444:5555:6666:7777:8888"])

def test_get_user_macs(tmp_path):
    u = _setup_db(tmp_path)
    assert(users.get_user_macs(u, 'goofy') == ["52:54:00:9d:3d:e5"])
    assert(users.get_user_macs(u, 'daisy') == [])

def test_get_group_addresses(tmp_path):
    u = _setup_db(tmp_path)
    (ipv4, ipv6) = users.get_group_addresses(u, 'vip')
    for ip in ipv4:
        assert(ip in ["192.168.100.36", "10.9.9.38", "192.168.100.30", "192.168.100.23", "192.168.100.22"])
    assert(ipv6 == ["2001:db8:3333:4444:5555:6666:7777:8888"])

def test_get_group_macs(tmp_path):
    u = _setup_db(tmp_path)
    assert(users.get_group_macs(u, 'vip') == ["52:54:00:9d:3d:e5"])

def test_get_user_by_name(tmp_path):
    u = _setup_db(tmp_path)
    assert(users.get_user_by_name(u, 'goofy') == {
        "name": "goofy",
        "database": "main",
        "description": "Goofy Doe",
        "macaddr": ["52:54:00:9d:3d:e5"],
        "ipaddr": ["192.168.100.23"],
        "domain": ["ns_goofy_name"],
        "host": ["ns_goofy_pc"],
        "openvpn_ipaddr": "10.9.9.38",
        "local": True,
        "admin": False,
        "id": "u1",
    })

    assert(users.get_user_by_name(u, 'goofy', database="second") == {
        "name": "goofy",
        "description": "Another Goofy",
        "database": "second",
        "local": True,
        "admin": False,
        "id": "u3"
    })

    assert(users.get_user_by_name(u, 'daisy', database="second") == None)
                   
def test_get_group_by_name(tmp_path):
    u = _setup_db(tmp_path)
    assert(users.get_group_by_name(u, 'vip') == {
        "name": "vip",
        "database": "main",
        "description": "Very Important People",
        "user": ["goofy", "daisy"],
        "local": True,
        "id": "g1"
    })
    
def test_list_databases(tmp_path):
    db_list = users.list_databases(_setup_db(tmp_path))
    assert {"name": "main", "description": "Main local database", "type": "local"} in db_list
    assert {"name": "second", "description": "Secondary local database", "type": "local"} in db_list
    assert {"name": "ldap1", "description": "Remote OpenLDAP server", "type": "ldap", "schema": "rfc2307", "uri": "ldaps://192.168.100.234", "used": []} in db_list
    assert {"name": "ad1", "description": "Remote AD server", "type": "ldap", "schema": "ad", "uri": "ldaps://ad.nethserver.org", "used": []} in db_list

def test_add_local_database(tmp_path):
    u = _setup_db(tmp_path)
    users.add_local_database(u, "test", "Test database")
    assert u.get('users', 'test') != None
    assert u.get('users', 'test', 'description') == "Test database"

def test_add_ldap_database(tmp_path):
    u = _setup_db(tmp_path)
    users.add_ldap_database(u, "testldap", "ldap://1.2.3.4", "ad", "dc=test,dc=org", "cn=users,dc=test,dc=org", "cn", "cn")
    assert u.get('users', 'testldap') != None
    assert u.get('users', 'testldap', 'uri') == "ldap://1.2.3.4"
    assert u.get('users', 'testldap', 'schema') == "ad"
    assert u.get('users', 'testldap', 'base_dn') == "dc=test,dc=org"
    assert u.get('users', 'testldap', 'user_dn') == "cn=users,dc=test,dc=org"
    assert u.get('users', 'testldap', 'user_attr') == "cn"
    assert u.get('users', 'testldap', 'user_display_attr') == "cn"
    assert u.get('users', 'testldap', 'start_tls') == "0"
    assert u.get('users', 'testldap', 'tls_reqcert') == "never"
    with pytest.raises(UciExceptionNotFound) as e:
        assert u.get('users', 'testldap', 'user_bind_dn')

    users.add_ldap_database(u, "testldap2", "ldaps://server.nethserver.org", "rfc2307", "dc=test,dc=org", "ou=People,dc=test,dc=org", "uid", "displayName", start_tls=True, tls_reqcert="always", description="mydesc")
    assert u.get('users', 'testldap2') != None
    assert u.get('users', 'testldap2', 'description') == "mydesc"
    assert u.get('users', 'testldap2', 'uri') == "ldaps://server.nethserver.org"
    assert u.get('users', 'testldap2', 'schema') == "rfc2307"
    assert u.get('users', 'testldap2', 'base_dn') == "dc=test,dc=org"
    assert u.get('users', 'testldap2', 'user_dn') == "ou=People,dc=test,dc=org"
    assert u.get('users', 'testldap2', 'user_attr') == "uid"
    assert u.get('users', 'testldap2', 'user_display_attr') == "displayName"
    assert u.get('users', 'testldap2', 'start_tls') == "1"
    assert u.get('users', 'testldap2', 'tls_reqcert') == "always"

    users.add_ldap_database(u, "testldap3", "ldaps://server.nethserver.org", "rfc2307", "dc=test,dc=org", "ou=People,dc=test,dc=org", "uid", "displayName", start_tls=True, tls_reqcert="always", description="mydesc", bind_dn="cn=admin,dc=test,dc=org", bind_password="12=34", user_bind_dn="%u@test.org")
    assert u.get('users', 'testldap3') != None
    assert u.get('users', 'testldap3', 'bind_dn') == "cn=admin,dc=test,dc=org"
    assert u.get('users', 'testldap3', 'bind_password') == "12=34"
    assert u.get('users', 'testldap3', 'user_bind_dn') == "%u@test.org"
    

def test_list_users(tmp_path):
    u = _setup_db(tmp_path)
    user_list = users.list_users(_setup_db(tmp_path), "second")
    assert(users.get_user_by_name(u, 'goofy', "second") in user_list)

def test_edit_ldap_database(tmp_path):
    u = _setup_db(tmp_path)
    users.edit_ldap_database(u, "testldap2", "ldaps://server.nethserver.org", "rfc2307", "dc=test2,dc=org2", "dc=test2,dc=org2", "uid", "cn", start_tls=False, tls_reqcert="never", description="mydesc2")
    assert u.get_all('users', 'testldap2') == {
        "description": "mydesc2",
        "uri": "ldaps://server.nethserver.org",
        "schema": "rfc2307",
        "base_dn": "dc=test2,dc=org2",
        "user_dn": "dc=test2,dc=org2",
        "user_attr": "uid",
        "user_display_attr": "cn",
        "start_tls": "0",
        "tls_reqcert": "never"
    }

    users.edit_ldap_database(u, "testldap3", "ldaps://server.nethserver.org", "rfc2307", "dc=test2,dc=org2", "dc=test2,dc=org2", "uid", "cn", start_tls=False, tls_reqcert="never", description="mydesc2")
    with pytest.raises(UciExceptionNotFound) as e:
        assert u.get('users', 'testldap3', 'bind_dn')
    with pytest.raises(UciExceptionNotFound) as e:
        assert u.get('users', 'testldap3', 'bind_password')
    users.edit_ldap_database(u, "testldap3", "ldaps://server.nethserver.org", "rfc2307", "dc=test2,dc=org2", "dc=test2,dc=org2", "uid", "cn", start_tls=False, tls_reqcert="never", description="mydesc2", bind_dn="cn=admin2,dc=test,dc=org", bind_password="4567", user_bind_dn="%u@test2.org2")
    assert u.get('users', 'testldap3', 'bind_dn') == "cn=admin2,dc=test,dc=org"
    assert u.get('users', 'testldap3', 'bind_password') == "4567"
    assert u.get('users', 'testldap3', 'user_bind_dn') == "%u@test2.org2"
    # check if user_bind_dn is deleted if not passed as parameter
    users.edit_ldap_database(u, "testldap3", "ldaps://server.nethserver.org", "rfc2307", "dc=test2,dc=org2", "dc=test2,dc=org2", "uid", "cn", start_tls=False, tls_reqcert="never", description="mydesc2", bind_dn="cn=admin2,dc=test,dc=org", bind_password="4567")
    with pytest.raises(UciExceptionNotFound) as e:
        assert u.get('users', 'testldap3', 'user_bind_dn')
    # add back user_bind_dn, check if it's removed if passed as empty string
    users.edit_ldap_database(u, "testldap3", "ldaps://server.nethserver.org", "rfc2307", "dc=test2,dc=org2", "dc=test2,dc=org2", "uid", "cn", start_tls=False, tls_reqcert="never", description="mydesc2", bind_dn="cn=admin2,dc=test,dc=org", bind_password="4567", user_bind_dn="%u@test3.org3")
    assert u.get('users', 'testldap3', 'user_bind_dn') == "%u@test3.org3"
    users.edit_ldap_database(u, "testldap3", "ldaps://server.nethserver.org", "rfc2307", "dc=test2,dc=org2", "dc=test2,dc=org2", "uid", "cn", start_tls=False, tls_reqcert="never", description="mydesc2", bind_dn="cn=admin2,dc=test,dc=org", bind_password="4567", user_bind_dn="")
    with pytest.raises(UciExceptionNotFound) as e:
        assert u.get('users', 'testldap3', 'user_bind_dn')



def test_delete_ldap_database(tmp_path):
    u = _setup_db(tmp_path)
    users.delete_ldap_database(u, "ldap1")
    with pytest.raises(UciExceptionNotFound) as e:
        assert u.get('users', 'ldap1')
    with pytest.raises(UciExceptionNotFound) as e:
        assert u.get('users', 'u4')
    with pytest.raises(UciExceptionNotFound) as e:
        assert u.get('users', 'g2')

def test_edit_local_database(tmp_path):
    u = _setup_db(tmp_path)
    users.edit_local_database(u, "main", "Main local database2")
    assert u.get('users', 'main', 'description') == "Main local database2"

def test_delete_local_database(tmp_path):
    u = _setup_db(tmp_path)
    users.delete_local_database(u, "main")
    with pytest.raises(UciExceptionNotFound) as e:
        assert u.get('users', 'main') == None
    with pytest.raises(UciExceptionNotFound) as e:
        u.get('users', 'u1')
    with pytest.raises(UciExceptionNotFound) as e:
        u.get('users', 'u2')
    with pytest.raises(UciExceptionNotFound) as e:
        u.get('users', 'g1')

def test_add_local_user(tmp_path):
    u = _setup_db(tmp_path)
    id = users.add_local_user(u, "t1", password="nethesis", description="mydesc", database="second", extra_fields={"openvpn_ipaddr": "1.2.3.4"})
    user = users.get_user_by_name(u, "t1", "second") 
    assert user != None
    assert users.check_password("nethesis", user.pop("password"))
    assert user == {
        "name": "t1",
        "description": "mydesc",
        "database": "second",
        "local": True,
        "admin": False,
        "id": id,
        "openvpn_ipaddr": "1.2.3.4"
    }

def test_edit_local_user(tmp_path):
    u = _setup_db(tmp_path)
    id = users.edit_local_user(u, "t1", password="pass2", description='mydesc2', database="second", extra_fields={"openvpn_ipaddr": "1.2.3.5", "openvpn_enabled": "1"})
    user = users.get_user_by_name(u, "t1", "second")
    assert users.check_password("pass2", user.pop("password"))
    assert user == {
        "name": "t1",
        "description": "mydesc2",
        "database": "second",
        "local": True,
        "admin": False,
        "id": id,
        "openvpn_ipaddr": "1.2.3.5",
        "openvpn_enabled": "1"
    }
    # make sure description is not changed if not passed as parameter
    id = users.edit_local_user(u, "t1", password="pass2", database="second", extra_fields={"openvpn_ipaddr": "1.2.3.5", "openvpn_enabled": "1"})
    assert u.get('users', id, 'description') == 'mydesc2'
    id = users.edit_local_user(u, "t1", password="pass2",  database="second", extra_fields={"openvpn_enabled": "1"})
    with pytest.raises(UciExceptionNotFound) as e:
        assert u.get('users', id, 'openvpn_ipaddr')

def test_add_local_group(tmp_path):
    u = _setup_db(tmp_path)
    id = users.add_local_group(u, "group3", ["goofy", "daisy"], "mydesc", database="second")
    assert u.get_all('users', id) == {
        "name": "group3",
        "description": "mydesc",
        "database": "second",
        "user": ("goofy", "daisy"),
    }

def test_edit_local_group(tmp_path):
    u = _setup_db(tmp_path)
    id = users.edit_local_group(u, "group3", ["goofy"], "mydesc2", database="second")
    assert u.get('users', id, 'description') == 'mydesc2'
    assert u.get('users', id, 'user', list=True) == ('goofy',)

def test_delete_local_user(tmp_path):
    u = _setup_db(tmp_path)
    assert users.delete_local_user(u, "t1", database="second")
    assert users.get_user_by_name(u, "t1", "second") == None
    assert users.delete_local_user(u, "goofy", database="second")
    group = users.get_group_by_name(u, "group3", "second")
    assert group.get('user',[]) == []

def test_delete_local_group(tmp_path):
    u = _setup_db(tmp_path)
    group = users.get_group_by_name(u, "group3", "second")
    users.delete_local_group(u, "group3", database="second")
    with pytest.raises(UciExceptionNotFound) as e:
        assert u.get('users', group['id'])

def test_add_remote_user(tmp_path):
    u = _setup_db(tmp_path)
    id = users.add_remote_user(u, "john", "ldap2", extra_fields={"openvpn_ipaddr": "1.2.3.4"})
    u.get('users', id, 'name') == "john"
    u.get('users', id, 'database') == "ldap2"
    u.get('users', id, 'openvpn_ipaddr') == "1.2.3.4"

def test_edit_remote_user(tmp_path):
    u = _setup_db(tmp_path)
    id = users.edit_remote_user(u, "john", "ldap2", extra_fields={"openvpn_enabled": "1"})
    with pytest.raises(UciExceptionNotFound) as e:
        assert u.get('users', id, 'openvpn_ipaddr')
    u.get('users', id, 'openvpn_enabled') == "1"

def test_delete_remote_user(tmp_path):
    u = _setup_db(tmp_path)
    user = users.get_user_by_name(u, "john", "ldap2")
    users.delete_remote_user(u, "john", database="ldap2")
    with pytest.raises(UciExceptionNotFound) as e:
        assert u.get('users', user['id'])

def test_shadow_password():
    shadow = users.shadow_password("test")
    assert(users.check_password("test", shadow))

def test_ldif2users():
    ldif_data = """
dn: uid=admin,ou=People,dc=directory,dc=nh
uid: admin
cn: admin

dn: uid=pluto,ou=People,dc=directory,dc=nh
uid: pluto
cn: Pluto Rossi

# pagedresults: cookie=
"""
    assert users.ldif2users(ldif_data) == [{"name": "admin", "description": "admin"},{"name":"pluto", "description": "Pluto Rossi"}]

    ldif_data = """
# John Doe, Users, domtest1.local
dn: CN=John Doe,CN=Users,DC=domtest1,DC=local
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: user
cn: John Doe
sn: doe
description: myoffice
physicalDeliveryOfficeName: myoffice
givenName: john
distinguishedName: CN=John Doe,CN=Users,DC=domtest1,DC=local
instanceType: 4
whenCreated: 20240605091444.0Z
whenChanged: 20240702131054.0Z
displayName: John Doe
uSNCreated: 45212
uSNChanged: 49102
name: John Doe
objectGUID:: 0JQMYe1R+0uziXQFbmQoJg==
userAccountControl: 512
badPwdCount: 0
codePage: 0
countryCode: 0
badPasswordTime: 133621586649855275
lastLogoff: 0
lastLogon: 133621586960949063
pwdLastSet: 133632746540757598
primaryGroupID: 513
objectSid:: AQUAAAAAAAUVAAAAvh3X9UPJVVW6ljm9VwQAAA==
accountExpires: 9223372036854775807
logonCount: 0
sAMAccountName: john.doe
sAMAccountType: 805306368
userPrincipalName: john.doe@domtest1.local
objectCategory: CN=Person,CN=Schema,CN=Configuration,DC=domtest1,DC=local
dSCorePropagationData: 16010101000000.0Z
"""
    assert users.ldif2users(ldif_data, 'sAMAccountName', 'displayName') == [{"name": "john.doe", "description": "John Doe"}]
    
def test_set_admin_user(tmp_path):
    u = _setup_db(tmp_path)
    users.add_local_user(u, "admin2", password="nethesis", description="mydesc", database="third")
    admin_id_rpcd = users.set_admin(u, "admin2", "third")
    for user in utils.get_all_by_type(u, "rpcd", "login"):
        if user == admin_id_rpcd:
            assert u.get('rpcd', admin_id_rpcd, "username") == "admin2"
            assert users.check_password("nethesis", u.get('rpcd', admin_id_rpcd, "password"))

def test_is_admin(tmp_path):
    u = _setup_db(tmp_path)
    assert users.is_admin(u, "admin2")
    user = users.get_user_by_name(u, "admin2", 'third')
    assert user.get("admin")

def test_change_admin_password(tmp_path):
    u = _setup_db(tmp_path)
    local_id = users.edit_local_user(u, "admin2", password="nethesis", description="mydesc", database="third")
    logins = utils.get_all_by_type(u, "rpcd", "login")
    for l in logins:
        if logins[l].get("username") == "admin2":
            assert logins[l].get("password") == u.get("users", local_id, "password")
  
def test_remove_admin_user(tmp_path):
    u = _setup_db(tmp_path)
    users.remove_admin(u, "admin2")
    found = False
    for user in utils.get_all_by_type(u, "rpcd", "login"):
        if user.get("username") == "admin2":
            found = True
    assert not found

def test_get_database(tmp_path):
    u = _setup_db(tmp_path)
    assert users.get_database(u, "third") == {
        "name": "third",
        "description": "Third local database",
        "type": "local"
    }

    assert users.get_database(u, "ad1") == {
        "name": "ad1",
        "description": "Remote AD server",
        "type": "ldap",
        "schema": "ad",
        "uri": "ldaps://ad.nethserver.org",
        "tls_reqcert": "always",
        "base_dn": "dc=ad,dc=nethserver,dc=org",
        "user_dn": "cn=users,dc=ad,dc=nethserver,dc=org",
        "user_attr": "uid",
        "user_display_attr": "cn",
        "starttls": "0"
    }
