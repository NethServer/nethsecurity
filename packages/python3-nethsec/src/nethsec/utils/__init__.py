#!/usr/bin/python3

#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

'''
General utilities
'''

import os
import base64
import re
import json
import uuid
import hashlib
import subprocess

def get_random_id():
    '''
    Return a random valid UCI id.

    Random ids:
      - have a length of 11 characters
      - are sanitized accordingly to UCI conventions (see 'sanitize' function)
      - start with ns\_ prefix

    Arguments:
      - name -- the name of the section

    Returns:
      - a valid UCI identifier as string
    '''

    h = hashlib.new('sha1')
    h.update(uuid.uuid4().bytes)
    digest = h.hexdigest()
    return get_id(digest, 11)

def get_id(name, length = 100):
    '''
    Return a valid UCI id based on the given string.
    All auto-generated NethSecurity ids:

      - have a maximum length of 100 characters
      - start with ns\_ prefix
      - are sanitized accordingly to UCI conventions

    Arguments:
      - name -- the name of the section
      - length -- maximum id length, default is 100. Maximum length for firewall zones is 15.

    Returns:
      - a valid UCI identifier as string
    '''
    sname = f'ns_{sanitize(name)}'
    return sname[0:length]

def sanitize(name):
    '''
    Replace illegal chars with _ char.
    UCI identifiers and config file names may contain only the characters a-z, 0-9 and _

    Arguments:
      - name -- the name of the section
    
    Returns:
      - a string with valid chachars for UCI
    '''
    name = re.sub(r'[^\x00-\x7F]+','_', name)
    name = re.sub('[^0-9a-zA-Z]', '_', name)
    name = name.removesuffix('_')
    return name

def get_all_by_type(uci, config, utype):
    '''
    Return all sections of the given utype from the given config

    Arguments:
      - uci -- EUci pointer
      - config -- Configuration database name
      - utype -- Section type

    Returns:
      - A dictionary of all matched sections, None in case of error
    '''
    ret = dict()
    try:
        for section in uci.get(config):
            if uci.get(config, section) == utype:
                ret[section] = uci.get_all(config, section)
        return ret
    except:
        return None

def get_device_name(hwaddr):
    '''
    Retrieve the physical device name given the MAC address

    Aarguments:
      - hwaddr -- MAC address string

    Returns:
      - The device name as a string if the network interface has been found, None otherwise.
    '''
    try:
        interfaces = json.loads(subprocess.run(["/sbin/ip", "--json", "address", "show"], check=True, capture_output=True).stdout)
        for interface in interfaces:
            if interface["address"] == hwaddr:
                return interface["ifname"]
    except:
        return None

    return None

def get_interface_from_mac(uci, hwaddr):
    '''
    Retrieve the logical UCI interface name given the MAC address

    Arguments:
      - uci -- EUci pointer
      - hwaddr -- MAC address string

    Returns:
      - The device name as a string if the interface has been found, None otherwise
    '''
    device = get_device_name(hwaddr)
    return get_interface_from_device(uci, device)

def get_interface_from_device(uci, device):
    '''
    Retrieve the logical UCI interface name given the device name

    Arguments:
      - uci -- EUci pointer
      - device -- Device name

    Returns:
      - The device name as a string if the interface has been found, None otherwise
    '''
    for section in uci.get("network"):
        if uci.get("network", section) == "interface":
            try:
                proto = uci.get("network", section, 'proto')
            except:
                continue
            if proto == 'bonding' and section == device:
                return section
            if proto == 'pppoe' and section == device.removeprefix('pppoe-'):
                return section
            try:
                sdevice = uci.get("network", section, 'device')
            except:
                continue
            if proto != 'bonding' and device == sdevice:
                return section

    return None

def get_all_by_option(uci, config, option, value, deep = True):
    '''
    Return all sections with the given option value

    Arguments:
      - uci -- EUci pointer
      - config -- Configuration database name
      - option -- Option name
      - value -- Option value
      - deep - If true, return a dict of all matched keys, otherwise return a list of section names

    Returns:
      - A dictionary or a list of all matched sections
    '''
    ret = dict()
    for section in uci.get(config, list=True, default=[]):
        if uci.get(config, section, option, default='') == value:
            if deep:
                ret[section] = uci.get_all(config, section)
            else:
                ret[section] = 1
    if deep:
        return ret
    else:
        return list(ret.keys())


def get_all_devices_by_zone(uci, zone, exclude_aliases=False):
    '''
    Retrieve all devices associated to the given zone

    Arguments:
      - uci -- EUci pointer
      - zone -- Firewall zone name

    Returns:
      - A list of device names
    '''
    devices = []
    for section in uci.get("firewall"):
        if uci.get("firewall", section, default='') == 'zone' and uci.get("firewall", section, "name", default='') == zone:
            devices = devices + list(uci.get("firewall", section, "device", list=True, default=[]))
            networks = uci.get("firewall", section, "network", list=True, default=[])
            for network in networks:
                if uci.get('network', network, 'proto', default='') == 'wireguard':
                    devices.append(network)
                    continue
                device = uci.get("network", network, "device", default="")
                if exclude_aliases and device.startswith("@"):
                    continue
                if device != "":
                    devices.append(device)
                else:
                    name = uci.get("network", network, "name", default="")
                    if name != "":
                        devices.append(name)

    # remove duplicates
    return list(set(devices))


def get_all_wan_devices(uci, exclude_aliases=False):
    """
    Retrieve all devices associated to the wan zone

    Arguments:
      - uci -- EUci pointer
      - exclude_aliases -- If true, exclude devices starting with @

    Returns:
      - A list of device names
    """
    return get_all_devices_by_zone(uci, 'wan', exclude_aliases)


def get_all_lan_devices(uci):
    '''
    Retrieve all devices associated to the lan zone, except for VPN ones

    Arguments:
      - uci -- EUci pointer

    Returns:
      - A list of device names
    '''
     # exclude tun and ipsec devices
    return list(filter(lambda d: not d.startswith("ipsec") and not d.startswith("tun"),  get_all_devices_by_zone(uci, 'lan')))

def get_unassigned_devices(uci):
    '''
    Retrieve all unused/unassigned devices.

    Arguments:
      - uci -- EUci pointer

    Returns:
      - A list of devices
    '''
    unassigned = []
    try:
        p = subprocess.run(["ip", "-j", "link"], check=True, capture_output=True, text=True)
        devices = json.loads(p.stdout)
    except:
        return []

    u_interfaces = get_all_by_type(uci, 'network', 'interface')
    u_devices = get_all_by_type(uci, 'network', 'device')

    for ip_device in devices:
        free = True
        ifname = ip_device.get('ifname', '')
        # exclude special devices
        if not ifname or ifname == "lo" or ifname.startswith("ifb-"):
            continue
        # exclude tun devices and ppp devices
        if ip_device.get("link_type", "ether") == "none" or ip_device.get("link_type", "ether") == "ppp": 
            continue
        # skip bridged interfaces
        if not ip_device.get("master") is None:
            continue
        # search among UCI devices
        for d in u_devices:
            # ports are present on bridge devices
            try:
                ports = uci.get_all('network', d, 'ports')
            except:
                ports = []
            if uci.get('network', d, 'name', default="") == ifname or ifname in ports:
                free = False
        # search among UCI interfaces
        for i in u_interfaces:
            # slaves are present on bond devices
            slaves = []
            if uci.get('network', i, 'proto', default='') == 'bonding':
                slaves = list(uci.get_all('network', i, 'slaves'))
                # for bonds, the section name is the nmame of device with 'bond-' prefix
                slaves.append(f'bond-{i}')
            device = uci.get('network', i, 'device', default="")
            if device == ifname or ifname in slaves:
                free = False
        # search inside hotspot configuration
        if uci.get('dedalo', 'config', 'disabled', default="1") == "0" and uci.get('dedalo', 'config', 'interface', default="") == ifname:
            free = False
        if free:
            unassigned.append(ifname)

    # prepare list of devices used in bridges
    used = {}
    for d in u_devices:
        try:
            for p in uci.get_all('network', d, 'ports'):
                used[p] = 1
        except:
            pass
    # prepare list of devices used in bonds
    bonds = get_all_by_type(uci, 'network', 'interface')
    for b in bonds:
        try:
            for s in uci.get_all('network', b, 'slaves'):
                used[s] = 1
        except:
            pass

    used = list(used.keys())

    for d in u_devices:
        free = True
        d_name = uci.get('network', d, 'name', default=None)
        # skip a device which is already up and visibile inside ip command
        # check if the device is used inside and interface
        if get_interface_from_device(uci, d_name):
            continue
        # check if the device is used inside a zone
        for z in get_all_by_type(uci, 'firewall', 'zone'):
            try:
                z_devices = uci.get_all('firewall', z, 'device')
            except:
                z_devices = []
            try:
                z_networks = uci.get_all('firewall', z, 'network')
            except:
                z_networks = []
            if d_name in z_devices or d_name in z_networks or d_name in used:
                free = False
                continue
        if free:
            unassigned.append(d_name)
    return unassigned


def validation_errors(errors):
    '''
    Generate a validation error for the APIs from an array.

    Arguments:
      - errors -- An array of array errors

    Each array element is an array composed by 3 parameters:
      - the name of the parameter
      - the validation error reason
      - the parameter original value that caused the error

    Returns:
      - A validation error object
    '''
    verrors = []
    for e in errors:
        verrors.append({"parameter": e[0], "message": e[1].strip().replace(" ", "_").lower(), "value": e[2]})

    return {"validation": {"errors": verrors}}

def validation_error(parameter, message="", value=""):
    '''
    Generate a validation error for the APIs.

    Arguments:
      - parameter -- The name of the parameter
      - message -- The validation error reason, default is empty
      - value -- The parmeter original value that caused the error

    Returns:
      - A validation error object
    '''
    return validation_errors([[parameter, message, value]])

def generic_error(error):
    '''
    Generate a generic error for the APIs.

    Arguments:
      - message -- An error message
    Returns:
      - A validation error object
    '''
    return {"error": error.strip().replace(" ", "_").lower()}

def shadow_password(password):
    '''
    Generates a shadow password hash using SHA-512 algorithm.

    Arguments:
      - password (str) - the password to be hashed.

    Returns:
       - the shadow password hash as strin
    '''
    salt = base64.b64encode(os.urandom(12))
    phash = base64.b64encode(hashlib.pbkdf2_hmac('sha512', bytes(password, 'UTF-8'), salt, 200000))
    return f"$6${salt.decode('UTF-8')}${phash.decode('UTF-8')}"

def check_password(password, shadow):
    '''
    Check if the given password matches the given shadow password hash.

    Arguments:
      - password (str) - the password to be checked.
      - shadow (str) - the shadow password hash to be checked.

    Returns:
      - True if the password matches the hash, False otherwise
    '''
    (_, alg, salt, curhash) = shadow.split("$")
    phash = base64.b64encode(hashlib.pbkdf2_hmac('sha512', bytes(password, 'UTF-8'), salt.encode("UTF-8"), 200000))
    return phash.decode("UTF-8") == curhash

def get_user_by_username(uci, username):
    '''
    Retrieve the user object id (UCI section) given the username

    Arguments:
      - uci -- EUci pointer
      - username -- Username

    Returns:
      - The user object id (UCI section) if the user has been found, None otherwise
    '''
    users = get_all_by_type(uci, 'objects', 'user')
    for user in get_all_by_type(uci, "users", "user"):
        if users[user].get("username", "") == username:
            users[user]["id"] = user
            return users[user]
    return None

def get_all_device_ips():
    '''
    Retrieve all device IPs
    '''
    ret = {}
    p = subprocess.run(["/sbin/ip", "-j", "address"], check=True, text=True, capture_output=True)
    data = json.loads(p.stdout)
    for interface in data:
        ipaddr = []
        name = interface.get("ifname")
        for addr in interface.get("addr_info", []):
            if name not in ret:
                ret[name] = []
            ret[name].append(addr.get('local', ''))
    return ret


def get_all_wan_ips(uci):
    '''
    List all WAN interfaces with their IP addresses
    Exclude bond management IPs.

    Arguments:
      - uci -- EUci pointer

    Returns:
      - A list of dictionaries with device and IP address
    '''
    ret = []
    seen = set() # track seen devices to avoid duplicates
    ips = get_all_device_ips()
    wans = get_all_wan_devices(uci)
    # list configured static wans
    for wan in wans:
        interface = get_interface_from_device(uci, wan)
        if interface:
            try:
                ipaddrs = uci.get_all('network', interface, 'ipaddr')
            except:
                continue
            if type(ipaddrs) == str:
                ipaddrs = [(ipaddrs)]
            for ipaddr in ipaddrs:
                # skip bond management IPs
                if ipaddr.startswith("127"):
                    continue
                # strip mask to avoid duplicates
                if ipaddr and '/' in ipaddr:
                    ipaddr = ipaddr.split('/')[0]
                if ipaddr and ipaddr not in seen:
                    seen.add(ipaddr)
                    device = wan
                    if wan.startswith('@'):
                         device = uci.get('network', wan[1:], 'device', default='')
                    if device:
                        device = f'({device})'
                    ret.append({"device": f'{interface.replace("@","")} {device}', "ipaddr": ipaddr})
    # list on-line wans, search also for dynamic IPs
    for device in ips.keys():
        if device in wans or device.startswith('pppoe'):
            for ip in ips[device]:
                # skip bond management IPs
                if ip.startswith("127"):
                    continue
                if ip not in seen:
                    seen.add(ip)
                    if device.startswith('pppoe-'):
                        interface = device.removeprefix('pppoe-')
                    else:
                        interface = get_interface_from_device(uci, device)
                    if interface:
                        ret.append({"device": f'{interface.replace("@","")} ({device})', "ipaddr": ip})

    return sorted(ret, key=lambda k: k['ipaddr'])


def get_public_ip_addresses(ip_address=""):
    """
    Return the public addresses associated to a private IP address.

    Arguments:
      - ip_address -- the private IP address of a network interface. If not specified, the default network interface is used.

    Returns:
      - a list of public addresses. Usually, the list contains only one element.
    """
    try:
        bindOption = ""
        if ip_address:
            bindOption = f" -b {ip_address}"

        cmd = f"/usr/bin/dig{bindOption} +short +time=1 myip.opendns.com @resolver1.opendns.com".split(" ")
        output = subprocess.check_output(cmd, timeout=5)
        public_ip_addresses = output.decode().strip().split('\n')

        if public_ip_addresses[0] == "":
            # cannot retrieve public IP address, returning input IP address as fallback
            if ip_address:
                return [ip_address]
            else:
                return []
        else:
            return public_ip_addresses
    except Exception as e:
        return []


class ValidationError(ValueError):
    def __init__(self, parameter, message="", value=""):
        self.parameter = parameter
        self.message = message
        self.value = value
