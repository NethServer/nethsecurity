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
            result['labels'] = []
            for label in child.findall('labels/label'):
                result['labels'].append(label.text)

    return result


def list_connections(labels: list = None):
    """
    List all network connections.

    Args:
     - labels: optional list of label strings to filter by. Only connections that have
               ALL the specified labels are returned. If ``None`` or empty, all
               connections are returned.

    Returns:
        list of connections.
    """
    cmd = ["conntrack", "-L", "-o", "labels,xml"]
    if labels:
        cmd.extend(["-l", ",".join(labels)])
    result = subprocess.run(cmd, capture_output=True, text=True)
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
