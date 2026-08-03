#!/usr/bin/python3

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#


from math import floor
from euci import EUci
from nethsec import utils, mwan, users, firewall, objects
import os
import re
import csv
import subprocess
import configparser
import json
import hashlib
from socket import inet_ntoa
from struct import pack

APK_WORLD = '/etc/apk/world'
APK_WORLD_BASE = '/rom/etc/apk/world'

## Utilities

def _run(cmd):
    try:
        proc = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return proc.stdout.rstrip().lstrip()
    except:
        return ''

def _run_status(cmd):
    try:
        proc = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return proc.returncode
    except:
        return 1

def _run_json(cmd):
    try:
        return json.loads(_run(cmd))
    except:
        return {}

def _get_role(uci: EUci, interface):
    for zone in utils.get_all_by_type(uci, 'firewall', 'zone'):
        name = uci.get('firewall', zone, 'name')
        networks = uci.get('firewall', zone, 'network', list=True, default=[])
        if interface in networks:
            if name == "lan":
                return "green"
            elif name == "wan":
                return "red"
            else:
                return name

def _get_ip(interface, uci: EUci):
    info = _run_json(f"ifstatus {interface}")
    try:
        return anonymize(info['ipv4-address'][0]['address'], uci)
    except:
        return ''

def _get_mask(interface):
    info = _run_json(f"ifstatus {interface}")
    try:
        m =  info['ipv4-address'][0]['mask']
        bits = 0xffffffff ^ (1 << 32 - int(m)) - 1
        mask = inet_ntoa(pack(">I", bits))
        return mask
    except:
        return ''

def _get_gateway(interface, uci: EUci):
    info = _run_json(f"ifstatus {interface}")
    try:
        for r in info['route']:
            if r['target'] == '0.0.0.0':
                return anonymize(r['nexthop'], uci)
    except:
        return ''

def _get_cpu_field(field, cpu_info):
    for f in cpu_info:
        if f['field'].startswith(field):
            return f['data']

    return ''

def _read_apk_world(path):
    names = set()
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('!'):
                    continue
                name = re.split(r'[<>=~]', line, maxsplit=1)[0].strip()
                if name:
                    names.add(name)
    except:
        pass
    return names

def anonymize(value, uci: EUci):
    if fact_subscription_status(uci).get('status', 'no') != "no":
        return value
    h = hashlib.sha256(value.encode()).hexdigest()
    return f"anon-{h[:16]}"

def parse_version(version_str):
    # Remove "NethSecurity " prefix if present
    if version_str.startswith('NethSecurity '):
        version_str = version_str[13:]  # len('NethSecurity ') = 13
    # Take only the part before "-"
    version_str = version_str.split('-')[0]
    # Convert to tuple of integers for comparison
    try:
        return tuple(int(x) for x in version_str.split('.'))
    except (ValueError, AttributeError):
        return ()

def get_networks(uci: EUci):
    networks = {}
    devices = utils.get_all_by_type(uci, 'network', 'device')
    for section in utils.get_all_by_type(uci, 'network', 'interface'):
        if section == "lan6" or section == "wan6": # skip IPv6 for now
            continue
        interface = uci.get_all('network', section)
        device = interface.get("device")
        if not device or device == "lo" or device.startswith("ipsec") or device.startswith("tun"):
            continue
        network = {"type": "ethernet", "name": device, "props": { "role": _get_role(uci, section), "ipaddr": _get_ip(section, uci), "netmask": _get_mask(section), "gateway": _get_gateway(section, uci)}}
        # get bridge ports, exclude vlans over bridges
        is_vlan = bool(re.search(r'\.\d+$', interface['device'])) # check if the device name ends with .<number>
        if interface['device'].startswith('br') and not is_vlan:
            network["type"] = "bridge"
            for d in devices:
                if uci.get('network', d, 'name') == device:
                    network['props']["bridge"] = uci.get('network', d, 'ports', default=[])
        networks[device] = network
    return networks

def get_version():
    version = ""
    with open('/etc/os-release', 'r') as file:
        for line in file:
            if line.startswith("VERSION_ID="):
                version = line.split('=')[1].replace('"','').rstrip()
                break
    return version

def get_product():
    product = ""
    try:
        with open('/sys/devices/virtual/dmi/id/product_name', 'r') as f:
            product = f.read().strip()
    except:
        pass
    if not product:
        try:
            with open('/etc/board.json', 'r') as f:
                binfo = json.load(f)
            product = binfo['model']['name']
        except:
            product = ""
    return product

def is_virtual():
    cpu_info = _run_json('lscpu -J')['lscpu']
    return _get_cpu_field("Hypervisor vendor", cpu_info) if _get_cpu_field("Hypervisor vendor", cpu_info) else 'physical'

def get_cpu_info():
    cpu_info = _run_json('lscpu -J')['lscpu']
    return {
        "model": _get_cpu_field("Model name", cpu_info),
        "architecture": _get_cpu_field("Architecture", cpu_info)
    }

def get_pci_info():
    # map kernel driver to device id
    drivers = {}
    for line in _run("find /sys | grep '.*/drivers/.*/0000:.*$' | cut -d'/' -f6,7").split('\n'):
        try:
            (driver,bus) = line.split("/0000:")
            drivers[bus] = driver
        except:
            continue

    # lspci -n: 00:1b.0 0403: 8086:293e (rev 03)
    # fields:   bus class vendor:device revision
    pci = {}
    if os.path.isdir('/proc/bus/pci'):
        for line in _run("lspci -n").split("\n"):
            revision = ''
            fields = line.split(" ", maxsplit=4)
            (vendor, device) = fields[2].split(":")
            if len(fields) > 3:
                revision = fields[4]
            pci[fields[0]] = {"class_id": fields[1].rstrip(":"), "vendor_id": vendor, "device_id": device, "revision": revision.strip(')')}

        # lspci -mm: 00:00.0 "Host bridge" "Intel Corporation" "82G33/G31/P35/P31 Express DRAM Controller" -p00 "Red Hat, Inc." "QEMU Virtual Machine"
        for fields in csv.reader(_run("lspci -mm").split("\n"), delimiter=' ', quotechar='"'):
            pci[fields[0]]['class_name'] = fields[1].strip('"')
            pci[fields[0]]['vendor_name'] = fields[2]
            pci[fields[0]]['device_name'] = fields[3]
            pci[fields[0]]['driver'] =  drivers.get(fields[0], '')
    return pci

def get_memory():
    result = {}
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().split()[0]  # Get the number, skip the unit (kB)
                    result[key] = int(value) * 1024  # Convert from kB to bytes
    except:
        pass
    if result:
        result["MemUsed"] = result.get('MemTotal', 0) - result.get('MemFree', 0) - result.get('Buffers', 0) - result.get('Cached', 0)
        result["SwapUsed"] = result.get('SwapTotal', 0) - result.get('SwapFree', 0)
    return result

def get_mount_points():
    result = {}
    exclude_mounts = {'/rom', '/overlay', '/dev'}
    seen_mounts = set()

    try:
        output = _run("df -P")
        lines = output.strip().split('\n')
        # Skip header line
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 6:
                mount_point = parts[5]
                # Skip excluded mount points
                if mount_point in exclude_mounts:
                    continue
                # Skip duplicates (keep first occurrence)
                if mount_point in seen_mounts:
                    continue
                try:
                    total = int(parts[1]) * 1024  # Convert from 1K blocks to bytes
                    used = int(parts[2]) * 1024
                    available = int(parts[3]) * 1024
                    result[mount_point] = {
                        'total_bytes': total,
                        'used_bytes': used,
                        'available_bytes': available
                    }
                    seen_mounts.add(mount_point)
                except (ValueError, IndexError):
                    continue
    except:
        pass

    return result

## Facts
## These functions are used to send info about system to legacy my.nethesis.it
## The format should not be changed until legacy my.nethesis.it is alive

def fact_hotspot(uci: EUci):
    enabled = uci.get('dedalo', 'config', 'disabled', default='1') == '0'
    server = uci.get('dedalo', 'config', 'api_url', default='')
    interface = uci.get('dedalo', 'config', 'interface', default='')
    return { 'enabled': enabled, 'server': server, 'interface': interface }

def fact_netifyd(uci: EUci):
    try:
        config = configparser.ConfigParser()
        config.read('/etc/netifyd.conf')
        enable_sink = config.get('netifyd', 'enable_sink')
    except:
        enable_sink = 'no'
    return { 'enabled': enable_sink == 'yes' }

def fact_flashstart(uci: EUci):
    enabled = uci.get('flashstart', 'global', 'enabled', default='0') == '1'
    bypass = len(uci.get('flashstart', 'global', 'bypass', list=True, default=[]))
    pro_plus = uci.get('flashstart', 'global', 'proplus', dtype=bool, default=False)
    custom_servers = len(uci.get('flashstart', 'global', 'custom_servers', list=True, default=[]))
    return { 'enabled': enabled, 'bypass': bypass, 'pro_plus': pro_plus, 'custom_servers': custom_servers }

def fact_openvpn_rw(uci: EUci):
    ret = { 'enabled': 0, 'server': 0, 'instances': [] }
    for section in utils.get_all_by_type(uci, 'openvpn', 'openvpn'):
        if uci.get("openvpn", section, 'ns_auth_mode', default=''):
            ret["server"] += 1
            if uci.get("openvpn", section, 'enabled', default='0') == '1':
                ret["enabled"] += 1 
    for section in utils.get_all_by_type(uci, 'openvpn', 'openvpn'):
        vpn = uci.get_all("openvpn", section)
        if not section.startswith('ns_'):
            continue
        if "ns_auth_mode" in vpn:
            # we are in a ovpn_rw
            instance = {
                'section': section,
                'authentication': vpn.get('ns_auth_mode'),
                'user_database': vpn.get('ns_user_db'),
                'mode': vpn.get('dev_type')
            }
            ret['instances'].append(instance)
    return ret

def fact_openvpn_tun(uci: EUci):
    ret = { 'client': 0, 'server': 0, 'tunnels': [] }
    for section in utils.get_all_by_type(uci, 'openvpn', 'openvpn'):
        vpn = uci.get_all("openvpn", section)
        if 'ns_auth_mode' in vpn or not section.startswith('ns_'):
            continue
        if vpn.get("client", "0") == "1" or vpn.get("ns_client", "0") == "1":
            ret["client"] += 1
        else:
            ret["server"] += 1
        instance = {
            'section': section,
            'mode': vpn.get('dev_type')
        }
        ret['tunnels'].append(instance)
    return ret

def fact_certificates_info(uci: EUci):
    result = {
        "custom_certificates": {
            "count": 0
        },
        "acme_certificates": {
            "count": 0,
            "issued": 0,
            "pending": 0
        }
    }
    
    # Count custom certificates
    try:
        for entry in os.scandir('/etc/nginx/custom_certs'):
            if entry.is_file() and entry.name.endswith('.crt') and os.path.isfile(entry.path[:-4] + '.key'):
                result["custom_certificates"]["count"] += 1
    except Exception as e:
        # Handle exceptions appropriately
        pass

    # Count ACME certificates
    try:
        requested_certificates = utils.get_all_by_type(uci, 'acme', 'cert')
        enabled_certificates = [certificate for certificate in requested_certificates
                                if requested_certificates[certificate]['enabled'] == '1']
        for certificate in enabled_certificates:
            result["acme_certificates"]["count"] += 1
            domain = requested_certificates[certificate]['domains'][0]
            cert_path = f'/etc/ssl/acme/{domain}.fullchain.crt'
            if os.path.isfile(cert_path):
                result["acme_certificates"]["issued"] += 1
            else:
                result["acme_certificates"]["pending"] += 1
    except Exception as e:
        # Handle exceptions appropriately
        pass

    return result

def fact_subscription_status(uci: EUci):
    return { 'status': uci.get('ns-plug', 'config', 'type', default='no') }

def fact_controller(uci: EUci):
    if uci.get('ns-plug', 'config', 'server', default='') and uci.get('ns-plug', 'config', 'unit_id', default='') and uci.get('ns-plug', 'config', 'token', default=''):
        return { "enabled": True}
    else:
        return { "enabled": False}

def fact_rpcd_users(uci: EUci):
    count = 0
    for section, options in (utils.get_all_by_type(uci, 'rpcd', 'login') or {}).items():
        # skip root and the controller user (controller has a random username)
        if options.get('username') == 'root' or section == 'controller':
            continue
        count += 1
    return { 'count': count }

def fact_threat_shield(uci: EUci):
    ret = { 'enabled': False, 'community': 0, 'enterprise': 0 }
    ret['enabled'] = uci.get('banip', 'global', 'ban_enabled', default='0') == '1'
    try:
        for feed in uci.get_all("banip", "global", "ban_feed"):
            if feed.startswith("nethesis") or feed.startswith("yoroi"):
                ret['enterprise'] += 1
            else:
                ret['community'] += 1
    except:
        pass
    return ret

def fact_adblock(uci: EUci):
    ret = { 'enabled': False, 'community': 0, 'enterprise': 0 }
    ret['enabled'] = uci.get('adblock', 'global', 'ts_enabled', default='0') == '1'
    try:
        enabled_feeds = list(uci.get_all('adblock', 'global', 'adb_sources'))
    except:
        enabled_feeds = []
    for feed in enabled_feeds:
        if feed.startswith("nethesis") or feed.startswith("yoroi"):
            ret['enterprise'] += 1
        else:
            ret['community'] += 1
    return ret

def fact_ui(uci: EUci):
    ret = { 'luci': False, 'port443': False, 'port9090': False }
    ret['luci'] = uci.get('ns-ui', 'config', 'luci_enable', default='0') == '1'
    ret['port443'] = uci.get('ns-ui', 'config', 'nsui_enable', default='0') == '1'
    ret['port9090'] = uci.get('ns-ui', 'config', 'nsui_extra_enable', default='0') == '1' and uci.get('ns-ui', 'config', 'nsui_extra_port', default='0') == '9090'
    return ret

def fact_network(uci: EUci):
    result: dict = {
        "zones": []
    }
    vlan_count = 0
    bridge_count = 0
    bond_count = 0
    zone_network_counts = {}
    route_info = {
        "count_ipv6_route": 0,
        "count_ipv4_route": 0
    }
    # Regex pattern to match interfaces that end with ".<integer>"
    vlan_pattern = re.compile(r'\.\d+$')
    interfaces = utils.get_all_by_type(uci, 'network', 'interface')

    # Loop through all firewall zones to gather network information
    for zone in utils.get_all_by_type(uci, 'firewall', 'zone').values():
        zone_info = {
                'name': zone['name'],
                'ipv4': 0,
                'ipv6': 0
            }
        devices = utils.get_all_devices_by_zone(uci, zone['name'], True)
        for device in devices:
            interface = utils.get_interface_from_device(uci, device)
            if interface is None:
                continue
            is_ipv6 = False
            for option in uci.get_all('network', interface):
                if option.startswith("ip6") or option == "dhcpv6" or option == "ipv6":
                    is_ipv6 = True
                    break
            if uci.get('network', interface, 'proto', default="") in ['dhcpv6', '6in4', '6to4', '6rd', 'grev6', 'grev6tap', 'vtiv6']:
                is_ipv6 = True
            if is_ipv6:
                zone_info['ipv6'] += 1
            else:
                zone_info['ipv4'] += 1
            # Count VLAN, bridge, and bond interfaces
            if 'device' in interfaces.get(interface, {}):
                device_name = interfaces[interface]['device']
                if vlan_pattern.search(device_name):
                    vlan_count += 1
                if device_name.startswith('br-'):
                    bridge_count += 1
                if device_name.startswith('bond-'):
                    bond_count += 1
        result["zones"].append(zone_info)
        # Count networks for each zone
        networks = uci.get('firewall', 'ns_'+zone['name'], 'network', list=True, default=[])
        network_count = len(networks)
        # Count devices for each zone (if networks are not defined, hotspot zones, openvpn zones, etc.)
        devices = utils.get_all_devices_by_zone(uci, zone['name'], True)
        # remove tun-dedalo if present (it's a virtual device, we count the real interface
        devices = [d for d in devices if not d.startswith('tun-dedalo')]
        devices_count = len(devices)
        zone_network_counts[zone['name']] = network_count or devices_count # Use the number of networks if available, otherwise use the number of devices
    # Get route information
    routes_ipv6 = utils.get_all_by_type(uci, 'network', 'route6')
    for _ in routes_ipv6:
        route_info["count_ipv6_route"] += 1

    routes_ipv4 = utils.get_all_by_type(uci, 'network', 'route')
    for _ in routes_ipv4:
        route_info["count_ipv4_route"] += 1

    # Add VLAN, bridge, and bond counts to the result
    result['interface_counts'] = {
        'vlans': vlan_count,
        'bridges': bridge_count,
        'bonds': bond_count
    }
    # Add network zone counts to the result
    result['zone_network_counts'] = zone_network_counts

    # Add route information to the result
    result['route_info'] = route_info

    result['configuration'] = get_networks(uci)

    return result

def fact_database_stats(uci: EUci):
    ret = {}
    databases = users.list_databases(uci)
    for db in databases:
        name = db["name"]
        number_users = len(users.list_users(uci, name))
        ret[name] = { "users": number_users }
    return ret

def fact_firewall_stats(uci: EUci):
    result = {
        "firewall": {
            "port_forward": 0,
            "nat": {"masquerade": 0, "snat": 0, "accept": 0},
            "netmap": {"source": 0, "destination": 0},
            "rules": {"forward": 0, "input": 0, "output": 0}
        },
        "objects": {
            "domains": 0,
            "hosts": 0,
            "port_forward": {"allowed_from": 0, "destination_to": 0},
            "mwan_rules": 0,
            "rules": {"forward": 0, "input": 0, "output": 0}
        }
    }

    # Firewall Information
    # Count port forward
    result["firewall"]["port_forward"] = len(utils.get_all_by_type(uci, 'firewall', 'redirect'))

    # Count NAT rules
    for rule in firewall.list_nat_rules(uci):
        if rule['target'] == 'ACCEPT':
            result["firewall"]["nat"]["accept"] += 1
        elif rule['target'] == 'MASQUERADE':
            result["firewall"]["nat"]["masquerade"] += 1
        elif rule['target'] == 'SNAT':
            result["firewall"]["nat"]["snat"] += 1

    # Count netmap rules
    for rule in firewall.list_netmap_rules(uci):
        if rule.get('dest', ''):
            result["firewall"]["netmap"]["source"] += 1
        elif rule.get('src', ''):
            result["firewall"]["netmap"]["destination"] += 1

    # Count rules
    result["firewall"]["rules"]["forward"] = len(firewall.list_forward_rules(uci))
    result["firewall"]["rules"]["input"] = len(firewall.list_input_rules(uci))
    result["firewall"]["rules"]["output"] = len(firewall.list_output_rules(uci))

    # Object Information
    # Count objects
    result["objects"]["domains"] = len(objects.list_domain_sets(uci))
    result["objects"]["hosts"] = len(objects.list_host_sets(uci))

    # Count object for port forward
    for key, value in utils.get_all_by_type(uci, 'firewall', 'redirect').items():
        if isinstance(value.get('ns_src'), str):
            result["objects"]["port_forward"]["allowed_from"] += 1
        if isinstance(value.get('ns_dst'), str):
            result["objects"]["port_forward"]["destination_to"] += 1

    # Count object for rules
    for value in firewall.list_forward_rules(uci):
        if isinstance(value.get('ns_dst'), str):
            result["objects"]["rules"]["forward"] += 1
    for value in firewall.list_input_rules(uci):
        if isinstance(value.get('ns_src'), str):
            result["objects"]["rules"]["input"] += 1
    for value in firewall.list_output_rules(uci):
        if isinstance(value.get('ns_dst'), str):
            result["objects"]["rules"]["output"] += 1
    for value in mwan.index_rules(uci):
        if isinstance(value.get('ns_src'), str):
            result["objects"]["mwan_rules"] += 1

    return result

def fact_storage(uci: EUci):
    return {"enabled": uci.get("fstab", "ns_data", "enabled", default="0") == "1"}

def fact_clm(uci: EUci):
    return {"enabled": uci.get("ns-clm", "config", "enabled", default="0") == "1"}

def fact_proxy_pass(uci: EUci):
    ret = { "count": 0}
    try:
        for l in utils.get_all_by_type(uci, 'nginx', 'location'):
            if uci.get('nginx', l, 'proxy_pass', default=''):
                ret["count"] += 1
    except:
        pass
    return ret

def fact_dpi(uci: EUci):
    ret = {"enabled": False, "rules": 0}
    ret["enabled"] = uci.get('dpi', 'config', 'enabled', default='0') == '1'
    for rule in utils.get_all_by_type(uci, 'dpi', 'rule'):
        if uci.get('dpi', rule, 'enabled', default='0') == '1':
            ret["rules"] += 1
    return ret

def fact_extra_packages(uci: EUci):
    """
    List the packages installed by the administrator on top of the base image.

    The base image package set is read from /rom/etc/apk/world, the read-only
    squashfs lower layer, while the current one is read from /etc/apk/world.
    Since 'apk add <pkg>' appends only <pkg> itself, and not its dependencies,
    the difference between the two files is the set of packages explicitly
    installed after the image was built.
    If the base world file is missing or unreadable, no package is reported:
    this avoids reporting the whole world as administrator-installed.

    Arguments:
      - uci -- EUci pointer, unused, kept for consistency with other facts

    Returns:
      - a dictionary with the following keys:
        - count -- number of extra packages
        - packages -- sorted list of extra package names
    """
    base = _read_apk_world(APK_WORLD_BASE)
    current = _read_apk_world(APK_WORLD)
    extras = sorted(current - base) if base else []
    return {'count': len(extras), 'packages': extras}

def fact_dhcp_server(uci: EUci):
    result = {
        'count': 0,  # Initialize the count for DHCP servers
        'static_leases': 0, 
        'dynamic_leases': 0, 
        'dns_records_count': 0, 
        'dns_forwarder_enabled': False
    }

    # Count DHCP servers
    for section in utils.get_all_by_type(uci, 'dhcp', 'dhcp'):
        if uci.get('dhcp', section, 'dhcpv4', default='') == 'server' or uci.get('dhcp', section, 'dhcpv6', default='') == 'server':
            result['count'] += 1  # Increment the count for DHCP servers
    
    # Count static leases
    result['static_leases'] = len(utils.get_all_by_type(uci, 'dhcp', 'host'))
    
    static_leases = []
    for l in utils.get_all_by_type(uci, 'dhcp', 'host'):
        ldata = uci.get_all('dhcp', l)
        if 'mac' in ldata and 'ip' in ldata:
            static_leases.append(ldata['mac'].lower())

    # Count dynamic leases, skipping static leases
    try:
        with open("/tmp/dhcp.leases", "r") as fp:
            for line in fp.readlines():
                tmp = line.split(" ")
                if tmp[1].lower() not in static_leases:
                    result['dynamic_leases'] += 1
    except FileNotFoundError:
        # Handle the case where the leases file doesn't exist
        pass

    # Count DNS records and check if DNS forwarder is enabled
    for section in utils.get_all_by_type(uci, 'dhcp', 'dnsmasq'):
        servers = uci.get('dhcp', section, 'server', default=[])
        if servers:
            result['dns_forwarder_enabled'] = True
        for r in utils.get_all_by_type(uci, 'dhcp', 'domain'):
            result['dns_records_count'] += 1
    
    return result

def fact_multiwan(uci: EUci):
    policies = mwan.index_policies(uci)
    result = {
        'enabled': len(policies) > 0,
        'policies': {
            'backup': 0,
            'balance': 0,
            'custom': 0
        },
        'rules': len(mwan.index_rules(uci))
    }
    for policy in policies:
        result['policies'][policy['type']] += 1
    return result

def fact_qos(uci: EUci):
    ret = {
        "count": 0,
        "rules": []
    }
    for key, interface in utils.get_all_by_type(uci, 'qosify', 'interface').items():
        if interface['disabled'] == '0':
            ret["count"] += 1
            rule = {
                'enabled': interface['disabled'] == '0',
                'upload': int(interface['bandwidth_up'].removesuffix('mbit')),
                'download': int(interface['bandwidth_down'].removesuffix('mbit')),
            }
            ret['rules'].append(rule)
    return ret

def fact_ipsec(uci: EUci):
    try:
        count = len(utils.get_all_by_type(uci, 'ipsec', 'remote'))
    except:
        count = -1
    return { 'count': count }

def fact_nathelpers(uci: EUci):
    # count the number of lines in the file
    try:
        with open('/etc/modules.d/ns-nathelpers') as f:
            count = len(f.readlines())
    except:
        count = 0
    return { 'count': count, 'enabled': count > 0 }

def fact_ddns(uci: EUci):
    ddns = _run_status("/etc/init.d/ddns enabled")
    return { 'enabled': ddns == 0 }

def fact_snmp (uci: EUci):
    snmp = _run_status("/etc/init.d/snmpd running")
    return { 'enabled': snmp == 0 }

def fact_wireguard(uci: EUci):
    servers = dict()
    interfaces = utils.get_all_by_type(uci, "network", "interface")
    for i in interfaces:
        if interfaces[i].get("proto", "") != "wireguard":
            continue
        peers = utils.get_all_by_type(uci, 'network', f'wireguard_{i}')
        routing_all_traffic = 0
        for peer in peers:
            if uci.get('network', peer, 'ns_route_all_traffic', dtype=bool, default=False):
                routing_all_traffic += 1
        servers[i] = {
            "peers": len(peers),
            "routing_all_traffic": routing_all_traffic
        }

    return {
        "enabled": len(servers) > 0,
        "servers": servers
    }


def fact_snort(uci: EUci):
    ret = { 'enabled': False, 'policy': '', 'oink_enabled': False, 'disabled_rules': 0, 'suppressed_rules': 0, 'bypass_src_ipv4': 0, 'bypass_src_ipv6': 0, 'bypass_dst_ipv4': 0, 'bypass_dst_ipv6': 0 }

    ret['enabled'] = uci.get('snort', 'snort', 'enabled', dtype=bool, default=False)
    ret['policy'] = uci.get('snort', 'snort', 'ns_policy', default='')
    ret['oink_enabled'] = True if uci.get('snort', 'snort', 'oinkcode', default='') else False

    # count list of ns_disabled_rules
    ret['disabled_rules'] = len(uci.get('snort', 'snort', 'ns_disabled_rules', list=True, default=[]))
    # count list of ns_suppress rules
    ret['suppressed_rules'] = len(uci.get('snort', 'snort', 'ns_suppress', list=True, default=[]))
    # count the source bypass of ipv4 and ipv6
    ret['bypass_src_ipv4'] = len(uci.get('snort', 'nfq', 'bypass_src_v4', list=True, default=[]))
    ret['bypass_src_ipv6'] = len(uci.get('snort', 'nfq', 'bypass_src_v6', list=True, default=[]))
    ## count the destination bypass_dst_v4 and bypass_dst_ipv6
    ret['bypass_dst_ipv4'] = len(uci.get('snort', 'nfq', 'bypass_dst_v4', list=True, default=[]))
    ret['bypass_dst_ipv6'] = len(uci.get('snort', 'nfq', 'bypass_dst_v6', list=True, default=[]))

    return ret

def fact_mac_ip_binding(uci: EUci):
    ret = { "disabled": 0, "soft-binding": 0, "hard-binding": 0 }
    # Parse DHCP servers (interface with static IP, wan is excluded)
    result = subprocess.check_output(['/usr/libexec/rpcd/ns.dhcp', 'call', 'list-interfaces'])
    interfaces = json.loads(result)
    for i in interfaces:
        if uci.get('dhcp', i, 'ns_binding', default='') == '' or uci.get('dhcp', i, 'ns_binding', default='') == '0':
            ret['disabled'] += 1  # Increment the count for DHCP servers
        elif uci.get('dhcp', i, 'ns_binding', default='') == '1':
            ret['soft-binding'] += 1
        elif uci.get('dhcp', i, 'ns_binding', default='') == '2':
            ret['hard-binding'] += 1
    return ret

def fact_backups(uci: EUci):
    ret = { 'backup_passphrase': False, 'passphrase_date': 0 }
    try:
        ret['backup_passphrase'] = os.path.exists('/etc/backup.pass')
        ret['passphrase_date'] = int(os.path.getmtime('/etc/backup.pass'))
    except:
        return {}
    return ret

def fact_ha(uci: EUci):
    vrrp_instances = utils.get_all_by_type(uci, 'keepalived', 'vrrp_instance')
    if vrrp_instances is None:
        vrrp_instances = []
    ipaddresses = utils.get_all_by_type(uci, 'keepalived', 'ipaddress')
    if ipaddresses is None:
        ipaddresses = []

    return { 'enabled': len(vrrp_instances) > 0, 'vips': len(ipaddresses) }

def fact_default_password(uci: EUci):
    data = {
        'username': 'root',
        'password': 'Nethesis,1234',
        'timeout': 1
    }
    result = subprocess.run(['/bin/ubus', 'call', 'session', 'login', json.dumps(data)], capture_output=True)

    return { 'default_password': result.returncode == 0 }

## Info
## These functions are used to send info about system to new my.nethesis.it and phonehome.nethserver.org

def info_fqdn(uci: EUci):
    system = uci.get_all('system')
    for section in system:
        for option in system[section]:
            if option == 'hostname':
                return anonymize(system[section][option], uci)
    return ''

def info_timezone(uci: EUci):
    system = uci.get_all('system')
    for section in system:
        for option in system[section]:
            if option == 'zonename':
                return system[section][option]
    return ''

def info_kernel_version(uci: EUci):
    try:
        with open('/proc/version', 'r') as f:
            version = f.read().strip()
            return version.split()[2]
    except:
        return ''

def info_uptime_seconds(uci: EUci):
    try:
        with open('/proc/uptime', 'r') as f:
            uptime = f.read().strip().split()[0]
            return floor(float(uptime))
    except:
        return 0

def info_default_ipv4(uci: EUci):
    # first method: dig -4 TXT +short o-o.myaddr.l.google.com @ns1.google.com
    try:
        res = subprocess.run(['dig', '-4', '+short', 'myip.opendns.com', '@resolver1.opendns.com'],
                             capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            ip = res.stdout.strip().strip('"')
            if ip:
                return anonymize(ip, uci)
    except:
        pass

    # second method: curl -4 ifconfig.co
    try:
        res = subprocess.run(['curl', '-4', '-s', 'ifconfig.co'],
                             capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            return anonymize(res.stdout.strip(), uci)
    except:
        pass

    # third method: get the first WAN device and its IPv4
    try:
        wan_devices = utils.get_all_wan_devices(uci)
        if wan_devices:
            first_wan = wan_devices[0]
            res = subprocess.run(['ip', '-4', '-j', 'addr', 'show', first_wan],
                                 capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                addr_info = json.loads(res.stdout)
                if addr_info and 'addr_info' in addr_info[0]:
                    for addr in addr_info[0]['addr_info']:
                        if addr.get('family') == 'inet':
                            return anonymize(addr.get('local'), uci)
    except:
        pass

    return ''

def info_default_ipv6(uci: EUci):
    # Get the first WAN device and its IPv6
    ipv6 = ''
    try:
        wan_devices = utils.get_all_wan_devices(uci)
        if wan_devices:
            first_wan = wan_devices[0]
            res = subprocess.run(['ip', '-6', '-j', 'addr', 'show', first_wan],
                                 capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                addr_info = json.loads(res.stdout)
                if addr_info and 'addr_info' in addr_info[0]:
                    for addr in addr_info[0]['addr_info']:
                        if addr.get('family') == 'inet6' and addr.get('scope') == 'global':
                            ipv6 = addr.get('local')
    except:
        pass

    # If WAN has no IPv6, assume that IPv6 is not configured: speedup data collection
    if ipv6 == '':
        return ''

    # first method: dig -6 TXT +short o-o.myaddr.l.google.com @ns1.google.com
    try:
        res = subprocess.run(['dig', '-6', 'TXT', '+short', 'o-o.myaddr.l.google.com', '@ns1.google.com'],
                             capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            ip = res.stdout.strip().strip('"')
            if ip:
                return anonymize(ip, uci)
    except:
        pass

    # second method: curl -6 ifconfig.co
    try:
        res = subprocess.run(['curl', '-6', '-s', 'ifconfig.co'],
                             capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            return anonymize(res.stdout.strip(), uci)
    except:
        pass


    return anonymize(ipv6, uci)

def info_package_updates_available(uci: EUci):
    """Check if package updates are available"""
    try:
        res = subprocess.run(['/usr/libexec/rpcd/ns.update', 'call', 'check-package-updates'],
                             capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            if isinstance(data, dict) and 'updates' in data:
                updates = data['updates']
                if isinstance(updates, list) and len(updates) > 0:
                    return True
    except:
        pass
    return False

def info_image_updates_available(uci: EUci):
    """Check if system image updates are available"""
    try:
        res = subprocess.run(['/usr/libexec/rpcd/ns.update', 'call', 'check-system-update'],
                             capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            current_version = data.get('currentVersion', '')
            last_version = data.get('lastVersion', '')

            if current_version and last_version:
                current = parse_version(current_version)
                last = parse_version(last_version)
                if current and last and last > current:
                    return True
    except:
        pass
    return False

def info_dns_servers(uci: EUci):
    dns_list = []
    try:
        for server in uci.get('dhcp', 'ns_dnsmasq', 'server', list=True, default=[]):
            dns_list.append(server)
    except:
        pass
    if not dns_list:
        try:
            with open('/tmp/resolv.conf.d/resolv.conf.auto', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('nameserver'):
                        parts = line.split()
                        if len(parts) > 1:
                            dns_list.append(parts[1])
        except:
            pass
    return dns_list
