#!/usr/bin/python3

#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

'''
Firewall utilities
'''
import ipaddress
import json
import os
import subprocess

from euci import EUci

from nethsec import utils, objects

PROTOCOLS = ['tcp', 'udp', 'udplite', 'icmp', 'esp', 'ah', 'sctp']
TARGETS = ['ACCEPT', 'DROP', 'REJECT', 'NOTRACK']

def add_device_to_zone(uci, device, zone):
    '''
    Add given device to a firewall zone.
    The device is not added if the firewall zone does not exists
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - device -- Device name
      - zone -- Firewall zone name

    Returns:
      - If the firewall zone exists, the name of the section where the device has been added.
      - None, otherwise.
    '''
    for section in uci.get("firewall"):
        s_type = uci.get("firewall", section)
        if s_type == "zone":
            zname = uci.get("firewall", section, "name")
            if zname == zone:
                try:
                    devices = list(uci.get_all("firewall", section, "device"))
                except:
                    devices = []
                if not device in devices:
                    devices.append(device)
                    uci.set("firewall", section, "device", devices)
                    uci.save("firewall")
                return section

    return None

def add_interface_to_zone(uci, interface, zone):
    '''
    Add given interface to a firewall zone.
    The interface is not added if the firewall zone does not exists
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - interface -- Interface name
      - zone -- Firewall zone name

    Returns:
      - If the firewall zone exists, the name of the section where the device has been added.
      - None, otherwise.
    '''
    for section in uci.get("firewall"):
        s_type = uci.get("firewall", section)
        if s_type == "zone":
            zname = uci.get("firewall", section, "name")
            if zname == zone:
                try:
                    networks = list(uci.get_all("firewall", section, "network"))
                except:
                    networks = []
                if not interface in networks:
                    networks.append(interface)
                    uci.set("firewall", section, "network", networks)
                    uci.save("firewall")
                return section

    return None


def remove_interface_from_zone(uci, interface, zone):
    '''
    Remove the given interface from a firewall zone.
    The operation always succeed if the zone does not exists

    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - interface -- Interface name
      - zone -- Firewall zone name

    Returns:
      - If the firewall zone exists, the name of the section where the interface has been removed.
      - None, otherwise.
    '''
 
    for z in utils.get_all_by_type(uci, 'firewall', 'zone'):
        if uci.get('firewall', z, 'name') == zone:
            try:
                networks = list(uci.get_all("firewall", z, "network"))
            except:
                networks = []
            if interface in networks:
                networks.remove(interface)
                uci.set("firewall", z, "network", networks)
                uci.save("firewall")
                return z
    return None

def remove_device_from_zone(uci, device, zone):
    '''
    Remove the given device from a firewall zone.
    The operation always succeed if the zone does not exists

    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - device -- Device name
      - zone -- Firewall zone name

    Returns:
      - If the firewall zone exists, the name of the section where the device has been removed.
      - None, otherwise.
    '''
 
    for z in utils.get_all_by_type(uci, 'firewall', 'zone'):
        if uci.get('firewall', z, 'name') == zone:
            try:
                devices = list(uci.get_all("firewall", z, "device"))
            except:
                devices = []
            if device in devices:
                devices.remove(device)
                uci.set("firewall", z, "device", devices)
                uci.save("firewall")
                return z
    return None

def add_device_to_lan(uci, device):
    '''
    Shortuct to add a device to lan zone

    Arguments:
      - uci -- EUci pointer
      - device -- Device name

    Returns:
      - The name of section or None
    '''
    return add_device_to_zone(uci, device, 'lan')

def add_device_to_wan(uci, device):
    '''
    Shortuct to add a device to wan zone

    Arguments:
      - uci -- EUci pointer
      - device -- Device name

    Returns:
      - The name of the configuration section or None
    '''
    return add_device_to_zone(uci, device, 'wan')

def add_vpn_interface(uci, name, device, link=""):
    '''
    Create a network interface for the given device.
    The interface can be used for PBR (Policy Based Routing).
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - name -- Interface name
      - device -- Device name
      - link -- A reference to an existing key in the format <database>/<keyname> (optional)

    Returns:
      - The name of the configuration section or None in case of error
    '''
    iname = utils.sanitize(name)
    uci.set('network', iname, 'interface')
    uci.set('network', iname, 'proto', 'none')
    uci.set('network', iname, 'device', device)
    uci.set('network', iname, 'ns_tag', ["automated"])
    if link:
        uci.set('network', iname, 'ns_link', link)
    uci.save('network')
    return iname

def add_trusted_zone(uci, name, networks = [], link = ""):
    '''
    Create a trusted zone. The zone will:
      - be able to access lan and wan zone
      - be accessible from lan zone

    If a zone with the same name already exists, do not recreate it.
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - name -- Zone name, maximum length is 12
      - network -- A list of interfaces to be added to the zone (optional)
      - link -- A reference to an existing key in the format <database>/<keyname> (optional)

    Returns a tuple:
      - The name of the configuration section or None in case of error
      - A list of configuration sections or an empy list in case of error
    '''

    if len(name) > 12:
        return None, None

    # avoid duplicated zones
    zones = utils.get_all_by_type(uci, 'firewall', 'zone')
    for z in zones:
        if zones[z].get("name", "") == name:
            return None, None
    forwardings = list()
    zname = utils.get_random_id()
    name = utils.sanitize(name)
    uci.set("firewall", zname, 'zone')
    uci.set("firewall", zname, 'name', name)
    uci.set("firewall", zname, 'input', 'ACCEPT')
    uci.set("firewall", zname, 'output', 'ACCEPT')
    uci.set("firewall", zname, 'forward', 'REJECT')
    if networks:
        uci.set("firewall", zname, 'network', networks)
    uci.set("firewall", zname, "ns_tag", ["automated"])
    if link:
        uci.set("firewall", zname, "ns_link", link)

    flan = utils.get_random_id()
    uci.set("firewall", flan, "forwarding")
    uci.set("firewall", flan, "src", name)
    uci.set("firewall", flan, "dest", "lan")
    uci.set("firewall", flan, "ns_tag", ["automated"])
    if link:
        uci.set("firewall", flan, "ns_link", link)
    forwardings.append(flan)

    flan = utils.get_random_id()
    uci.set("firewall", flan, "forwarding")
    uci.set("firewall", flan, "src", "lan")
    uci.set("firewall", flan, "dest", name)
    uci.set("firewall", flan, "ns_tag", ["automated"])
    if link:
        uci.set("firewall", flan, "ns_link", link)
    forwardings.append(flan)

    flan = utils.get_random_id()
    uci.set("firewall", flan, "forwarding")
    uci.set("firewall", flan, "src", name)
    uci.set("firewall", flan, "dest", "wan")
    uci.set("firewall", flan, "ns_tag", ["automated"])
    if link:
        uci.set("firewall", flan, "ns_link", link)
    forwardings.append(flan)
    uci.save('firewall')
    reorder_firewall_config(uci)

    return zname, forwardings

def add_service(uci, name, port, proto, link = "", tags=None):
    '''
    Create an ACCEPT traffic rule for the given service
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - name -- Service name
      - port -- Service port number as string or array
      - proto -- List of service protocols
      - link -- A reference to an existing key in the format <database>/<keyname> (optional)

    Returns:
      - The name of the configuration section
    '''
    if tags is None:
        tags = ['automated']
    rname = utils.get_id(f"allow_{name}")
    uci.set("firewall", rname, "rule")
    uci.set("firewall", rname, "name", f"Allow-{name}")
    uci.set("firewall", rname, "ns_service", "custom")
    uci.set("firewall", rname, "src", "wan")
    uci.set("firewall", rname, "dest_port", port)
    if type(proto) is str:
        proto = [proto]
    uci.set("firewall", rname, "proto", proto)
    uci.set("firewall", rname, "target", "ACCEPT")
    uci.set("firewall", rname, "enabled", "1")
    uci.set("firewall", rname, "ns_tag", tags)
    if link:
        uci.set("firewall", rname, "ns_link", link)
    uci.save('firewall')
    reorder_firewall_config(uci)

    return rname

def remove_service(uci, name):
    '''
    Remove the ACCEPT traffic rule for the given service
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - name -- Service name

    Returns:
      - The name of the configuration section
    '''
    rname = utils.get_id(f"allow_{name}")
    uci.delete("firewall", rname)
    uci.save('firewall')
    reorder_firewall_config(uci)

    return rname

def disable_service(uci, name):
    '''
    Disable the ACCEPT rule traffic for the given service.
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - name -- Service name

    Returns:
      - The name of the configuration section if found, None otherwise
    '''
    rname = utils.get_id(f"allow_{name}")
    try:
        uci.set("firewall", rname, "enabled", "0")
    except:
        return None
    uci.save("firewall")
    return rname

def enable_service(uci, name):
    '''
    Disable the ACCEPT rule traffic for the given service
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - name -- Service name

    Returns:
      - The name of the configuration section if found, None otherwise
    '''
    rname = utils.get_id(f"allow_{name}")
    try:
        uci.set("firewall", rname, "enabled", "0")
    except:
        return None
    uci.save("firewall")
    return rname

def apply(uci):
    '''
    Apply firewall configuration:
      - commit changes to firewall config
      - reload the firewall service

    Arguments:
      - uci -- EUci pointer
    '''
    uci.commit('firewall')
    subprocess.run(["/etc/init.d/firewall", "reload"], check=True)


def add_template_forwarding(uci, name, link = ""):
    '''
    Create a forwarding from templates database.
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - name -- Name of the template forwarding from the templates database
      - link -- A reference to an existing key in the format <database>/<keyname> (optional)

    Returns a tuple:
      - The name of the configuration section for the forwarding or None in case of error
    '''

    frecord =  uci.get_all("templates", name)
    fname = utils.get_random_id()
    uci.set("firewall", fname, "forwarding")
    for section in frecord:
        uci.set("firewall", fname, section, frecord[section])
    uci.set("firewall", fname, "ns_tag", ["automated"])
    if link:
        uci.set("firewall", fname, "ns_link", link)
    uci.save('firewall')
    reorder_firewall_config(uci)

    return fname

def add_template_zone(uci, name, networks = [], link = ""):
    '''
    Create a zone from templates database.
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - name -- Name of the zone from the templates database
      - network -- A list of interfaces to be added to the zone (optional)
      - link -- A reference to an existing key in the format <database>/<keyname> (optional)

    Returns a tuple:
      - The name of the configuration section for the zone or None in case of error
      - A list of configuration section names for the forwardings or None in case of error
    '''

    dzone = uci.get_all("templates", name)
    # Search for zones with the same "name"
    for zone in utils.get_all_by_type(uci, "firewall", "zone"):
        if uci.get("firewall", zone, "name") == dzone["name"]:
            return None, None

    forwardings = list()
    zname = utils.get_random_id()
    forward_list = dzone.pop("forwardings", list())
    uci.set("firewall", zname, "zone")
    for section in dzone:
        uci.set("firewall", zname, section, dzone[section])
    if len(networks) > 0:
        uci.set("firewall", zname, "network", networks)
    uci.set("firewall", zname, "ns_tag", ["automated"])
    if link:
        uci.set("firewall", zname, "ns_link", link)

    for forward in forward_list:
        forwardings.append(add_template_forwarding(uci, forward, link))
    uci.save('firewall')
    reorder_firewall_config(uci)
    return (zname, forwardings)

def add_template_service_group(uci, name, src='lan', dest='wan', link=""):
    '''
    Create all rules for the given service group
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - name -- Name of the service group from the templates database
      - src -- Source zone, default is 'lan'. The zone must already exists inside the firewall db
      - dest -- Destination zone, default is 'wan'. The zone must already exists inside the firewall db
      - link -- A reference to an existing key in the format <database>/<keyname> (optional)

    Returns:
      - A list of configuration section names of each rule, None in case of error
    '''

    group = uci.get_all("templates", name)
    services = group.pop("services", list())

    if not services:
        return None

    rules = dict()
    sections = list()

    for service in services:
        (port, proto, sdesc) = service.split("/",2)
        if proto not in rules:
            rules[proto] = {"ports": list(), "description": ""}
        rules[proto]["ports"].append(port)
        rules[proto]["description"] = utils.sanitize(sdesc)

    for proto in rules:
        sname = utils.get_random_id()
        desc = rules[proto]["description"]
        uci.set("firewall", sname, "rule")
        uci.set("firewall", sname, "name", f"Allow-{name}-{proto}")
        uci.set("firewall", sname, "ns_description", f"{desc} - {proto}")
        uci.set("firewall", sname, "src", src)
        uci.set("firewall", sname, "dest", dest)
        uci.set("firewall", sname, "proto", proto)
        uci.set("firewall", sname, "dest_port", ",".join(rules[proto]["ports"]))
        uci.set("firewall", sname, "target", "ACCEPT")
        uci.set("firewall", sname, "enabled", "1")
        uci.set("firewall", sname, "ns_tag", ["automated"])
        if link:
            uci.set("firewall", sname, "ns_link", link)
        sections.append(sname)
    uci.save('firewall')
    reorder_firewall_config(uci)
    return sections

def add_template_rule(uci, name, proto="", port="", link="", tags=None):
    '''
    Create a rule from templates database.
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - name -- Name of the template rule from the templates database
      - proto -- A valid UCI protocol (optional)
      - port -- A port or comma-separated list of ports (optional)
      - link -- A reference to an existing key in the format <database>/<keyname> (optional)

    Returns:
      - The name of the configuration section for the rule or None in case of error
    '''

    if tags is None:
        tags = ['automated']
    drule = uci.get_all("templates", name)
    rname = utils.get_random_id()
    uci.set("firewall", rname, "rule")
    for section in drule:
        if port:
            drule[section] = drule[section].replace("__PORT__", port)
        if proto:
            drule[section] = drule[section].replace("__PROTO__", proto)
        uci.set("firewall", rname, section, drule[section])
    uci.set("firewall", rname, "ns_tag", tags)
    if link:
        uci.set("firewall", rname, "ns_link", link)
    uci.save('firewall')
    reorder_firewall_config(uci)
    return rname

def get_all_linked(uci, link):
    '''
    Search all database, execpt templates one, for entities with the given link

    Arguments:
      - uci -- EUci pointer
      - link -- A reference to an existing key in the format <database>/<keyname>

    Returns:
      - A dictionary of all matched sections like
        {"db1": ["key1", "key2"], "db2": [...] }
    '''

    ret = dict()
    for config in uci.list_configs():
        if config == "templates" or config.endswith(".backup"):
            continue
        records = utils.get_all_by_option(uci, config, 'ns_link', link, deep = False)
        ret[config] = records

    return ret

def disable_linked_rules(uci, link):
    '''
    Disable all rules matching the given link
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - link -- A reference to an existing key in the format <database>/<keyname>

    Returns:
      - A list of disabled sections
    '''

    disabled = list()
    linked = get_all_linked(uci, link)
    if "firewall" in linked:
        for section in linked["firewall"]:
            if uci.get("firewall", section) == "rule":
                uci.set("firewall", section, "enabled", 0)
                disabled.append(section)

    uci.save("firewall")
    return disabled

def delete_linked_sections(uci, link):
    '''
    Delete all sections matching the given link.
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer
      - link -- A reference to an existing key in the format <database>/<keyname>

    Returns:
      - A list of deleted sections
    '''

    deleted = list()
    linked = get_all_linked(uci, link)
    for db in linked:
        for section in linked[db]:
            uci.delete(db, section)
            deleted.append(section)
        uci.save(db)

    return deleted

def is_ipv6_enabled(uci):
    '''
    Search the network database for devices and interfaces using IPv6

    Arguments:
      - uci -- EUci pointer

    Returns:
      - True if IPv6 is enabled at least on a device or interface, False otherwise
    '''

    for interface in utils.get_all_by_type(uci, 'network', 'interface'):
        for option in uci.get_all('network', interface):
            if option.startswith("ip6") or option == "dhcpv6" or option == "ipv6":
                return True
        if uci.get('network', interface, 'proto', default="") in ['6in4', '6to4', '6rd', 'grev6', 'grev6tap', 'vtiv6']:
            return True

    for device in utils.get_all_by_type(uci, 'network', 'device'):
        try:
            if uci.get_all('network', device, 'ipv6') == 1:
                return True
        except:
            pass
    return False

def disable_ipv6_firewall(uci):
    '''
    Disable all rules, forwardings, redirects, zones and ipsets for ipv6-only family.
    Changes are saved to staging area.

    Arguments:
      - uci -- EUci pointer

    Returns:
      - A list of disabled sections
    '''

    disabled = list()
    for section_type in ["rule", "forwarding", "redirect", "zone", "ipset"]:
        for section in utils.get_all_by_type(uci, 'firewall', section_type):
            if uci.get("firewall", section, 'family', default="any") == "ipv6":
                uci.set("firewall", section, "enabled", "0")
                disabled.append(section)

    uci.save("firewall")
    return disabled


def list_zones(uci) -> dict:
    """
    Get all zones from firewall config

    Args:
        uci: EUci pointer

    Returns:
        dict with all zones
    """
    return utils.get_all_by_type(uci, 'firewall', 'zone')


def list_zones_no_aliases(uci) -> dict:
    """
    Get all zones from firewall config, excluding aliases in network section

    Args:
      - uci: EUci pointer

    Returns:
        dict with all zones
    """
    zones = list_zones(uci)
    for name, zone in zones.items():
        result = []
        networks = zone.get("network", [])
        for network in networks:
            config_network = uci.get("network", network, "device", default="", dtype=str)
            if not config_network.startswith("@"):
                result.append(network)

        zone["network"] = result

    return zones


def list_forwardings(uci) -> dict:
    """
    Get all forwardings from firewall config

    Args:
        uci: EUci pointer

    Returns:
        dict with all forwardings
    """
    return utils.get_all_by_type(uci, 'firewall', 'forwarding')


def add_forwarding(uci, src: str, dest: str) -> str:
    """
    Add forwarding from src to dest.

    Args:
        uci: EUci pointer
        src: source zone, must be zone name, not config name
        dest: destination zone, must be zone name, not config name

    Returns:
        name of forwarding config that was added
    """
    config_name = utils.get_id(f'{src}2{dest}')
    uci.set('firewall', config_name, 'forwarding')
    uci.set('firewall', config_name, 'src', src)
    uci.set('firewall', config_name, 'dest', dest)
    uci.save('firewall')
    return config_name

def get_zone_by_name(uci, name: str) -> str:
    """
    Get zone config name by zone name.

    Args:
        uci: EUci pointer
        name: zone name

    Returns:
        tuple of zone config name and zone config if zone with name name exists, (None, None) otherwise
    """
    zones = utils.get_all_by_type(uci, 'firewall', 'zone')
    for z in zones:
        if uci.get('firewall', z, 'name', default='') == name:
            return (z, zones[z])
    return (None, None)

def get_rule_by_name(uci, name: str, tag = "") -> str:
    """
    Get rule config name and rule data by rule name, optionally filtered by tag.
    Assume there is only one rule with the same name.

    Args:
        uci: EUci pointer
        name: rule name
        tag: optional tag to filter rules

    Returns:
        tuple of rule config name and rule config if rule with name name exists, (None, None) otherwise
    """
    rules = utils.get_all_by_type(uci, 'firewall', 'rule')
    for r in rules:
        if uci.get('firewall', r, 'name', default='') == name:
            if not tag or tag in uci.get('firewall', r, 'ns_tag', default=[]):
                return (r, rules[r])
    return (None, None)


def zone_exists(u, zone_name):
    """
    Check if a zone with name zone_name already exists

    Args:
        u: EUci pointer
        zone_name: zone name to check

    Returns:
        true if a zone with name zone_name already exists, false otherwise
    """
    try:
        for h in utils.get_all_by_type(u, 'firewall', 'zone'):
            if u.get('firewall', h, 'name', default='') == zone_name:
                return True
    except:
        return False

    return False


def add_zone(uci, name: str, input: str, forward: str, traffic_to_wan: bool = False, forwards_to: list[str] = None,
             forwards_from: list[str] = None, log: bool = False) -> {str, set[str]}:
    """
    Add zone to firewall config.

    Args:
        uci: EUci pointer
        name: name of zone
        input: rule for input traffic, must be one of 'ACCEPT', 'REJECT', 'DROP'
        forward: rule for forward traffic, must be one of 'ACCEPT', 'REJECT', 'DROP'
        traffic_to_wan: if True, add forwarding from zone to wan
        forwards_to: list of zones to forward traffic to
        forwards_from: list of zones to forward traffic from
        log: if True, log blocked traffic destined to this zone

    Returns:
        tuple of zone config name and set of added forwarding configs
    """

    # check if a zone with the same name already exists
    if zone_exists(uci, name):
        return utils.validation_error("name", "zone_already_exists", name)

    zone_config_name = utils.get_id(name)
    uci.set('firewall', zone_config_name, 'zone')
    uci.set('firewall', zone_config_name, 'name', name)
    uci.set('firewall', zone_config_name, 'input', input)
    uci.set('firewall', zone_config_name, 'forward', forward)
    uci.set('firewall', zone_config_name, 'output', 'ACCEPT')
    if log:
        uci.set('firewall', zone_config_name, 'log', '1')
        log_opts = get_default_logging_options(uci)
        uci.set('firewall', zone_config_name, 'log_limit', log_opts['zone_log_limit'])
    else:
        uci.set('firewall', zone_config_name, 'log', '0')
        try:
            uci.delete('firewall', zone_config_name, 'log_limit')
        except:
            pass


    forwardings_added = set()

    if traffic_to_wan:
        forwardings_added.add(add_forwarding(uci, name, 'wan'))

    if forwards_to is not None:
        for forward_to in forwards_to:
            forwardings_added.add(add_forwarding(uci, name, forward_to))

    if forwards_from is not None:
        for forward_from in forwards_from:
            forwardings_added.add(add_forwarding(uci, forward_from, name))

    uci.save('firewall')
    reorder_firewall_config(uci)
    return zone_config_name, forwardings_added


def edit_zone(uci, name: str, input: str, forward: str, traffic_to_wan: bool = False, forwards_to: list[str] = None,
             forwards_from: list[str] = None, log: bool = False) -> {str, set[str]}:
    """
    Edit an existing zone.

    Args:
        uci: EUci pointer
        name: name of zone to edit
        input: rule for input traffic, must be one of 'ACCEPT', 'REJECT', 'DROP'
        forward: rule for forward traffic, must be one of 'ACCEPT', 'REJECT', 'DROP'
        traffic_to_wan: if True, add forwarding from zone to wan
        forwards_to: list of zones to forward traffic to
        forwards_from: list of zones to forward traffic from
        log: if True, log blocked traffic destined to this zone

    Returns:
        tuple of zone config name and set of updated forwarding configs
    """
    (zone_config_name, zone) = get_zone_by_name(uci, name)
    if zone is None or zone_config_name is None:
        return utils.validation_error("name", "zone_does_not_exists", name)

    uci.set('firewall', zone_config_name, 'input', input)
    uci.set('firewall', zone_config_name, 'forward', forward)
    uci.set('firewall', zone_config_name, 'output', 'ACCEPT')
    if log:
        uci.set('firewall', zone_config_name, 'log', '1')
        if uci.get('firewall', zone_config_name, 'log_limit', default=None) is None:
            # set default log limit, do not overwrite existing value
            log_opts = get_default_logging_options(uci)
            uci.set('firewall', zone_config_name, 'log_limit', log_opts['zone_log_limit'])
    else:
        uci.set('firewall', zone_config_name, 'log', '0')
        try:
            uci.delete('firewall', zone_config_name, 'log_limit')
        except:
            pass

    # delete old forwardings

    forwardings = list_forwardings(uci)
    to_delete_forwardings = set()
    for forwarding in forwardings:
        if forwardings[forwarding]['src'] == name:
            to_delete_forwardings.add(forwarding)
        if forwardings[forwarding]['dest'] == name:
            to_delete_forwardings.add(forwarding)

    for to_delete_forwarding in to_delete_forwardings:
        uci.delete('firewall', to_delete_forwarding)

    # create updated forwardings

    forwardings_added = set()

    if traffic_to_wan:
        forwardings_added.add(add_forwarding(uci, name, 'wan'))

    if forwards_to is not None:
        for forward_to in forwards_to:
            forwardings_added.add(add_forwarding(uci, name, forward_to))

    if forwards_from is not None:
        for forward_from in forwards_from:
            forwardings_added.add(add_forwarding(uci, forward_from, name))

    uci.save('firewall')
    return zone_config_name, forwardings_added


def delete_zone(uci, zone_config_name: str) -> {str, set[str]}:
    """
    Delete zone and all forwardings that are connected to it.

    Args:
        uci: EUci pointer
        zone_config_name: name of zone config to delete

    Returns:
        tuple of zone config name and set of deleted forwarding configs

    Raises:
        ValueError: if zone_config_name is not a valid zone config name
    """
    if zone_config_name not in list_zones(uci):
        raise ValueError
    zone_name = list_zones(uci)[zone_config_name]['name']
    forwardings = list_forwardings(uci)
    to_delete_forwardings = set()
    for forwarding in forwardings:
        if forwardings[forwarding]['src'] == zone_name:
            to_delete_forwardings.add(forwarding)
        if forwardings[forwarding]['dest'] == zone_name:
            to_delete_forwardings.add(forwarding)

    for to_delete_forwarding in to_delete_forwardings:
        uci.delete('firewall', to_delete_forwarding)
    uci.delete('firewall', zone_config_name)
    uci.save('firewall')
    reorder_firewall_config(uci)
    return zone_config_name, to_delete_forwardings

def add_default_ipv6_rules(uci):
    """
    Add default ipv6 rules to firewall config, if they don't exist already.

    Args:
        uci: EUci pointer
    
    Returns:
        list of added rule config names
    """
    ret = list()
    rules = {"ip6_dhcp" : "Allow-DHCPv6", "ip6_mld" : "Allow-MLD", "ip6_icmp" : "Allow-ICMPv6-Input", "ip6_icmp_forward" : "Allow-ICMPv6-Forward"}
    for r in rules:
        (rule_name, rule) = get_rule_by_name(uci, rules[r], tag="automated")
        if rule_name is None:
            ret.append(add_template_rule(uci, r))
    return ret

def delete_rule(uci, id: str) -> str:
    """
    Delete rule from firewall config.

    Args:
        uci: EUci pointer
        id: name of rule config to delete

    Returns:
        name of rule config that was deleted

    Raises:
        ValueError: if id is not a valid rule config name
    """
    if id not in list_rule_ids(uci):
        raise utils.ValidationError('id', 'rule_not_found', id)
    uci.delete('firewall', id)
    uci.save('firewall')
    reorder_firewall_config(uci)
    return id

def disable_rule(uci, id: str) -> str:
    """
    Disable rule from firewall config.

    Args:
        uci: EUci pointer
        id: name of rule config to disable

    Returns:
        name of rule config that was disabled

    Raises:
        ValueError: if id is not a valid rule config name
    """
    if id not in list_rule_ids(uci):
        raise utils.ValidationError('id', 'rule_not_found', id)
    uci.set('firewall', id, 'enabled', '0')
    uci.save('firewall')
    return id

def enable_rule(uci, id: str) -> str:
    """
    Enable rule from firewall config.

    Args:
        uci: EUci pointer
        id: name of rule config to enable

    Returns:
        name of rule config that was enabled

    Raises:
        ValueError: if id is not a valid rule config name
    """
    if id not in list_rule_ids(uci):
        raise utils.ValidationError('id', 'rule_not_found', id)
    uci.set('firewall', id, 'enabled', '1')
    uci.save('firewall')
    return id

def list_rule_ids (uci) -> list[str]:
    """
    Get all rule ids from firewall config

    Args:
        uci: EUci pointer

    Returns:
        list of all rule ids
    """
    return list(utils.get_all_by_type(uci, 'firewall', 'rule').keys())

def order_rules(uci, rule_type: str, order: list[str]) -> list[str]:
    """
    Orders firewall rules, moves everything else but rules to the end of the list.

    Args:
        e_uci: euci instance
        rule_type: type of rule to order, must be 'input', 'output' or 'forward'
        rules: which order to put rules

    Returns:
        list of ordered rules entries

    Raises:
        ValidationError: if a rule is not present in /etc/config/firewall
    """
    rules = []
    if not rule_type in ['input', 'output', 'forward']:
        raise utils.ValidationError('rule_type', 'invalid_rule_type', rule_type)
    
    (defaults, zones, forwardings, other_rules, forward_rules, output_rules, input_rules) = split_firewall_config(uci)

    if rule_type == 'input':
        rules = input_rules
    elif rule_type == 'output':
        rules = output_rules
    elif rule_type == 'forward':
        rules = forward_rules

    for r in rules:
        if r not in order:
            raise utils.ValidationError('order', 'invalid_order', r)

    if rule_type == 'input':
        final_order = defaults + zones + forwardings + other_rules + forward_rules + output_rules + order
    elif rule_type == 'output':
        final_order = defaults + zones + forwardings + other_rules + forward_rules + order + input_rules
    elif rule_type == 'forward':
        final_order = defaults + zones + forwardings + other_rules + order + output_rules + input_rules
    
    # enforce new order
    index = 0
    for section in final_order:
        subprocess.run(["uci", "-c", uci.confdir(), "-t", uci.savedir(), "reorder", f"firewall.{section}={index}"])
        index = index + 1
    uci.save('firewall')

    return order

def resolve_address(uci, address: str) -> str:
    """
    Resolve address to a more human-redeable name.

    Args:
        uci: EUci pointer
        address: address to resolve

    Returns:
        resolved address as a dict with keys value, label and type
    """
    for section in uci.get_all("dhcp"):
        if uci.get("dhcp", section, "ip", default='') == address:
            return {"value": address, "label": uci.get("dhcp", section, "name", default=address), "type": uci.get("dhcp", section)}

    for section in uci.get_all("network"):
        if uci.get("network", section, "ipaddr", default='') == address:
            return {"value": address, "label": section, "type": uci.get("network", section)}
        if uci.get("network", section, "ip6addr", default='') == address:
            return {"value": address, "label": section, "type": uci.get("network", section)}

    return {"value": address, "label": None, "type": None}

def enrich_rule(uci, rule: dict) -> dict:
    """
    Enrich rule with more human-readable data and missing fields

    Args:
        uci: EUci pointer
        rule: rule to enrich

    Returns:
        enriched rule
    """
    if 'automated' in rule.get('ns_tag', []):
        rule['system_rule'] = True
    else:
        rule['system_rule'] = False
    if not 'src_ip' in rule:
        rule['src_ip'] = []
    else:
        if type(rule['src_ip'] ) == tuple:
            rule['src_ip'] = list(rule['src_ip'])
        elif type(rule['src_ip'] ) == str:
            rule['src_ip'] = [rule['src_ip']]
    if not 'dest_ip' in rule:
        rule['dest_ip'] = []
    else:
        if type(rule['dest_ip'] ) == tuple:
            rule['dest_ip'] = list(rule['dest_ip'])
        elif type(rule['dest_ip'] ) == str:
            rule['dest_ip'] = [rule['dest_ip']]
    # try to gather info on src_ip and dest_ip
    for key in ['src_ip', 'dest_ip']:
        tmp = []
        for ip in rule.get(key, []):
            if ip:
                tmp.append(resolve_address(uci, ip))
        rule[key] = tmp
    proto = rule.get('proto', "")
    if not proto:
        rule['proto'] = ['udp', 'tcp']
    else:
        if type(proto) == tuple:
            rule['proto'] = list(proto)
        elif type(proto) == str:
            rule['proto'] = [proto]
    dest_port = rule.get('dest_port', "")
    if not dest_port:
        rule['dest_port'] = []
    else:
        if type(dest_port) != list:
            rule['dest_port'] = dest_port.split(" ")
    if not 'ns_service' in rule:
        if rule.get('proto') != None or rule.get('dest_port') != None:
            rule['ns_service'] = 'custom'
        else:
            rule['ns_service'] = ''
    if not 'ns_tag' in rule:
        rule['ns_tag'] = []
    rule['log'] = True if rule.get('log', '0') == '1' else False
    rule['enabled'] = True if rule.get('enabled', '1') == '1' else False
    return rule

def is_forward_rule(rule: dict) -> bool:
    """
    Check if rule is a forward rule

    Args:
        rule: rule to check

    Returns:
        True if rule is a forward rule, False otherwise
    """
    if rule.get('dest') and rule.get('src'):
        return True
    return False

def is_input_rule(rule: dict) -> bool:
    """
    Check if rule is an input rule

    Args:
        rule: rule to check

    Returns:
        True if rule is an input rule, False otherwise
    """
    if not rule.get('dest') and rule.get('src'):
        return True
    return False

def is_output_rule(rule: dict) -> bool:
    """
    Check if rule is an output rule

    Args:
        rule: rule to check

    Returns:
        True if rule is an output rule, False otherwise
    """
    if rule.get('dest') and not rule.get('src'):
        return True
    return False

def is_zone(uci, name:str) -> bool:
    """
    Check if name is a zone or any zone ('*')

    Args:
        name: zone to check

    Returns:
        True if name is a zone, False otherwise
    """

    # True zone if name is 'any' zone name -> '*'
    if name == '*':
        return True

    zones = list_zones(uci)
    for value in zones.values():
        if 'name' in value and value['name'] == name:
            return True
    return False

def list_rules(uci, rule_type = None) -> list:
    """
    Get all rules from firewall config

    Args:
        uci: EUci pointer
        rule_type: optional rule type to filter, must be one of 'input', 'output' or 'forward'

    Returns:
        a list of all rules
    """
    rules = []
    i = 0
    for section in uci.get_all("firewall"):
        if uci.get('firewall', section) == 'rule':
            rule = uci.get_all('firewall', section)
            rule['id'] = section
            rule['index'] = i
            if not rule_type:
                rules.append(enrich_rule(uci, rule))
            else:
                if rule_type =='forward' and is_forward_rule(rule):
                   rules.append(enrich_rule(uci, rule))
                   rule['active_zone'] = is_zone(uci, rule.get('src','*')) and is_zone(uci, rule.get('dest','*')) 
                elif rule_type =='input' and is_input_rule(rule):
                   rules.append(enrich_rule(uci, rule))
                   rule['active_zone'] = is_zone(uci, rule.get('src','*'))
                elif rule_type =='output' and is_output_rule(rule):
                   rules.append(enrich_rule(uci, rule))
                   rule['active_zone'] = is_zone(uci, rule.get('dest','*'))
        i += 1
    return rules

def list_forward_rules(uci) -> list:
    """
    Get all forward rules from firewall config

    Args:
        uci: EUci pointer

    Returns:
        a list of all forward rules
    """
    return list_rules(uci, 'forward')


def list_output_rules(uci) -> list:
    """
    Get all output rules from firewall config

    Args:
        uci: EUci pointer

    Returns:
        a list of all output rules
    """
    return list_rules(uci, 'output')


def list_input_rules(uci) -> list:
    """
    Get all input rules from firewall config

    Args:
        uci: EUci pointer

    Returns:
        a list of all input rules
    """
    return list_rules(uci, 'input')


def list_service_suggestions():
    """
    Get all services from /etc/services

    Returns:
        a list of all services, each service is a dict with keys id, port, proto
    """
    services = {}
    if os.path.isfile('/etc/services'):
        with open('/etc/services', 'r') as fp:
            for line in fp:
                if line.startswith('#'):
                    continue
                try:
                    tmp = line.split()
                    name = tmp[0]
                    (port, proto) = tmp[1].split('/')
                except Exception as e:
                    continue
                if port not in services:
                    services[port] = {"id": name, "proto": [proto]}
                else:
                    services[port]['proto'].append(proto)
    else:
        return []
    ret = []
    for port in services:
        service = services[port]
        service['port'] = int(port)
        ret.append(service)
    return ret

def list_active_leases():
    """
    Get all active leases from /tmp/dhcp.leases

    Returns:
        a list of all active leases, each lease is a dict with keys value, label, type
    """
    ret = []
    if os.path.isfile("/tmp/dhcp.leases"):
        with open("/tmp/dhcp.leases", "r") as fp:
            for line in fp.readlines():
                line = line.strip()
                if not line:
                    continue
                tmp = line.split(" ")
                if tmp[3] != "*":
                    ret.append({"value": tmp[2], "label": tmp[3], 'type': 'lease'})
    return ret

def list_host_suggestions(uci):
    """
    Get all hosts from dhcp and network config

    Args:
        uci: EUci pointer

    Returns:
        a list of all hosts, each host is a dict with keys value, label, type
    """
    ret = []
    for section in uci.get_all("dhcp"):
        if uci.get("dhcp", section, "ip", default=None):
            ret.append({"value": uci.get("dhcp", section, "ip"), "label": uci.get("dhcp", section, "name"), "type": uci.get("dhcp", section)})
    for section in uci.get_all("network"):
        ip = uci.get("network", section, "ipaddr", default=None)
        if ip and ip != '127.0.0.1':
            ret.append({"value": uci.get("network", section, "ipaddr"), "label": section, "type": "network"})
        if uci.get("network", section, "ip6addr", default=None):
            ret.append({"value": uci.get("network", section, "ip6addr"), "label": section, "type": "network"})
    ret = ret + list_active_leases()
    return ret

def list_object_suggestions(uci, expand = False):
    """
    Get all objects from objects config

    Args:
        uci: EUci pointer
        expand: if True, expand object details

    Returns:
        a list of all objects, each object is a dict with keys value, label, type
    """
    return objects.list_all_objects(uci, expand)

def validate_address_format(address: str) -> bool:
    """
    Validate address format.
    Valid formats are:
    - ip address
    - ip range like 192.168.100.1-192.168.100.10
    - ip cidr

    Args:
        address: address to validate

    Returns:
        True if address is valid, False otherwise
    """
    if not address:
        return True
    try:
        if '/' in address:
            (ip, cidr) = address.split('/')
            ipaddress.ip_address(ip)
            cidr = int(cidr)
            if cidr < 0 or cidr > 32:
                return False
        elif '-' in address:
            (start, end) = address.split('-')
            start = ipaddress.ip_address(start)
            end = ipaddress.ip_address(end)
            if start > end:
                return False
        else:
            ipaddress.ip_address(address)
    except:
        return False
    return True

def validate_port_format(port: str) -> bool:
    """
    Validate port format.

    Args:
        port: port to validate

    Returns:
        True if port is valid, False otherwise
    """
    if not port:
        return True
    try:
        if '-' in port:
            (start, end) = port.split('-')
            start = int(start)
            end = int(end)
            if start < 0 or start > 65535:
                return False
            if end < 0 or end > 65535:
                return False
            if start > end:
                return False
        elif ',' in port:
            for p in port.split(','):
                p = int(p)
                if p < 0 or p > 65535:
                    return False
        else:
            port = int(port)
            if port < 0 or port > 65535:
                return False
    except:
        return False
    return True

def validate_rule(uci, src: str, src_ip: list[str], dest: str, dest_ip: list[str], proto: list, dest_port: list[str], target: str, service: str, ns_src: str, ns_dst: str):
    """
    Validate rule.

    Args:
        src: source zone, must be zone name, not config name
        src_ip: a list of source ip
        dest: destination zone, must be zone name, not config name
        dest_ip: a list of destination ip
        proto: protocol, must be a list of protocols in "tcp", "udp", "udplite", "icmp", "esp", "ah", "sctp"
        dest_port: a list of destination ports, each element cna be be a port number, a comma-separated list of port numbers or a range with `-` (eg. 80-90)
        target: target, must be one of 'ACCEPT', 'REJECT', 'DROP', 'NOTRACK'
        service: service name
        ns_src: an object in the form `<database>/<id>`
        ns_dst: an object in the form `<database>/<id>`

    Raises:
        ValidationError: if rule is invalid
    """
    if ns_src:
        if not objects.object_exists(uci, ns_src):
            raise utils.ValidationError('ns_src', 'object_not_found', ns_src)
    else: # check source only if not using objects
        for s in src_ip:
            if not validate_address_format(s):
                raise utils.ValidationError('src_ip', 'invalid_format', s)
    if ns_dst:
        if not objects.object_exists(uci, ns_dst):
            raise utils.ValidationError('ns_dst', 'object_not_found', ns_dst)
    else: # check destiation only if not using objects
        for d in dest_ip:
            if not validate_address_format(d):
               raise utils.ValidationError('dest_ip', 'invalid_format', d)
    if ns_src and ns_dst and objects.is_domain_set(uci, ns_src) and objects.is_domain_set(uci, ns_dst):
        raise utils.ValidationError('ns_dst', 'domain_set_conflict', ns_dst)
    if target not in TARGETS:
        raise utils.ValidationError('target', 'invalid_target', target)
    if service and service != '*':
        if service == 'custom':
            for p in proto:
                if p not in PROTOCOLS:
                    raise utils.ValidationError('proto', 'invalid_proto', p)
            for port in dest_port:
                if not validate_port_format(port):
                    raise utils.ValidationError('dest_port', 'invalid_port', port)
        else:
            services = list(map(lambda x: x['id'], list_service_suggestions()))
            if services and service not in services:
                raise utils.ValidationError('ns_service', 'invalid_service', service)

def get_service_by_name(name: str) -> dict:
    """
    Get service by name.

    Args:
        name: service name

    Returns:
        service dict if service with name name exists, None otherwise
    """
    for service in list_service_suggestions():
        if service['id'] == name:
            return service
    return None

def setup_rule(uci, id: str, name: str, src: str, src_ip: list[str], dest: str, dest_ip: list[str], proto: list, dest_port: list[str], target: str, service: str,
                enabled: bool = True, log: bool = False, tag = [], ns_src: str = None, ns_dst: str = None, ns_link: str = None) -> None:
    """
    Set up a rule in the firewall config.

    Args:
            uci: EUci pointer
            id: id of the rule
            name: name of the rule
            src: source zone, must be zone name, not config name
            src_ip: a list of source IP addresses
            dest: destination zone, must be zone name, not config name
            dest_ip: a list of destination IP addresses
            proto: protocol, must be a list of protocols in "tcp", "udp", "udplite", "icmp", "esp", "ah", "sctp"
            dest_port: a list of destination ports, each element can be a port number, a comma-separated list of port numbers, or a range with `-` (e.g., 80-90)
            target: target, must be one of 'ACCEPT', 'REJECT', 'DROP', 'NOTRACK'
            service: service name
            enabled: if True, rule is enabled; if False, rule is disabled
            log: if True, log traffic
            tag: list of optional tags
            ns_src: an object in the form `<database>/<id>`
            ns_dst: an object in the form `<database>/<id>`
            ns_link: a string in the form `<database>/<id>` that is used to link this rule to another entity
    """
    uci.set('firewall', id, 'name', name)
    uci.set('firewall', id, 'src', src)
    uci.set('firewall', id, 'src_ip', src_ip)
    uci.set('firewall', id, 'dest', dest)
    uci.set('firewall', id, 'dest_ip', dest_ip)
    
    uci.set('firewall', id, 'target', target)
    if service and service != '*':
        if service == 'custom':
            uci.set('firewall', id, 'ns_service', 'custom')
            uci.set('firewall', id, 'proto', proto)
            uci.set('firewall', id, 'dest_port', " ".join(dest_port))
        else:
            uci.set('firewall', id, 'ns_service', service)
            service = get_service_by_name(service)
            uci.set('firewall', id, 'proto', service['proto'])
            uci.set('firewall', id, 'dest_port', service['port'])
    else:
        try:
            uci.set('firewall', id, 'ns_service', '*')
            uci.set('firewall', id, 'proto', 'all')
            uci.delete('firewall', id, 'dest_port')
        except:
            pass

    uci.set('firewall', id, 'enabled', '1' if enabled else '0')
    if log:
        uci.set('firewall', id, 'log', '1')
        if uci.get('firewall', id, 'log_limit', default=None) is None:
            # set default log limit, do not overwrite existing value
            log_opts = get_default_logging_options(uci)
            uci.set('firewall', id, 'log_limit', log_opts['rule_log_limit'])
    else:
        uci.set('firewall', id, 'log', '0')
        try:
            uci.delete('firewall', id, 'log_limit')
        except:
            pass
    uci.set('firewall', id, 'ns_tag', tag)
    if ns_src:
        uci.set('firewall', id, 'ns_src', ns_src)
    else:
        try:
            uci.delete('firewall', id, 'ns_src')
        except:
            pass
    if ns_dst:
        uci.set('firewall', id, 'ns_dst', ns_dst)
    else:
        try:
            uci.delete('firewall', id, 'ns_dst')
        except:
            pass
    if ns_link:
        uci.set('firewall', id, 'ns_link', ns_link)
    else:
        try:
            uci.delete('firewall', id, 'ns_link')
        except:
            pass
    uci.save('firewall')

def split_firewall_config(uci):
    """
    Split firewall config into sections.

    Args:
        uci: EUci pointer

    Returns:
        tuple of lists of sections, in the following order: defaults, zones, forwardings, other_rules, forward_rules, output_rules, input_rules
    """
    forward_rules = []
    output_rules = []
    input_rules = []
    other_rules = []
    zones = []
    forwardings = []
    defaults = []
    for section in uci.get_all("firewall"):
        record = uci.get_all("firewall", section)
        if uci.get('firewall', section) == 'rule':
            if is_forward_rule(record):
                forward_rules.append(section)
            elif is_input_rule(record):
                input_rules.append(section)
            elif is_output_rule(record):
                output_rules.append(section)
            else:
                other_rules.append(section)
        elif uci.get('firewall', section) == 'zone':
            zones.append(section)
        elif uci.get('firewall', section) == 'forwarding':
            forwardings.append(section)
        else:
            defaults.append(section)

    return (defaults, zones, forwardings, other_rules, forward_rules, output_rules, input_rules)


def reorder_firewall_config(uci):
    """
    Reorder firewall config, moving all rules at the bottom.
    The order in the file will be:
    - defaults and includes
    - zones
    - forwardings
    - forward rules
    - output rules
    - input rules

    Args:
        uci: EUci pointer
    """
    (defaults, zones, forwardings, other_rules, forward_rules, output_rules, input_rules) = split_firewall_config(uci)

    order = defaults + zones + forwardings + other_rules + forward_rules + output_rules + input_rules
    index = 0
    for section in order:
        subprocess.run(["uci", "-t", uci.savedir(), "-c", uci.confdir(), "reorder", f"firewall.{section}={index}"])
        index = index + 1
    uci.save('firewall')

def add_rule(uci, name: str, src: str, src_ip: list[str], dest: str, dest_ip: list[str], proto: list, dest_port: list[str], target: str, service: str,
            enabled: bool = True, log: bool = False, tag = [], add_to_top: bool = False, ns_src: str = None, ns_dst: str = None, ns_link: str = None) -> str:
    """
    Add rule to firewall config.

    Args:
        uci: EUci pointer
        id: id of rule to edit
        name: name of rule
        src: source zone, must be zone name, not config name
        src_ip: a list of source ip
        dest: destination zone, must be zone name, not config name
        dest_ip: a list of destination ip
        proto: protocol, must be a list of protocols in "tcp", "udp", "udplite", "icmp", "esp", "ah", "sctp"
        dest_port: a list of destination ports, each element cna be be a port number, a comma-separated list of port numbers or a range with `-` (eg. 80-90)
        target: target, must be one of 'ACCEPT', 'REJECT', 'DROP', 'NOTRACK'
        service: service name
        enabled: if True, rule is enabled, if False, rule is disabled
        log: if True, log traffic
        tag: list of optional tags
        add_to_top: if True, add rule to the top of the list, otherwise add to the bottom
        ns_src: an object in the form `<database>/<id>`
        ns_dst: an object in the form `<database>/<id>`
        ns_link: a string in the form `<database>/<id>` that is used to link this rule to another entity

    Returns:
        name of rule config that was added
    """
    validate_rule(uci, src, src_ip, dest, dest_ip, proto, dest_port, target, service, ns_src, ns_dst)
    rule = utils.get_random_id()
    uci.set('firewall', rule, 'rule')
    setup_rule(uci, rule, name, src, src_ip, dest, dest_ip, proto, dest_port, target, service, enabled, log, tag, ns_src, ns_dst, ns_link)
    reorder_firewall_config(uci)
    update_firewall_rules(uci) # expand objects and save

    if add_to_top:
        rule_type = uci.get_all('firewall', rule)
        if is_forward_rule(rule_type):
            ids = list(map(lambda x: x['id'], list_forward_rules(uci)))
            order_rules(uci, 'forward', [rule] + ids[:-1] )
        elif is_input_rule(rule_type):
            ids = list(map(lambda x: x['id'], list_input_rules(uci)))
            order_rules(uci, 'input', [rule] + ids[:-1] )
        elif is_output_rule(rule_type):
            ids = list(map(lambda x: x['id'], list_output_rules(uci)))
            order_rules(uci, 'output', [rule] + ids[:-1] )
    return rule

def edit_rule(uci, id: str, name: str, src: str, src_ip: list[str], dest: str, dest_ip: list[str], proto: list, dest_port: list[str], target: str, service: str, 
            enabled: bool = True, log: bool = False, tag = [], ns_src: str = None, ns_dst: str = None, ns_link: str = None) -> str:
    """
    Edit rule in firewall config.

    Args:
        uci: EUci pointer
        id: id of rule to edit
        name: name of rule
        src: source zone, must be zone name, not config name
        src_ip: a list of source ip
        dest: destination zone, must be zone name, not config name
        dest_ip: a list of destination ip
        proto: protocol, must be a list of protocols in "tcp", "udp", "udplite", "icmp", "esp", "ah", "sctp"
        dest_port: a list of destination ports, each element cna be be a port number, a comma-separated list of port numbers or a range with `-` (eg. 80-90)
        target: target, must be one of 'ACCEPT', 'REJECT', 'DROP', 'NOTRACK'
        service: service name
        enabled: if True, rule is enabled, if False, rule is disabled
        log: if True, log traffic
        tag: list of optional tags
        ns_src: an object in the form `<database>/<id>`
        ns_dst: an object in the form `<database>/<id>`
        ns_link: a string in the form `<database>/<id>` that is used to link this rule to another entity

    Returns:
        name of rule config that was edited
    """
    if not uci.get('firewall', id, default=None):
        raise utils.ValidationError("id", "rule_does_not_exists", id)  
    validate_rule(uci, src, src_ip, dest, dest_ip, proto, dest_port, target, service, ns_src, ns_dst)
    setup_rule(uci, id, name, src, src_ip, dest, dest_ip, proto, dest_port, target, service, enabled, log, tag, ns_src, ns_dst, ns_link)
    update_firewall_rules(uci) # expand objects and save
    return id

def list_nat_rules(uci) -> list:
    """
    Get all nat rules from firewall config

    Args:
        uci: EUci pointer

    Returns:
        a list of all nat rules
    """
    rules = []
    for section in uci.get_all("firewall"):
        if uci.get('firewall', section) == 'nat':
            rule = uci.get_all('firewall', section)
            rule['id'] = section
            rule.pop('proto', None)
            rules.append(rule)
    return rules

def add_nat_rule(uci, name: str, target: str, src: str = '*', src_ip: str = '', dest_ip: str = '', snat_ip: str = '', device: str = '') -> str:
    """
    Add nat rule to firewall config.

    Args:
        uci: EUci pointer
        name: name of rule
        target: target, must be one of 'SNAT', 'DNAT'
        src: source zone, must be zone name, not config name
        src_ip: source ip
        dest_ip: destination ip
        snat_ip: snat ip
        device: add nat rule just for specific device

    Returns:
        name of rule config that was added
    """
    if len(name) > 120:
        raise utils.ValidationError('name', 'name_too_long', name)
    if target not in ["ACCEPT", "MASQUERADE", "SNAT"]:
        raise utils.ValidationError('target', 'invalid_target', target)
    rule = utils.get_random_id()
    uci.set('firewall', rule, 'nat')
    uci.set('firewall', rule, 'name', name)
    uci.set('firewall', rule, 'target', target)
    uci.set('firewall', rule, 'src', src)
    uci.set('firewall', rule, 'src_ip', src_ip)
    uci.set('firewall', rule, 'dest_ip', dest_ip)
    uci.set('firewall', rule, 'snat_ip', snat_ip)
    uci.set('firewall', rule, 'proto', ["all"])
    uci.set('firewall', rule, 'device', device)
    uci.save('firewall')
    return rule

def edit_nat_rule(uci, id: str, name: str, target: str, src: str = '*', src_ip: str = '', dest_ip: str = '', snat_ip: str = '', device: str = '') -> str:
    """
    Edit nat rule in firewall config.

    Args:
        uci: EUci pointer
        id: id of rule to edit
        name: name of rule
        target: target, must be one of 'SNAT', 'DNAT'
        src: source zone, must be zone name, not config name
        src_ip: source ip
        dest_ip: destination ip
        snat_ip: snat ip
        src_device: source device
        device: add nat rule just for specific device

    Returns:
        name of rule config that was edited
    """
    if not uci.get('firewall', id, default=None):
        raise utils.ValidationError("id", "rule_does_not_exists", id)
    if len(name) > 120:
        raise utils.ValidationError('name', 'name_too_long', name)
    if target not in ["ACCEPT", "MASQUERADE", "SNAT"]:
        raise utils.ValidationError('target', 'invalid_target', target)
    uci.set('firewall', id, 'name', name)
    uci.set('firewall', id, 'target', target)
    uci.set('firewall', id, 'src', src)
    uci.set('firewall', id, 'src_ip', src_ip)
    uci.set('firewall', id, 'dest_ip', dest_ip)
    uci.set('firewall', id, 'snat_ip', snat_ip)
    uci.set('firewall', id, 'device', device)
    uci.save('firewall')
    return id

def delete_nat_rule(uci, id: str) -> str:
    """
    Delete nat rule from firewall config.

    Args:
        uci: EUci pointer
        id: id of rule to delete

    Returns:
        name of rule config that was deleted
    """
    if not uci.get('firewall', id, default=None):
        raise utils.ValidationError("id", "rule_does_not_exists", id)
    uci.delete('firewall', id)
    uci.save('firewall')
    return id

def list_netmap_rules(uci) -> list:
    """
    Get all netmap rules from netmap config

    Args:
        uci: EUci pointer

    Returns:
        a list of all netmap rules
    """
    rules = []
    for section in uci.get_all("netmap"):
        if uci.get('netmap', section) == 'rule':
            rule = uci.get_all('netmap', section)
            rule['id'] = section
            rules.append(rule)
    return rules

def validate_netmap_rule(name: str, src: str, dest: str, map_from: str, map_to: str):
    if len(name) > 120:
        raise utils.ValidationError('name', 'name_too_long', name)
    if src and dest:
        raise utils.ValidationError('src', 'src_or_dest', src)
    try:
        ipaddress.ip_network(map_from)
    except:
        raise utils.ValidationError('map_from', 'map_from_invalid_format', map_from)
    try:
        ipaddress.ip_network(map_to)
    except:
        raise utils.ValidationError('map_to', 'map_to_invalid_format', map_to)
    if src:
        try:
            ipaddress.ip_network(src)
        except:
            raise utils.ValidationError('src', 'src_invalid_format', src)
    if dest:
        try:
            ipaddress.ip_network(dest)
        except:
            raise utils.ValidationError('dest', 'dest_invalid_format', dest)


def add_netmap_rule(uci, name: str, src: str, dest: str, device_in: list[str], device_out: list[str], map_from: str, map_to: str) -> str:
    """
    Add netmap rule to netmap config.

    Args:
        uci: EUci pointer
        name: name of rule
        src: source zone, must be zone name, not config name
        dest: destination zone, must be zone name, not config name
        device_in: list of incoming network interfaces
        device_out: list of outgoing network interfaces
        map_from: source network address
        map_to: destination network address

    Returns:
        name of rule config that was added
    """
    validate_netmap_rule(name, src, dest, map_from, map_to)
    rule = utils.get_random_id()
    uci.set('netmap', rule, 'rule')
    uci.set('netmap', rule, 'name', name)
    uci.set('netmap', rule, 'src', src)
    uci.set('netmap', rule, 'dest', dest)
    uci.set('netmap', rule, 'device_in', device_in)
    uci.set('netmap', rule, 'device_out', device_out)
    uci.set('netmap', rule, 'map_from', map_from)
    uci.set('netmap', rule, 'map_to', map_to)
    uci.save('netmap')
    return rule

def edit_netmap_rule(uci, id: str, name: str, src: str, dest: str, device_in: list[str], device_out: list[str], map_from: str, map_to: str) -> str:
    """
    Edit netmap rule in netmap config.

    Args:
        uci: EUci pointer
        id: id of rule to edit
        name: name of rule
        src: source zone, must be zone name, not config name
        dest: destination zone, must be zone name, not config name
        device_in: list of incoming network interfaces
        device_out: list of outgoing network interfaces
        map_from: source network address
        map_to: destination network address

    Returns:
        name of rule config that was edited
    """
    validate_netmap_rule(name, src, dest, map_from, map_to)
    uci.set('netmap', id, 'name', name)
    uci.set('netmap', id, 'src', src)
    uci.set('netmap', id, 'dest', dest)
    uci.set('netmap', id, 'device_in', device_in)
    uci.set('netmap', id, 'device_out', device_out)
    uci.set('netmap', id, 'map_from', map_from)
    uci.set('netmap', id, 'map_to', map_to)
    uci.save('netmap')
    return id

def delete_netmap_rule(uci, id: str) -> str:
    """
    Delete netmap rule from netmap config.

    Args:
        uci: EUci pointer
        id: id of rule to delete

    Returns:
        name of rule config that was deleted
    """
    if not uci.get('netmap', id, default=None):
        raise utils.ValidationError("id", "rule_does_not_exists", id)
    uci.delete('netmap', id)
    uci.save('netmap')
    return id

def list_netmap_devices(uci) -> list:
    """
    Get all network devices from ip command

    Args:
        uci: EUci pointer

    Returns:
        a list of all network devices
    """
    devices = []
    try:
        output = subprocess.run(["ip", "-j", "link", "show"], capture_output=True, text=True)
        data = json.loads(output.stdout)
        for device in data:
            if device.get('ifname') != 'lo' and not device.get('ifname').startswith('ifb-'):
                devices.append({"device": device['ifname'], "interface": utils.get_interface_from_device(uci, device['ifname'])})
    except:
        pass
    return devices

# Objects

def update_redirect_rules(uci):
    """
    Update redirect rules with ipset field set and ns_src set.

    Args:
        uci: EUci pointer
        changed_sections: list of changed objects, each object is in the form of `<database>/<id>`
    """
    for section in utils.get_all_by_type(uci, 'firewall', 'redirect'):
        # fetch ns_src and ns_dst for each redirect rule
        ns_src = uci.get('firewall', section, 'ns_src', default=None)
        ns_dst = uci.get('firewall', section, 'ns_dst', default=None)
        if ns_dst:
            # if ns_dst is set, fetch the ip address from the object and set it in the redirect rule
            # in case that the redirect is then deleted, no action is needed
            ipaddr = objects.get_object_ip(uci, ns_dst)
            if ipaddr:
                uci.set('firewall', section, 'dest_ip', ipaddr)
        if ns_src:
            # if ns_src is set, check if it is a domain set
            database, id = ns_src.split('/')
            obj_type = uci.get(database, id)
            if database == "objects" and obj_type == "domain":
                # if it is a domain set, set the ipset field in the redirect rule
                ipsets = objects.get_domain_set_ipsets(uci, id)
                uci.set('firewall', section, 'ipset', f"{ipsets['firewall']} src_net")
                try:
                    uci.delete('firewall', f"{section}_ipset")
                except:
                    pass
            else:
                # create a full ipset configuration for the redirect rule
                uci.set('firewall', section, 'ipset', f"{section}_ipset")
                uci.set('firewall', f"{section}_ipset", "ipset")
                uci.set('firewall', f"{section}_ipset", "name", f"{section}_ipset")
                uci.set('firewall', f"{section}_ipset", "match", "src_net")
                uci.set('firewall', f"{section}_ipset", "enabled", "1")
                uci.set('firewall', f"{section}_ipset", 'ns_link', f"firewall/{section}")
                uci.set('firewall', f"{section}_ipset", "entry", objects.get_object_ips(uci, ns_src))

    uci.save('firewall')

def update_firewall_rules(uci):
    """
    Update firewall rules with ipset field set and ns_src set.

    Args:
        uci: EUci pointer
    """
    for section in utils.get_all_by_type(uci, 'firewall', 'rule'):
        keep_ipset = False
        ns_src = uci.get('firewall', section, 'ns_src', default=None)
        ns_dst = uci.get('firewall', section, 'ns_dst', default=None)
        name = uci.get('firewall', section, 'name', default=None)
        if ns_src:
            if objects.is_domain_set(uci, ns_src):
                keep_ipset = True
                id = ns_src.split('/')[1]
                ipsets = objects.get_domain_set_ipsets(uci, id)
                uci.set('firewall', section, 'ipset', f"{ipsets['firewall']} src")
                try:
                    uci.delete('firewall', section, 'src_ip')
                except:
                    pass
            else:
                ipaddr = objects.get_object_ips(uci, ns_src)
                if ipaddr:
                    uci.set('firewall', section, 'src_ip', ipaddr)

        if ns_dst:
            if objects.is_domain_set(uci, ns_dst):
                keep_ipset = True
                id = ns_dst.split('/')[1]
                ipsets = objects.get_domain_set_ipsets(uci, id)
                uci.set('firewall', section, 'ipset', f"{ipsets['firewall']} dst")
                try:
                    uci.delete('firewall', section, 'dest_ip')
                except:
                    pass
            else:
                ipaddr = objects.get_object_ips(uci, ns_dst)
                if ipaddr:
                    uci.set('firewall', section, 'dest_ip', ipaddr)

        # delete ipset field if no domains are set
        if not keep_ipset:
            try:
                uci.delete('firewall', section, 'ipset')
            except:
                pass
    uci.save('firewall')

def list_object_suggestions(uci, expand = False):
    """
    Get all objects from objects config

    Args:
        uci: EUci pointer
        expand: if True, expand object details

    Returns:
        a list of all objects, each object is a dict with keys value, label, type
    """
    return objects.list_all_objects(uci, expand)

def get_default_logging_options(uci):
    """
    Get default logging options

    Args:
        uci: EUci pointer

    Returns:
        a dict with keys rule_log_limit, zone_log_limit, redirect_log_limit
    """

    ret = {}
    defaults = uci.get('firewall', 'ns_defaults', 'rule_log_limit', default=None)
    if defaults is None:
        # Set defaults, if needed
        uci.set('firewall', 'ns_defaults', 'defaults')
        uci.set('firewall', 'ns_defaults', 'rule_log_limit', '1/s')
        uci.set('firewall', 'ns_defaults', 'zone_log_limit', '5/s')
        uci.set('firewall', 'ns_defaults', 'redirect_log_limit', '1/s')
        uci.save('firewall')

    for key in ['rule_log_limit', 'zone_log_limit', 'redirect_log_limit']:
        ret[key] = uci.get('firewall', 'ns_defaults', key)

    return ret

def apply_default_logging_options(uci):
    """
    Walk all rules, zones and redirect rules and set logging options to default

    Args:
        uci: EUci pointer

    Returns:
        None
    """
    log_opts = get_default_logging_options(uci)
    for section in uci.get_all("firewall"):
        if uci.get('firewall', section) == 'rule' and uci.get('firewall', section, 'log', default='0') == '1':
            uci.set('firewall', section, 'log_limit', log_opts['rule_log_limit'])
        elif uci.get('firewall', section) == 'zone' and uci.get('firewall', section, 'log', default='0') == '1':
            uci.set('firewall', section, 'log_limit', log_opts['zone_log_limit'])
        elif uci.get('firewall', section) == 'redirect' and uci.get('firewall', section, 'log', default='0') == '1':
            uci.set('firewall', section, 'log_limit', log_opts['redirect_log_limit'])
    uci.save('firewall')