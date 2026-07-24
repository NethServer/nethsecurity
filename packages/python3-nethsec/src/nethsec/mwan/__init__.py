#!/usr/bin/python3

#
# Copyright (C) 2023 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""
Mwan utilities
"""


import json
import subprocess

import uci
from euci import EUci

from nethsec import utils, objects
from nethsec.utils import ValidationError

def _is_valid_src(e_uci: EUci, database_id: str):
    """
    Validate the given object for source.
    Source objects can be only:
    - dhcp reservation
    - dns domain
    - vpn user
    - a singleton host set

    Args:
        e_uci: EUci instance
        database_id: id of object

    Returns:
        True if object is valid, False otherwise
    """
    if objects.is_host_set(e_uci, database_id):
        return objects.is_singleton_host_set(e_uci, database_id, allow_cidr=True)
        
    return objects.is_host(e_uci, database_id) or objects.is_domain(e_uci, database_id) or objects.is_vpn_user(e_uci, database_id)

def _is_valid_dst(e_uci: EUci, database_id: str):
    """
    Validate the given object for destination.
    Destination objects can be only:
    - dhcp reservation
    - dns domain
    - vpn user
    - a singleton host set

    Args:
        e_uci: EUci instance
        database_id: id of object

    Returns:
        True if object is valid, False otherwise
    """
    if objects.is_host_set(e_uci, database_id):
        return objects.is_singleton_host_set(e_uci, database_id, allow_cidr=True)

    return objects.is_host(e_uci, database_id) or objects.is_domain(e_uci, database_id) or objects.is_vpn_user(e_uci, database_id)

def __generate_metric(e_uci: EUci) -> int:
    """
    Generates a metric for an interface.

    Args:
        e_uci: EUci instance

    Returns:
        first metric that is not present in interface_metrics
    """
    next_metric = 20
    for interface in utils.get_all_by_type(e_uci, 'network', 'interface').values():
        if 'metric' in interface:
            next_metric = max(next_metric, int(interface['metric']))
    return next_metric + 10


def __set_interface_defaults(e_uci: EUci, name: str):
    default_interface_config = e_uci.get_all('ns-api', 'defaults_mwan')
    e_uci.set('mwan3', name, 'initial_state', default_interface_config['initial_state'])
    e_uci.set('mwan3', name, 'family', default_interface_config['protocol'])
    e_uci.set('mwan3', name, 'track_ip', default_interface_config['track_ip'])
    e_uci.set('mwan3', name, 'track_method', default_interface_config['tracking_method'])
    e_uci.set('mwan3', name, 'reliability', default_interface_config['tracking_reliability'])
    e_uci.set('mwan3', name, 'count', default_interface_config['ping_count'])
    e_uci.set('mwan3', name, 'size', default_interface_config['ping_size'])
    e_uci.set('mwan3', name, 'max_ttl', default_interface_config['ping_max_ttl'])
    e_uci.set('mwan3', name, 'timeout', default_interface_config['ping_timeout'])
    e_uci.set('mwan3', name, 'interval', default_interface_config['ping_interval'])
    e_uci.set('mwan3', name, 'failure_interval', default_interface_config['ping_failure_interval'])
    e_uci.set('mwan3', name, 'recovery_interval', default_interface_config['ping_recovery_interval'])
    e_uci.set('mwan3', name, 'down', default_interface_config['interface_down_threshold'])
    e_uci.set('mwan3', name, 'up', default_interface_config['interface_up_threshold'])


def __store_interface(e_uci: EUci, name: str) -> tuple[bool, bool]:
    """
    Stores interface configuration for mwan3 and network, not suited to be used outside store_policy.

    Args:
        e_uci: EUci instance
        name: name of interface

    Returns:
        tuple of booleans, first one indicates if mwan interface was created, second one indicates if metric was added
        to network interface

    Raises:
        ValidationError: if interface name is not defined in /etc/config/network
    """
    # checking if interface is configured
    try:
        e_uci.get('network', name)
    except uci.UciExceptionNotFound:
        raise ValidationError('name', 'invalid', name)

    created_interface = False
    # if no interface with name exists, create one with defaults
    if e_uci.get('mwan3', name, default=None) is None:
        created_interface = True
        # fetch default configuration and set interface
        e_uci.set('mwan3', name, 'interface')
        e_uci.set('mwan3', name, 'enabled', '1')
        __set_interface_defaults(e_uci, name)

    added_metric = False
    # avoid adding metric if already present
    if e_uci.get('network', name, 'metric', default=None) is None:
        added_metric = True
        # generate metric
        metric = __generate_metric(e_uci)
        # configure metric for interface
        e_uci.set('network', name, 'metric', metric)
    return created_interface, added_metric


def __store_member(e_uci: EUci, interface_name: str, metric: int, weight: int) -> tuple[str, bool]:
    """
    Stores member configuration for mwan3, not suited to be used outside store_policy.

    Args:
        e_uci: EUci instance
        interface_name: name of interface to link the member to
        metric: metric of the member
        weight: weight of the member

    Returns:
        tuple of string and boolean, first one is the generated name of the member, second one indicates if the member
        was created
    """
    member_config_name = utils.get_id(f'{interface_name}_M{metric}_W{weight}')
    changed = False
    if e_uci.get('mwan3', member_config_name, default=None) is None:
        changed = True
        e_uci.set('mwan3', member_config_name, 'member')
        e_uci.set('mwan3', member_config_name, 'interface', interface_name)
        e_uci.set('mwan3', member_config_name, 'metric', metric)
        e_uci.set('mwan3', member_config_name, 'weight', weight)
    return member_config_name, changed


def store_rule(e_uci: EUci, name: str, policy: str, protocol: str = None,
               source_address: str = None, source_port: str = None,
               destination_address: str = None, destination_port: str = None, sticky: bool = False,
               ns_src: str = None, ns_dst: str = None) -> str:
    """
    Stores a rule for mwan3

    Args:
        e_uci: EUci instance
        name: name of the rule, must be unique
        policy: policy to use for the rule, must be already set
        protocol: must be one of tcp, udp, icmp or all, defaults to 'all'
        source_address: source addresses to match
        source_port: source ports to match or range
        destination_address: destination addresses to match
        destination_port: destination ports to match or range
        sticky: whether to use sticky connections
        ns_src: source object, it overrides source_address
        ns_dst: destination object, it overrides destination_address

    Returns:
        name of the rule created

    Raises:
        ValidationError if name is not unique, policy is not valid or length get_id > 15
    """
    # check if the rule length  is not more than 15 characters: 12 from user and 3 from get_id prefix
    if len(name) > 12:
        # get_id add 3 more chars (ns_) to the name
        raise ValidationError('name', 'length_12_max', name)
    rule_config_name = utils.get_id(name.lower(), 15)
    rules = utils.get_all_by_type(e_uci, 'mwan3', 'rule').keys()
    if e_uci.get('mwan3', rule_config_name, default=None) is not None:
        raise ValidationError('name', 'unique', name)
    if e_uci.get('mwan3', policy, default=None) is None:
        raise ValidationError('policy', 'invalid', policy)
    if ns_src and not _is_valid_src(e_uci, ns_src):
        raise ValidationError('ns_src', 'invalid_object', ns_src)
    if ns_dst and not _is_valid_dst(e_uci, ns_dst):
        raise ValidationError('ns_dst', 'invalid_object', ns_dst)

    e_uci.set('mwan3', rule_config_name, 'rule')
    e_uci.set('mwan3', rule_config_name, 'label', name)
    e_uci.set('mwan3', rule_config_name, 'use_policy', policy)
    # test if sticky is True or False, if not raise an error
    if type(sticky) is not bool:
        raise ValidationError('sticky', 'sticky_not_valid', sticky)
    e_uci.set('mwan3', rule_config_name, 'sticky', sticky)
    if protocol is not None:
        e_uci.set('mwan3', rule_config_name, 'proto', protocol)
    if source_address is not None:
        e_uci.set('mwan3', rule_config_name, 'src_ip', source_address)
    if source_port is not None:
        e_uci.set('mwan3', rule_config_name, 'src_port', source_port.replace('-', ':'))
    if destination_address is not None:
        e_uci.set('mwan3', rule_config_name, 'dest_ip', destination_address)
    if destination_port is not None:
        e_uci.set('mwan3', rule_config_name, 'dest_port', destination_port.replace('-', ':'))
    if ns_src is not None:
        e_uci.set('mwan3', rule_config_name, 'ns_src', ns_src)
    if ns_dst is not None:
        e_uci.set('mwan3', rule_config_name, 'ns_dst', ns_dst)

    order_rules(e_uci, [rule_config_name] + list(rules))
    update_rules(e_uci) # update rules with objects and save mwan3 config
    return f'mwan3.{rule_config_name}'


def store_policy(e_uci: EUci, name: str, interfaces: list[dict]) -> list[str]:
    """
    Stores a policy for mwan3, takes care of creating interfaces and members.

    Args:
        e_uci: EUci instance
        name: name of policy
        interfaces: list of interfaces to add to policy, must have name, metric and weight fields

    Returns:
        list of changed configuration

    Raises:
        ValidationError: if name is not unique or length or get_id > 15
    """
    changed_config = []
    if len(name) > 12:
        # get_id add 3 more chars (ns_) to the name
        raise ValidationError('name', 'length_12_max', name)
    # generate policy name
    policy_config_name = utils.get_id(name.lower(), 15)
    #  test length of policy name
    # make sure name is not something that already exists
    if e_uci.get('mwan3', policy_config_name, default=None) is not None:
        raise ValidationError('name', 'unique', name)
    # generate policy config with corresponding name
    e_uci.set('mwan3', policy_config_name, 'policy')
    e_uci.set('mwan3', policy_config_name, 'label', name)
    changed_config.append(f'mwan3.{policy_config_name}')

    member_names = __add_interfaces(e_uci, interfaces, changed_config)

    e_uci.set('mwan3', policy_config_name, 'use_member', member_names)

    if len(utils.get_all_by_type(e_uci, 'mwan3', 'rule')) == 0:
        changed_config.append(store_rule(e_uci, 'Default Rule', policy_config_name))

    # default policy must have a last_resort field
    if len(utils.get_all_by_type(e_uci, 'mwan3', 'policy')) == 1:
        e_uci.set('mwan3', policy_config_name, 'last_resort', 'default')

    e_uci.save('mwan3')
    e_uci.save('network')
    return changed_config


def __fetch_interface_status(interface_name: str) -> str:
    try:
        output = (subprocess.run([
            'ubus',
            'call',
            'mwan3',
            'status',
            '{"section": "interfaces"}'
        ], capture_output=True, check=True)
                  .stdout.decode('utf-8'))
        decoded_output = json.JSONDecoder().decode(output)
        return decoded_output['interfaces'][interface_name]['status']
    except:
        return 'unknown'


def __parse_member(e_uci: EUci, member_name: str) -> dict:
    """
    Parses a member configuration and returns formatted data.

    Args:
        e_uci: EUci instance
        member_name: member name

    Returns:
        dict with member data
    """
    member_data = e_uci.get_all('mwan3', member_name)
    return {
        'name': member_name,
        'interface': member_data['interface'],
        'metric': member_data['metric'],
        'weight': member_data['weight'],
        'status': __fetch_interface_status(member_data['interface'])
    }


def index_policies(e_uci: EUci) -> list[dict]:
    """
    Returns a list of policies with their members, interfaces and metrics/weights.

    Args:
        e_uci: EUci instance

    Returns:
        list of dicts with policy data
    """
    data = []
    policies = utils.get_all_by_type(e_uci, 'mwan3', 'policy')
    # iterate over policies
    for policy_name in policies.keys():
        policy = policies[policy_name]
        policy_data = {
            'name': policy_name,
        }
        # add label only if present
        if 'label' in policy:
            policy_data['label'] = policy['label']

        # add members
        members = []
        if 'use_member' in policy:
            policy_data['members'] = {}
            for member in policy['use_member']:
                members.append(__parse_member(e_uci, member))

        # infer policy type by metrics
        metrics = [int(member['metric']) for member in members]
        if len(metrics) == 1:
            policy_data['type'] = 'custom'
        elif all(metric == metrics[0] for metric in metrics):
            policy_data['type'] = 'balance'
        elif all(metrics.index(metric) == key for key, metric in enumerate(metrics)):
            policy_data['type'] = 'backup'
        else:
            policy_data['type'] = 'custom'

        unique_metrics = list(set(metrics))
        for unique_metric in unique_metrics:
            policy_data['members'][unique_metric] = list(filter(lambda x: x['metric'] == str(unique_metric), members))

        # append policy to data
        data.append(policy_data)
    return data


def __add_interfaces(e_uci: EUci, interfaces: list[dict], changed_config: list[str] = None) -> list[str]:
    """
    Add interfaces to policy, takes care of creating interfaces and members.

    Args:
        e_uci: euci instance
        interfaces: list of interfaces to add
        changed_config: array of changed configuration

    Returns:
        list of member names added to policy

    Raises:
        ValidationError: if interface name is not defined in /etc/config/network
    """
    if changed_config is None:
        changed_config = list()
    member_names: list[str] = []
    for interface in interfaces:
        try:
            added_mwan_interface, updated_interface = __store_interface(e_uci, interface['name'])
        except ValidationError:
            raise ValidationError('interfaces', 'invalid', interface['name'])
        if added_mwan_interface:
            changed_config.append(f'mwan3.{interface["name"]}')
        if updated_interface:
            changed_config.append(f'network.{interface["name"]}')

        member_config_name, member_created = __store_member(e_uci,
                                                            interface['name'],
                                                            interface['metric'],
                                                            interface['weight'])
        member_names.append(member_config_name)
        if member_created:
            changed_config.append(f'mwan3.{member_config_name}')

    return member_names


def edit_policy(e_uci: EUci, name: str, label: str, interfaces: list[dict]) -> list[str]:
    """
    Edits a mwan3 policy.

    Args:
        e_uci: euci instance
        name: name of policy to edit
        label: policy label
        interfaces: dict of interfaces to add to policy

    Returns:
        list of changed mwan3 entries

    Raises:
        ValidationError: if name is not valid
    """
    if e_uci.get('mwan3', name, default=None) is None:
        raise ValidationError('name', 'invalid', name)
    changed_config = []
    if label != e_uci.get_all('mwan3', name)['label']:
        e_uci.set('mwan3', name, 'label', label)
        changed_config.append(f'mwan3.{name}')

    member_names = __add_interfaces(e_uci, interfaces, changed_config)

    e_uci.set('mwan3', name, 'use_member', member_names)

    e_uci.save('mwan3')
    e_uci.save('network')
    return changed_config


def delete_policy(e_uci: EUci, name: str) -> list[str]:
    """
    Deletes a mwan3 policy.

    Args:
        e_uci: euci instance
        name: name of policy to delete

    Returns:
        list of deleted mwan3 entries
    """
    if e_uci.get('mwan3', name, default=None) is None:
        raise ValidationError('name', 'invalid', name)
    e_uci.delete('mwan3', name)
    e_uci.save('mwan3')
    return [f'mwan3.{name}']


def index_rules(e_uci: EUci) -> list[dict]:
    """
    Returns a list of rules with their policies.

    Args:
        e_uci: euci instance

    Returns:
        parsed list of rules with assigned policy
    """
    data = []
    rules = utils.get_all_by_type(e_uci, 'mwan3', 'rule')
    for rule_key in rules.keys():
        rule_data = {}
        rule_value = rules[rule_key]
        rule_data['name'] = rule_key
        rule_data['policy'] = {}
        rule_data['policy']['name'] = rule_value['use_policy']
        if e_uci.get('mwan3', rule_value['use_policy'], default=None) is not None:
            rule_data['policy']['label'] = utils.get_all_by_type(e_uci, 'mwan3', 'policy')[rule_value['use_policy']].get('label')
        if 'label' in rule_value:
            rule_data['label'] = rule_value['label']
        if 'proto' in rule_value:
            rule_data['protocol'] = rule_value['proto']
        if 'src_ip' in rule_value:
            rule_data['source_address'] = rule_value['src_ip']
        if 'src_port' in rule_value:
            rule_data['source_port'] = rule_value['src_port'].replace(':', '-')
        if 'dest_ip' in rule_value:
            rule_data['destination_address'] = rule_value['dest_ip']
        if 'dest_port' in rule_value:
            rule_data['destination_port'] = rule_value['dest_port'].replace(':', '-')
        if 'sticky' in rule_value:
            rule_data['sticky'] = rule_value['sticky'] == '1'
        if 'ns_src' in rule_value:
            rule_data['ns_src'] = rule_value['ns_src']
        if 'ns_dst' in rule_value:
            rule_data['ns_dst'] = rule_value['ns_dst']

        data.append(rule_data)
    return data


def order_rules(e_uci: EUci, rules: list[str]) -> list[str]:
    """
    Orders mwan3 rules, moves everything else but rules to the end of the list.

    Args:
        e_uci: euci instance
        rules: which order to put rules

    Returns:
        list of ordered mwan3 entries

    Raises:
        ValidationError: if a rule is not present in /etc/config/mwan3
    """
    for rule in utils.get_all_by_type(e_uci, 'mwan3', 'rule').keys():
        if rule not in rules:
            raise ValidationError('rules', 'missing', rule)

    order: list[str] = []

    for key in e_uci.get_all('mwan3').keys():
        if key not in rules:
            order.append(key)

    order.extend(rules)

    subprocess.run([
        'ubus',
        'call',
        'uci',
        'order',
        json.dumps({
            'config': 'mwan3',
            'sections': order,
        })
    ])

    e_uci.save('mwan3')
    return order


def delete_rule(e_uci: EUci, name: str):
    """
    Deletes a mwan3 rule.

    Args:
        e_uci: euci instance
        name: rule name to delete

    Returns:
        name of rule deleted
    """
    if e_uci.get('mwan3', name, default=None) is None:
        raise ValidationError('name', 'invalid', name)

    e_uci.delete('mwan3', name)
    e_uci.save('mwan3')
    return f'mwan3.{name}'


def edit_rule(e_uci: EUci, name: str, policy: str, label: str, protocol: str = None,
              source_address: str = None, source_port: str = None,
              destination_address: str = None, destination_port: str = None, sticky: bool = False,
              ns_src: str = None, ns_dst: str = None):
    """
    Edits a mwan3 rule.

    Args:
        e_uci: EUci instance
        name: rule name
        policy: policy to use for the rule
        label: rule label
        protocol: protocol in which the rule applies
        source_address: CIDR notation of source address
        source_port: port or port range
        destination_address: CIDR notation of destination address
        destination_port: port or port range
        sticky: whether to use sticky connections
        ns_src: source object, it overrides source_address
        ns_dst: destination object, it overrides destination_address

    Raises:
        ValidationError: if name is not valid or policy is not valid
    """
    if e_uci.get('mwan3', name, default=None) is None:
        raise ValidationError('name', 'invalid', name)

    if e_uci.get('mwan3', policy, default=None) is None:
        raise ValidationError('policy', 'invalid', policy)
    if ns_src and not _is_valid_src(e_uci, ns_src):
        raise ValidationError('ns_src', 'invalid_object', ns_src)
    if ns_dst and not _is_valid_dst(e_uci, ns_dst):
        raise ValidationError('ns_dst', 'invalid_object', ns_dst)
    e_uci.set('mwan3', name, 'use_policy', policy)
    e_uci.set('mwan3', name, 'label', label)
    # test if sticky is True of False, if not raise an error
    if type(sticky) is not bool:
        raise ValidationError('sticky', 'sticky_not_valid', sticky)
    e_uci.set('mwan3', name, 'sticky', sticky)
    if protocol is not None:
        e_uci.set('mwan3', name, 'proto', protocol)
        if protocol != 'tcp' and protocol != 'udp':
            e_uci.delete('mwan3', name, 'src_port')
            e_uci.delete('mwan3', name, 'dest_port')
        else:
            if destination_port is not None:
                e_uci.set('mwan3', name, 'dest_port', destination_port.replace('-', ':'))
            if source_port is not None:
                e_uci.set('mwan3', name, 'src_port', source_port.replace('-', ':'))
    if source_address is not None:
        e_uci.set('mwan3', name, 'src_ip', source_address)
    else:
        e_uci.delete('mwan3', name, 'src_ip')
    if destination_address is not None:
        e_uci.set('mwan3', name, 'dest_ip', destination_address)
    else:
        e_uci.delete('mwan3', name, 'dest_ip')
    if ns_src is not None:
        e_uci.set('mwan3', name, 'ns_src', ns_src)
    else:
        e_uci.delete('mwan3', name, 'ns_src')
    if ns_dst is not None:
        e_uci.set('mwan3', name, 'ns_dst', ns_dst)
    else:
        e_uci.delete('mwan3', name, 'ns_dst')
    update_rules(e_uci) # update rules with objects and save mwan3 config
    return f'mwan3.{name}'


def clear_config(e_uci: EUci):
    """
    Clears mwan3 configuration.

    Args:
        e_uci: euci instance
    """
    for entry in e_uci.get_all('mwan3'):
        if entry != 'globals':
            e_uci.delete('mwan3', entry)

    e_uci.save('mwan3')


def set_default_config(e_uci: EUci, track_ip: list[str], ping_timeout: int, ping_interval: int,
                       ping_failure_interval: int, interface_down_threshold: int, interface_up_threshold: int):
    """
    Sets default configuration for mwan3.

    Args:
        e_uci: euci instance
        track_ip: list of IPs to track
        ping_timeout: timeout for ping
        ping_interval: interval between pings
        ping_failure_interval: interval between failed pings
        interface_down_threshold: threshold for interface down
        interface_up_threshold: threshold for interface up
    """
    e_uci.set('ns-api', 'defaults_mwan', 'track_ip', track_ip)
    e_uci.set('ns-api', 'defaults_mwan', 'ping_timeout', ping_timeout)
    e_uci.set('ns-api', 'defaults_mwan', 'ping_interval', ping_interval)
    e_uci.set('ns-api', 'defaults_mwan', 'ping_failure_interval', ping_failure_interval)
    e_uci.set('ns-api', 'defaults_mwan', 'interface_down_threshold', interface_down_threshold)
    e_uci.set('ns-api', 'defaults_mwan', 'interface_up_threshold', interface_up_threshold)

    for interface in utils.get_all_by_type(e_uci, 'mwan3', 'interface'):
        __set_interface_defaults(e_uci, interface)

    e_uci.save('ns-api')
    e_uci.save('mwan3')


def get_default_config(e_uci: EUci) -> dict:
    """
    Returns default configuration for mwan3.

    Args:
        e_uci: euci instance

    Returns:
        dict with default configuration
    """
    return e_uci.get_all('ns-api', 'defaults_mwan')


def update_rules(e_uci: EUci):
    """
    Updates mwan3 rules with objects addresses

    Args:
        e_uci: euci instance
    """
    for rule in utils.get_all_by_type(e_uci, 'mwan3', 'rule'):
        ns_src = e_uci.get('mwan3', rule, 'ns_src', default=None)
        ns_dst = e_uci.get('mwan3', rule, 'ns_dst', default=None)
        # both ns_src and ns_dst should be a singleton
        if ns_src:
            e_uci.set('mwan3', rule, 'src_ip', objects.get_object_ip(e_uci, ns_src))
        if ns_dst:
            # domain sets are not supported because mwan3 ipset functionality is broken on 23.05.
            e_uci.set('mwan3', rule, 'dest_ip', objects.get_object_ip(e_uci, ns_dst))

    e_uci.save('mwan3')
