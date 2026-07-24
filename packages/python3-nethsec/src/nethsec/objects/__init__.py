#!/usr/bin/python3

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

'''
Objects utilities
'''
import ipaddress
import json
import os
import subprocess

from euci import EUci

from nethsec import utils, firewall

# Generic

def is_object_id(id):
    """
    Check if an id is an object id.

    Args:
        id: id to check

    Returns:
        True if id is an object id, False otherwise
    """
    if not id or not isinstance(id, str):
        return False
    return id.startswith('objects/') or id.startswith('dhcp/') or id.startswith('users/')

def object_exists(uci, database_id):
    """
    Check if the object exists.

    Args:
        database_id: id to check in the form of `<database>/<id>`
    
    Returns:
        True if object exists, False otherwise
    """
    try:
        database, id = database_id.split('/')
        uci.get(database, id)
        return True
    except:
        return False

def get_object(uci, database_id):
    """
    Get object from objects config.

    Args:
        uci: EUci pointer
        id: id of the object in the form of `<database>/<id>`

    Returns:
        object from config or None if not found
    """
    try:
        database, id = database_id.split('/')
        return uci.get_all(database, id)
    except:
        return None

def is_used_object(uci, database_id):
    """
    Check if an object is used in:
     - firewall config
     - mwan3 config
     - dpi config
     - existing host set

    Args:
        uci: EUci pointer
        id: id of the object in the form of `<database>/<id>`

    Returns:
        A tuple with:
        - True if domain set is used in firewall config, False otherwise
        - a list of firewall sections where domain set is used
    """
    matches = []
    for section in uci.get_all("firewall"):
        if uci.get('firewall', section, 'ns_src', default=None) == database_id or uci.get('firewall', section, 'ns_dst', default=None) == database_id:
            matches.append(f'firewall/{section}')
    for section in uci.get_all("mwan3"):
        if uci.get('mwan3', section, 'ns_src', default=None) == database_id or uci.get('mwan3', section, 'ns_dst', default=None) == database_id:
            matches.append(f'mwan3/{section}')
    for section in uci.get_all("dpi"):
        if uci.get('dpi', section, 'source', default=None) == database_id:
            matches.append(f'dpi/{section}')
    for section in uci.get_all("objects"):
        try:
            ips = uci.get_all('objects', section, 'ipaddr')
            if database_id in ips:
                matches.append(f'objects/{section}')
        except:
            continue
    return len(matches) > 0, matches

def get_object_ips(uci, database_id):
    """
    Get all IP addresses from an object.

    Args:
        uci: EUci pointer
        id: id of the object in the form of `<database>/<id>`

    Returns:
        a list of unique IP addresses from the object
    """
    ips = []
    if not database_id:
        return ips

    obj = get_object(uci, database_id)
    database, id = database_id.split('/')

    if not obj:
        return ips
    
    if database == 'dhcp':
        ip = obj.get('ip')
        if ip:
            ips.append(ip)
    elif database == 'users':
        openvpn_ipaddr = obj.get('openvpn_ipaddr')
        if openvpn_ipaddr:
            ips.append(openvpn_ipaddr)
    elif database == 'objects':
        ipaddr = obj.get('ipaddr')
        if ipaddr:
            for ip in ipaddr:
                if is_object_id(ip):
                    ips.extend(get_object_ips(uci, ip))
                else:
                    ips.append(ip)
    
    return list(set(ips))  # Convert the list to a set to remove duplicates, then convert it back to a list

def get_object_ip(uci, database_id):
    """
    Get the first IP address from an object.

    Args:
        uci: EUci pointer
        id: id of the object in the form of `<database>/<id>`

    Returns:
        the first IP address from the object
    """
    ips = get_object_ips(uci, database_id)
    if ips:
        return ips[0]
    return None

# Domain set

def is_domain_set(uci, database_id):
    """
    Check if an object is a domain set.

    Args:
        uci: EUci pointer
        id: id of the object in the form of `<database>/<id>`

    Returns:
        True if object is a domain set, False otherwise
    """
    try:
        database, id = database_id.split('/')
        obj_type = uci.get(database, id)
        return database =="objects" and obj_type == "domain"
    except:
        return False

def is_used_domain_set(uci, id):
    """
    Check if domain set is used in firewall config.

    Args:
        uci: EUci pointer
        id: id of domain set

    Returns:
        A tuple with:
        - True if domain set is used in firewall config, False otherwise
        - a list of firewall sections where domain set is used
    """
    return is_used_object(uci, f'objects/{id}')

def get_domain_set_ipsets(uci, id):
    """
    Get ipsets linked to domain set.

    Args:
        uci: EUci pointer
        id: id of domain set

    Returns:
        a dictionary with
        - `firewall`: the ipset id linked to domain set from firewall config
        - `dhcp`: the ipset id linked to domain set from dhcp config
    """
    ipsets = {"firewall": None, "dhcp": None}
    for section in utils.get_all_by_type(uci, "firewall", "ipset"):
        if uci.get('firewall', section, 'ns_link', default=None) == f'objects/{id}':
            ipsets["firewall"] = uci.get("firewall", section, "name", default='')
            break
    for section in utils.get_all_by_type(uci, "dhcp", "ipset"):
        if uci.get('dhcp', section, 'ns_link', default=None) == f'objects/{id}':
            ipsets["dhcp"] = section
            break
    return ipsets

def get_domain_set_total_chars(name: str, unique_domains: list[str]):
    """
    Calculate the total number of characters the given domain set will use in the dnsmasq configuration file.
    This file supports a maximum of 1024 characters per line.

    Example syntax of a domain set in dnsmasq configuration file:
    nftset=/example1.org/example2.org/example3.org/.../4#inet#fw4#domainSetName

    Args:
        name: name of domain set
        domains: a list of valid DNS names
        
    Returns:
        the number of characters
    """
    total_chars = 8 + 11  # leading "nftset=/" and trailing "4#inet#fw4#"

    for domain in unique_domains:
        total_chars += len(domain) + 1  # +1 for trailing "/"

    total_chars += len(name)  # domain set name
    return total_chars

def add_domain_set(uci, name: str, family: str, domains: list[str], timeout: int = 660) -> str:
    """
    Add domain set to objects config.

    Args:
        uci: EUci pointer
        name: name of domain set
        family: can be `ipv4` or `ipv6`
        domains: a list of valid DNS names
        timeout: the timeout in seconds for the DNS resolution, default is `660` seconds

    Returns:
        id of domain set config that was added
    """
    if len(name) > 16:
        raise utils.ValidationError('name', 'name_too_long', name)
    # check name contains only number and letters
    if not name.isalnum():
        raise utils.ValidationError('name', 'invalid_name', name)
    if family not in ['ipv4', 'ipv6']:
        raise utils.ValidationError('family', 'invalid_family', family)
    if timeout < 0:
        raise utils.ValidationError('timeout', 'invalid_timeout', timeout)

    # remove duplicated domains
    unique_domains = list(dict.fromkeys(domains))
    if get_domain_set_total_chars(name, unique_domains) > 1024 - 10:  # -10 chars for safety
        raise utils.ValidationError('domain', 'total_chars_exceeded')

    id = utils.get_random_id()
    uci.set('objects', id, 'domain')
    uci.set('objects', id, 'name', name)
    uci.set('objects', id, 'family', family)
    uci.set('objects', id, 'timeout', timeout)
    uci.set('objects', id, 'domain', unique_domains)
    uci.save('objects')

    # create ipset inside dhcp config
    ipset = utils.get_random_id()
    uci.set('dhcp', ipset, 'ipset')
    uci.set('dhcp', ipset, 'name', [name])
    uci.set('dhcp', ipset, 'domain', unique_domains)
    uci.set('dhcp', ipset, 'table_family', 'inet')
    uci.set('dhcp', ipset, 'ns_link', f'objects/{id}')
    uci.save('dhcp')

    # create ipset inside firewall config
    ipset = utils.get_random_id()
    uci.set('firewall', ipset, 'ipset')
    uci.set('firewall', ipset, 'name', name)
    uci.set('firewall', ipset, 'family', family)
    uci.set('firewall', ipset, 'timeout', timeout)
    uci.set('firewall', ipset, 'counters', '1')
    uci.set('firewall', ipset, 'match', 'ip')
    uci.set('firewall', ipset, 'ns_link', f'objects/{id}')
    uci.save('firewall')
    return id

def edit_domain_set(uci, id: str, name: str, family: str, domains: list[str], timeout: int = 660) -> str:
    """
    Edit domain set in objects config.

    Args:
        uci: EUci pointer
        id: id of domain set to edit
        name: name of domain set
        family: can be `ipv4` or `ipv6`
        domains: a list of valid DNS names
        timeout: the timeout in seconds for the DNS resolution, default is `660` seconds

    Returns:
        id of domain set config that was edited
    """
    if not uci.get('objects', id, default=None):
        raise utils.ValidationError("id", "domain_set_does_not_exists", id)
    if len(name) > 16:
        raise utils.ValidationError('name', 'name_too_long', name)
    if family not in ['ipv4', 'ipv6']:
        raise utils.ValidationError('family', 'invalid_family', family)
    if timeout < 0:
        raise utils.ValidationError('timeout', 'invalid_timeout', timeout)

    # remove duplicated domains
    unique_domains = list(dict.fromkeys(domains))
    if get_domain_set_total_chars(name, unique_domains) > 1024 - 10:  # -10 chars for safety
        raise utils.ValidationError('domain', 'total_chars_exceeded')

    uci.set('objects', id, 'name', name)
    uci.set('objects', id, 'family', family)
    uci.set('objects', id, 'timeout', timeout)
    uci.set('objects', id, 'domain', unique_domains)
    uci.save('objects')

    # update ipset inside dhcp config
    for section in uci.get_all("dhcp"):
        if uci.get('dhcp', section, 'ns_link', default=None) == f'objects/{id}':
            uci.set('dhcp', section, 'name', [name])
            uci.set('dhcp', section, 'domain', unique_domains)
            uci.set('dhcp', section, 'ns_tag', ['automated'])
            uci.save('dhcp')
            break
    for section in uci.get_all("firewall"):
        if uci.get('firewall', section, 'ns_link', default=None) == f'objects/{id}':
            uci.set('firewall', section, 'name', name)
            uci.set('firewall', section, 'family', family)
            uci.set('firewall', section, 'timeout', timeout)
            uci.set('firewall', section, 'ns_tag', ['automated'])
            uci.save('firewall')
            break
    return id

def delete_domain_set(uci, id: str) -> str:
    """
    Delete domain set from objects config.

    Args:
        uci: EUci pointer
        id: id of domain set to delete

    Returns:
        name of domain set config that was deleted
    """
    if not uci.get('objects', id, default=None):
        raise utils.ValidationError("id", "domain_set_does_not_exists", id)
    used, matches = is_used_domain_set(uci, id)
    if used:
        raise utils.ValidationError("id", "domain_set_is_used", matches)
    uci.delete('objects', id)
    uci.save('objects')
    for section in uci.get_all("dhcp"):
        if uci.get('dhcp', section, 'ns_link', default=None) == f'objects/{id}':
            uci.delete('dhcp', section)
            uci.save('dhcp')
            break
    for section in uci.get_all("firewall"):
        if uci.get('firewall', section, 'ns_link', default=None) == f'objects/{id}':
            uci.delete('firewall', section)
            uci.save('firewall')
            break
    return id

def list_domain_sets(uci, used_info = True) -> list:
    """
    Get all domain sets from objects config

    Args:
        uci: EUci pointer
        used_info: include used and matches info

    Returns:
        a list of all domain sets
    """
    sets = []
    for section in uci.get_all("objects"):
        if uci.get('objects', section) == 'domain':
            rule = uci.get_all('objects', section)
            rule['id'] = section
            rule['type'] = 'domain_set'
            rule['subtype'] = 'domain_set'
            if used_info:
                used, matches = is_used_domain_set(uci, section)
                rule['used'] = used
                rule['matches'] = matches
            sets.append(rule)
    return sets

# Host set

def _has_loop(uci, id, ipaddr, depth=0):
    if depth > 2:
        return True
    if is_object_id(ipaddr):
        if ipaddr == id:
            return True
        obj = get_object(uci, ipaddr)
        if obj:
            for ip in obj.get('ipaddr', []):
                if _has_loop(uci, id, ip, depth + 1):
                    return True
    return False

def _validate_host_set_ipaddr(uci, id, ipaddr: str, family: str):
    if is_object_id(ipaddr):
        if not object_exists(uci, ipaddr):
            raise utils.ValidationError('ipaddr', 'object_does_not_exists', ipaddr)
        else:
            if id and is_host_set(uci, id):
                # check loop
                if _has_loop(uci, id, ipaddr):
                    raise utils.ValidationError('ipaddr', 'loop_detected', ipaddr)
        return # validation is ok

    if family == 'ipv4':
        return _validate_host_set_ipaddr_v4(ipaddr)
    elif family == 'ipv6':
        return _validate_host_set_ipaddr_v6(ipaddr)
    
def _validate_host_set_ipaddr_v4(ipaddr: str):
    if '/' in ipaddr:
        # validate CIDR
        try:
            ipaddress.IPv4Network(ipaddr)
        except:
            raise utils.ValidationError('ipaddr', 'invalid_ipaddr', ipaddr)
    elif '-' in ipaddr:
        start, end = ipaddr.split('-')
        try:
            ipaddress.IPv4Address(start)
            ipaddress.IPv4Address(end)
        except:
            raise utils.ValidationError('ipaddr', 'invalid_ipaddr', ipaddr)
    else:
        # validate IPv4
        try:
            ipaddress.IPv4Address(ipaddr)
        except:
            raise utils.ValidationError('ipaddr', 'invalid_ipaddr', ipaddr)
    return True

def _validate_host_set_ipaddr_v6(ipaddr: str):
    if '/' in ipaddr:
        # validate CIDR
        try:
            ipaddress.IPv6Network(ipaddr)
        except:
            raise utils.ValidationError('ipaddr', 'invalid_ipaddr', ipaddr)
    elif '-' in ipaddr:
        start, end = ipaddr.split('-')
        try:
            ipaddress.IPv6Address(start)
            ipaddress.IPv6Address(end)
        except:
            raise utils.ValidationError('ipaddr', 'invalid_ipaddr', ipaddr)
    else:
        # validate IPv6
        try:
            ipaddress.IPv6Address(ipaddr)
        except:
            raise utils.ValidationError('ipaddr', 'invalid_ipaddr', ipaddr)
    return True

def add_host_set(uci, name: str, family: str, ipaddrs: list[str]) -> str:
    """
    Add host set to objects config.

    Args:
        uci: EUci pointer
        name: name of host set
        family: can be `ipv4` or `ipv6`
        ipaddrs: a list of IP addresses

    Returns:
        id of host set config that was added
    """
    if len(name) > 16:
        raise utils.ValidationError('name', 'name_too_long', name)
    # check name contains only number and letters
    if not name.isalnum():
        raise utils.ValidationError('name', 'invalid_name', name)
    for ipaddr in ipaddrs:
        _validate_host_set_ipaddr(uci, '', ipaddr, family)
    id = utils.get_random_id()
    uci.set('objects', id, 'host')
    uci.set('objects', id, 'name', name)
    uci.set('objects', id, 'family', family)
    uci.set('objects', id, 'ipaddr', ipaddrs)
    uci.save('objects')
    return id

def edit_host_set(uci, id: str, name: str, family: str, ipaddrs: list[str]) -> str:
    """
    Edit host set in objects config.

    Args:
        uci: EUci pointer
        id: id of host set to edit
        name: name of host set
        family: can be `ipv4` or `ipv6`
        ipaddrs: a list of IP addresses

    Returns:
        id of host set config that was edited
    """
    if not uci.get('objects', id, default=None):
        raise utils.ValidationError("id", "host_set_does_not_exists", id)
    if len(name) > 16:
        raise utils.ValidationError('name', 'name_too_long', name)
    for ipaddr in ipaddrs:
        _validate_host_set_ipaddr(uci, f'objects/{id}', ipaddr, family)
    uci.set('objects', id, 'name', name)
    uci.set('objects', id, 'family', family)
    uci.set('objects', id, 'ipaddr', ipaddrs)
    uci.save('objects')
    return id

def delete_host_set(uci, id: str) -> str:
    """
    Delete host set from objects config.

    Args:
        uci: EUci pointer
        id: id of host set to delete

    Returns:
        name of host set config that was deleted
    """
    if not uci.get('objects', id, default=None):
        raise utils.ValidationError("id", "host_set_does_not_exists", id)
    used, matches = is_used_host_set(uci, id)
    if used:
        raise utils.ValidationError("id", "host_set_is_used", matches)
    uci.delete('objects', id)
    uci.save('objects')
    return id

def is_used_host_set(uci, id):
    """
    Check if host set is used in firewall config.

    Args:
        uci: EUci pointer
        id: id of host set

    Returns:
        A tuple with:
        - True if host set is used in firewall config, False otherwise
        - a list of firewall sections where host set is used
    """
    return is_used_object(uci, f'objects/{id}')

def list_host_sets(uci, used_info = True) -> list:
    """
    Get all host sets from objects config

    Args:
        uci: EUci pointer
        used_info: include used and matches info

    Returns:
        a list of all host sets
    """
    sets = []
    for section in uci.get_all("objects"):
        if uci.get('objects', section) == 'host':
            rule = uci.get_all('objects', section)
            rule['id'] = section
            rule['singleton'] = is_singleton_host_set(uci, f'objects/{section}')
            if rule['singleton']:
                # set subtype to CIDR, range or host
                ip = get_object_ip(uci, f'objects/{section}')
                if '/' in ip:
                    rule['subtype'] = 'cidr'
                elif '-' in ip:
                    rule['subtype'] = 'range'
                else:
                    rule['subtype'] = 'host'
            else:
                rule['subtype'] = 'host_set'
            if used_info:
                used, matches = is_used_host_set(uci, section)
                rule['used'] = used
                rule['matches'] = matches
            sets.append(rule)
    return sets

def is_host_set(uci, database_id):
    """
    Check if an object is a host set.

    Args:
        uci: EUci pointer
        id: id of the object in the form of `<database>/<id>`

    Returns:
        True if object is a host set, False otherwise
    """
    try:
        database, id = database_id.split('/')
        obj_type = uci.get(database, id)
        return database == "objects" and obj_type == "host"
    except:
        return False

# in mathematical terms, a singleton set is a set with exactly one element
def is_singleton_host_set(uci, database_id, allow_cidr=False):
    """
    Check if an object is a host set with a single IP address.
    The IP must not be an IP range.
    If `allow_cidr` is True, the IP can be in CIDR notation.

    Args:
        uci: EUci pointer
        database_id: id of the object in the form of `<database>/<id>`
        allow_cidr: allow CIDR notation

    Returns:
        True if object is a singleton host set, False otherwise
    """
    if is_host_set(uci, database_id):
        obj = get_object(uci, database_id)
        if obj and len(obj.get('ipaddr')) == 1:
            ip = obj.get('ipaddr')[0]
            if '-' in ip:
                return False
            if allow_cidr:
                return True
            else:
                return '/' not in ip
    return False

# Host

def is_host(uci, database_id):
    """
    Check if an object is a host.

    Args:
        uci: EUci pointer
        database_id: id of the object in the form of `<database>/<id>`

    Returns:
        True if object is a host, False otherwise
    """
    try:
        database, id = database_id.split('/')
        obj_type = uci.get(database, id)
        return database == "dhcp" and obj_type == "host"
    except:
        return False

# Domain

def is_domain(uci, database_id):
    """
    Check if an object is a domain.

    Args:
        uci: EUci pointer
        database_id: id of the object in the form of `<database>/<id>`

    Returns:
        True if object is a domain, False otherwise
    """
    try:
        database, id = database_id.split('/')
        obj_type = uci.get(database, id)
        return database == "dhcp" and obj_type == "domain"
    except:
        return False

# VPN user

def is_vpn_user(uci, database_id):
    """
    Check if an object is a VPN user.

    Args:
        uci: EUci pointer
        database_id: id of the object in the form of `<database>/<id>`

    Returns:
        True if object is a VPN user, False otherwise
    """
    try:
        database, id = database_id.split('/')
        obj_type = uci.get(database, id)
        return database == "users" and obj_type == "user" and uci.get(database, id, 'openvpn_ipaddr', default=None) != None
    except:
        return False
    
# API suggestions functions

# Each element of the list should contain the following fields:
# - `id`: the id of the object
# - `name`: the name of the object
# - `type`: the type of the object
# - `family`: the family of the object (optional)
# If expand flag is set to True, the list should contain all IP addresses of the object

def list_vpn_users(uci, expand=False, used_info=False):
    """
    Get all VPN users from users config

    Args:
        uci: EUci pointer
        expand: expand the list with all IP addresses of the object
        used_info: include used and matches info

    Returns:
        a list of all VPN users
    """
    users = []
    for section in uci.get_all("users"):
        user = {}
        if uci.get('users', section) == 'user' and uci.get('users', section, 'openvpn_ipaddr', default=None) != None:
            obj = uci.get_all('users', section)
            user['id'] = f"users/{section}"
            user['name'] = obj.get('name')
            user['type'] = 'vpn_user'
            user['subtype'] = 'vpn_user'
            user['family'] = 'ipv4'
            if expand:
                user['ipaddr'] = [obj.get('openvpn_ipaddr')]
            if used_info:
                used, matches = is_used_object(uci, f'users/{section}')
                user['used'] = used
                user['matches'] = matches
            users.append(user)
    return users

def list_dhcp_static_leases(uci, expand=False, used_info=False):
    """
    Get all DHCP static leases from dhcp config

    Args:
        uci: EUci pointer
        expand: expand the list with all IP addresses of the object
        used_info: include used and matches info

    Returns:
        a list of all DHCP static leases
    """
    leases = []
    for section in uci.get_all("dhcp"):
        lease = {}
        if uci.get('dhcp', section) == 'host':
            obj = uci.get_all('dhcp', section)
            lease['id'] = f"dhcp/{section}"
            lease['name'] = obj.get('name')
            lease['type'] = 'dhcp_static_lease'
            lease['subtype'] = 'dhcp_static_lease'
            lease['family'] = 'ipv4'
            if expand:
                lease['ipaddr'] = [obj.get('ip')]
            if used_info:
                used, matches = is_used_object(uci, f'dhcp/{section}')
                lease['used'] = used
                lease['matches'] = matches
            leases.append(lease)
    return leases

def list_dns_records(uci, expand=False, used_info=False):
    """
    Get all DNS records from dhcp config

    Args:
        uci: EUci pointer
        expand: expand the list with all IP addresses of the object
        used_info: include used and matches info

    Returns:
        a list of all DNS records
    """
    records = []
    for section in uci.get_all("dhcp"):
        record = {}
        if uci.get('dhcp', section) == 'domain':
            obj = uci.get_all('dhcp', section)
            record['id'] = f"dhcp/{section}"
            record['name'] = obj.get('name')
            record['type'] = 'dns_record'
            record['subtype'] = 'dns_record'
            record['family'] = 'ipv4'
            if expand:
                record['ipaddr'] = [obj.get('ip')]
            if used_info:
                used, matches = is_used_object(uci, f'dhcp/{section}')
                record['used'] = used
                record['matches'] = matches
            records.append(record)
    return records

def list_objects(uci, include_domain_sets=True, include_host_sets=True, singleton_only=False, expand=False):
    """
    Get objects from objects, dhcp, and users config

    Args:
        uci: EUci pointer
        include_domain_sets: include domain sets in the list
        include_host_sets: include host sets in the list
        expand: expand the list with all IP addresses of the object

    Returns:
        a list of all objects
    """
    hsets = []
    dsets = []
    if include_host_sets:
        for h in list_host_sets(uci, True):
            if singleton_only and not h['singleton']:
                continue
            h['id'] = f"objects/{h['id']}"
            h['type'] = 'host_set'
            if not expand:
                del[h['ipaddr']]
            hsets.append(h)

    if include_domain_sets:
        for d in list_domain_sets(uci, True):
            d['id'] = f"objects/{d['id']}"
            d['type'] = 'domain_set'
            d['subtype'] = 'domain_set'
            if not expand:
                del[d['domain']]
                del[d['timeout']]
            dsets.append(d)
    vpn_users = list_vpn_users(uci, expand, True)
    dhcp_static_leases = list_dhcp_static_leases(uci, expand, True)
    dns_records = list_dns_records(uci, expand, True)
    return hsets + dsets + vpn_users + dhcp_static_leases + dns_records

def get_info(uci, database_id):
    """
    Get the info of the object.

    Args:
        uci: EUci pointer
        database_id: id of the object in the form of `<database>/<id>`

    Returns:
        a dictionary with the following fields:

        - `database`: the database of the object
        - `id`: the id of the object
        - `name`: the name of the object
        - `type`: the type of the object
        - `family`: IP family, like `ipv4` or `ipv6`
    """
    try:
        database, id = database_id.split('/')
        type = uci.get(database, id)
        name = uci.get(database, id, 'name', default=None)
        family = uci.get(database, id, 'family', default='ipv4')
        if not name:
            name = uci.get(database, id, 'label', default=None)
            if not name:
                name = id
        return {'database': database, 'id': id, 'name': name, 'type': type, 'family': family}
    except:
        return None
        
