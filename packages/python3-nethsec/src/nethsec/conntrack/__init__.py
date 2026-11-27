#!/usr/bin/python3

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""
Library for reading and managing network connections.
"""
import subprocess

from xml.etree import ElementTree
from xml.etree.ElementTree import Element


def __parse_connection_info(flow: Element) -> dict:
    """
    Parse the connection information from a flow tag.

    Args:
     - flow: ElementTree.Element with the flow tag.

    Returns:
        dictionary with the connection information.
    """
    result = {}
    reply = None
    # expand meta tags
    for child in flow.findall('meta'):
        if child.get('direction') == 'original':
            layer3 = child.find('layer3')
            result['source'] = layer3.find('src').text
            result['destination'] = layer3.find('dst').text
            layer4 = child.find('layer4')
            result['protocol'] = layer4.get('protoname')
            if layer4.find('sport') is not None:
                result['source_port'] = layer4.find('sport').text
            if layer4.find('dport') is not None:
                result['destination_port'] = layer4.find('dport').text
            counters = child.find('counters')
            if counters is not None:
                result['source_stats'] = {
                    'packets': int(counters.find('packets').text),
                    'bytes': int(counters.find('bytes').text)
                }
        if child.get('direction') == 'reply':
            reply = child
            counters = child.find('counters')
            if counters is not None:
                result['destination_stats'] = {
                    'packets': int(counters.find('packets').text),
                    'bytes': int(counters.find('bytes').text)
                }
        if child.get('direction') == 'independent':
            result['id'] = child.find('id').text
            if child.find('timeout') is not None:
                result['timeout'] = child.find('timeout').text
            if child.find('unreplied') is not None:
                result['unreplied'] = True
            if child.find('state') is not None:
                result['state'] = child.find('state').text
            # seconds since the connection started, only with conntrack timestamps enabled
            if child.find('deltatime') is not None:
                result['deltatime'] = int(child.find('deltatime').text)
            result['labels'] = []
            for label in child.findall('labels/label'):
                result['labels'].append(label.text)

    # reply tuple differs from the original one when the connection is translated
    if reply is not None and 'source' in result:
        layer3 = reply.find('layer3')
        layer4 = reply.find('layer4')
        sport = layer4.find('sport')
        dport = layer4.find('dport')
        reply_sport = sport.text if sport is not None else None
        reply_dport = dport.text if dport is not None else None
        if layer3.find('src').text != result['destination'] or reply_sport != result.get('destination_port'):
            result['destination_nat'] = layer3.find('src').text
            if reply_sport is not None:
                result['destination_nat_port'] = reply_sport
        if layer3.find('dst').text != result['source'] or reply_dport != result.get('source_port'):
            result['source_nat'] = layer3.find('dst').text
            if reply_dport is not None:
                result['source_nat_port'] = reply_dport

    return result


def list_connections(labels: list = None, extra_args: list = None):
    """
    List all network connections.

    Args:
     - labels: optional list of label strings to filter by. Only connections that have
               ALL the specified labels are returned. If ``None`` or empty, all
               connections are returned.
     - extra_args: optional list of extra conntrack arguments, e.g. ``["--orig-src", "10.0.0.1"]``.

    Returns:
        list of connections.
    """
    cmd = ["conntrack", "-L", "-o", "labels,xml"]
    if labels:
        cmd.extend(["-l", ",".join(labels)])
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if not result.stdout.strip():
        return []
    root = ElementTree.fromstring(result.stdout)
    connections = []
    for flow in root.findall('flow'):
        connections.append(__parse_connection_info(flow))

    return connections


def drop_connection(connection_id: str):
    """
    Drop a connection by its id.

    Args:
     - connection_id: id of the connection to drop.

    Raises:
     - ValueError: if the connection with the given id is not found.
     - RuntimeError: if the connection could not be dropped.
    """
    connections = list(filter(lambda x: x['id'] == connection_id, list_connections()))
    if len(connections) <= 0:
        raise ValueError(f"Connection with id {connection_id} not found.")

    connection = connections[0]
    process_commands = [
        'conntrack',
        '-D',
        '-p',
        connection['protocol'],
        '-s',
        connection['source'],
        '-d',
        connection['destination']
    ]
    if connection['protocol'] not in ['icmp', 'gre']:
        process_commands.extend(['--sport', connection['source_port'], '--dport', connection['destination_port']])

    try:
        subprocess.run(process_commands, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error running command: {e}")


def drop_all_connections():
    """
    Flush all connections.

    Raises:
     - RuntimeError: if command failed to execute.
    """
    try:
        subprocess.run(['conntrack', '-F'], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error running command: {e}")
