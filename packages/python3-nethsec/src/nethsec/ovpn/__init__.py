#!/usr/bin/python3

#
# Copyright (C) 2023 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""
Library for common VPN functions.
"""

import json
import ipaddress
import random
import struct
import socket
import subprocess
from nethsec import utils

def get_local_networks(u):
    """
    Return a list of local networks.

    Arguments:
      - u -- EUci instance

    Returns:
      - a list of local networks
    """
    ret = set()
    for l in utils.get_all_lan_devices(u):
        try:
            data = json.loads(subprocess.run(["ip", "--json", "address", "show", "dev", l], capture_output=True, text=True, check=True).stdout)
            if len(data) > 0:
                for addr in data[0].get('addr_info', []):
                    if addr.get("local", None) and addr.get("family", None) == "inet": # ipv4 only
                        # skip bond management address
                        if addr.get("local").startswith("127"):
                            continue
                        net = ipaddress.ip_interface(f'{addr.get("local")}/{addr.get("prefixlen")}').network
                        ret.add(f'{net}')
        except:
            continue
    return list(ret)

def get_public_addresses(u):
    """
    Return a list of public addresses.

    Arguments:
      - u -- EUci instance

    Returns:
      - a list of public addresses
    """
    ret = {}
    for w in utils.get_all_wan_devices(u):
        try:
             data = json.loads(subprocess.run(["ip", "--json", "address", "show", "dev", w], capture_output=True, text=True, check=True).stdout)
        except:
            continue
        if len(data) > 0:
            for addr in data[0].get('addr_info', []):
                if addr.get("local", None):
                    try:
                        res = subprocess.run([
                            "/usr/bin/dig",
                            "-b",
                            addr.get("local"),
                            "+short",
                            "+time=1",
                            "myip.opendns.com",
                            "@resolver1.opendns.com"
                        ],
                        capture_output=True, text=True, check=True)
                        ret[res.stdout.strip()] = 1
                    except:
                        pass
    return list(ret.keys())

def to_cidr(netmask):
    """
    Convert a netmask to CIDR notation.

    Arguments:
      - netmask -- netmask in dotted decimal notation

    Returns:
      - CIDR notation

    """
    return sum([bin(int(x)).count('1') for x in netmask.split('.')])

def to_netmask(prefix):
    """
    Convert a CIDR notation to netmask.

    Arguments:
      - prefix -- CIDR notation

    Returns:
      - netmask in dotted decimal notation
    """
    return socket.inet_ntoa(struct.pack(">I", (0xffffffff << (32 - int(prefix))) & 0xffffffff))

def generate_random_network(u):
    """
    Generate a random network.

    Arguments:
      - u -- EUci instance

    Returns:
     - a random unused network
    """
    network = random_network()
    while is_used_network(u, network):
        network = random_network()
    return network

def random_network():
    """
    Generate a random private network address.

    Returns:
      - a random private network address
    """
    return f"10.{random.randint(0, 254)}.{random.randint(0, 254)}.0/24"

def is_used_network(u, network):
    """
    Check if a network is already used by another OpenVPN.

    Arguments:
      - u -- EUci instance
      - network -- network to check

    Returns:
      - True if the network is already used, False otherwise
    """
    try:
        openvpn = u.get_all('openvpn')
    except:
        return False

    for v in openvpn:
        ifconfig = u.get('openvpn', v, 'ifconfig', default="")
        if ifconfig:
            ifnet = f'{ifconfig.split(" ")[0]}/24' # assume /24
            if ipaddress.ip_network(ifnet, strict=False) == ipaddress.ip_network(network):
                return True

        server = opt2cidr(u.get('openvpn', v, 'server', default=""))
        if server and server == network:
            return True

        server_bridge = opt2cidr(u.get('openvpn', v, 'server_bridge', default=""))
        if server_bridge:
            if ipaddress.ip_network(server_bridge, strict=False) == ipaddress.ip_network(network):
                return True
    return False

def opt2cidr(opt):
    """
    Convert an OpenVPN option to CIDR notation.

    Arguments:
      - opt -- OpenVPN option

    Returns:
      - CIDR notation
    """
    try:
        tmp = opt.split(" ")
        return f'{tmp[0]}/{to_cidr(tmp[1])}'
    except:
        return ""
    

def list_cipher():
    """
    Return a list of OpenVPN ciphers.

    Returns:
      - a list of OpenVPN ciphers, each element is a dicttionary with the following keys:
          - name: cipher name
          - description: cipher description (weak or strong)
    """
    ret = []
    try:
        result = subprocess.run(['/usr/sbin/openvpn', '--show-ciphers'], capture_output=True, text=True, check=True)
        output_lines = result.stdout.splitlines()

        for line in output_lines:
            if '(' in line:
                description = 'weak'
                tmp = line.split()
                cipher_name = tmp[0]
                try:
                    bits = int(cipher_name.split("-")[1])
                except:
                    bits = 0
                if bits in [192, 256, 384, 512]:
                    description = 'strong'
                ret.append({'name': cipher_name, 'description': description})
    except:
        return {"ciphers": []}
    return {"ciphers": ret}

def list_digest():
    """
    Return a list of OpenVPN digests.

    Returns:
      - a list of OpenVPN digests, each element is a dicttionary with the following keys:
        - name: digest name
        - description: digest description (weak or strong)
    """
    ret = []
    try:
        result = subprocess.run(['/usr/sbin/openvpn', '--show-digests'], capture_output=True, text=True, check=True)
        output_lines = result.stdout.splitlines()

        for line in output_lines:
            if 'bit' in line:
                description = 'weak'
                tmp = line.split()
                if tmp[1] in ['224', '256', '384', '512', 'whirlpool']:
                    description = 'strong'
                ret.append({'name': tmp[0], 'description': description})
    except:
        return {"digests": []}
    return {"digests": ret}

def generate_random_port(uci, limit_min, limit_max):
    '''
    Generate a random port.

    Arguments:
        - uci -- EUci instance
        - limit_min -- minimum port number
        - limit_max -- maximum port number

    Returns:
        - a random port number
    '''
    port = random.randint(limit_min, limit_max)
    while is_used_port(uci, port):
        port = random.randint(limit_min, limit_max)
    return port

def is_used_port(uci, port):
    '''
    Check if a port is already used by another OpenVPN.

    Arguments:
        - uci -- EUci instance
        - port -- port to check

    Returns:
        - True if the port is already used, False otherwise
    '''
    for v in uci.get_all('openvpn'):
        rport = int(uci.get('openvpn', v, 'port', default="0"))
        lport = int(uci.get('openvpn', v, 'lport', default="0"))
        if port == rport or port == lport:
            return True
    return False

def list_connected_clients(openvpninstance, type="subnet"):
    """
    List connected clients.

    Arguments:
        - openvpninstance -- OpenVPN instance name
        - type -- type of list (subnet or p2p)

    Returns:
        - a list of connected clients
    """
    try:
        p = subprocess.run(["/usr/bin/openvpn-status", "-t", type, f"/var/run/openvpn_{openvpninstance}.socket"], check=True, capture_output=True, text=True)
    except:
        return {}
    return json.loads(p.stdout)
