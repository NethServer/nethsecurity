#!/usr/bin/python3

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Read and set HA configuration

import sys
import json
from euci import EUci
import os
import subprocess
import hashlib
import time
from nethsec import firewall


def setup(role, lan_interface, ha_interface, virtual_ip, ha_main_ipaddress, ha_secondary_ipaddress, pubkey = "", password = ""):
    ret = {}
    u = EUci()

    firewall.add_template_zone(u, 'ns_ha', link="keepalived/ha_address")

    u.set('network', 'ha', 'interface')
    u.set('network', 'ha', 'proto', 'static')
    u.set('network', 'ha', 'netmask', '255.255.255.0')
    u.set('network', 'ha', 'device', ha_interface)
    if role == 'main':
        u.set('network', 'ha', 'ipaddr', ha_main_ipaddress)
    else:
        u.set('network', 'ha', 'ipaddr', ha_secondary_ipaddress)
    u.save('network')

    # setup UAM rule, if needed
    (z_name, z_config) = firewall.get_zone_by_name(u, 'ha')
    if 'ha' not in z_config.get('network', []):
        u.set('firewall', z_name, 'network', ['ha'])
        u.save('firewall')
    
    u.set('keepalived', 'ha_address', 'ipaddress')
    u.set('keepalived', 'ha_address', 'name', f'{lan_interface}_ha')
    u.set('keepalived', 'ha_address', 'address', virtual_ip)
    u.set('keepalived', 'ha_address', 'device', lan_interface)
    u.set('keepalived', 'ha_address', 'label_suffix', 'ha')

    u.set('keepalived', 'ha_sync', 'vrrp_script')
    u.set('keepalived', 'ha_sync', 'name', 'ha_sync')
    u.set('keepalived', 'ha_sync', 'script', '/etc/keepalived/scripts/rsync.sh')
    u.set('keepalived', 'ha_sync', 'interval', '60')
    u.set('keepalived', 'ha_sync', 'weight', '100')

    u.set('keepalived', 'lan_static', 'static_ipaddress')
    u.set('keepalived', 'lan_static', 'address', f'{lan_interface}_ha')

    u.set('keepalived', 'lan_track', 'track_interface')
    u.set('keepalived', 'lan_track', 'name', f'{lan_interface}_ha')
    u.set('keepalived', 'lan_track', 'value', lan_interface)
    u.set('keepalived', 'lan_track', 'weight', '100')

    if role == 'main':
        u.set('keepalived', 'ha_sender', 'track_script')
        u.set('keepalived', 'ha_sender', 'name', 'sender')
        u.set('keepalived', 'ha_sender', 'value', 'ha_sync')
        u.set('keepalived', 'ha_sender', 'weight', '100')

        u.set('keepalived', 'ha_peer', 'peer')
        u.set('keepalived', 'ha_peer', 'name', 'backup')
        u.set('keepalived', 'ha_peer', 'address', ha_secondary_ipaddress)
        u.set('keepalived', 'ha_peer', 'sync', '1')
        u.set('keepalived', 'ha_peer', 'sync_mode', 'send')
        u.set('keepalived', 'ha_peer', 'sync_dir', '/usr/share/keepalived/rsync')
        u.set('keepalived', 'ha_peer', 'ssh_port', '22')
        u.set('keepalived', 'ha_peer', 'ssh_key', '/etc/keepalived/keys/id_rsa')

        u.set('keepalived', 'main', 'vrrp_instance')
        u.set('keepalived', 'main', 'name', 'master')
        u.set('keepalived', 'main', 'state', 'MASTER')
        u.set('keepalived', 'main', 'interface', ha_interface)
        u.set('keepalived', 'main', 'virtual_router_id', '100')
        u.set('keepalived', 'main', 'priority', '100')
        u.set('keepalived', 'main', 'advert_int', '1')
        u.set('keepalived', 'main', 'nopreempt', '0')
        u.set('keepalived', 'main', 'virtual_ipaddress', [f'{lan_interface}_ha'])
        u.set('keepalived', 'main', 'unicast_src_ip', ha_main_ipaddress)
        u.set('keepalived', 'main', 'unicast_peer', ['backup'])
        u.set('keepalived', 'main', 'auth_type', 'PASS')

        password = u.get('keepalived', 'vrrp_instance', 'auth_pass', default=None)
        if not password:
            # generate random password: SHA1 hash based on the current time
            current_time = str(time.time()).encode('utf-8')
            password = hashlib.sha1(current_time).hexdigest()[:8]
        ret['password'] = password
        u.set('keepalived', 'main', 'auth_pass', password)
        u.set('keepalived', 'main', 'track_interface', [f'{lan_interface}_ha'])
        u.set('keepalived', 'main', 'track_script', ['sender'])

        # Generate the private key if it does not exist
        private_key_path = '/etc/keepalived/keys/id_rsa'
        if not os.path.isfile(private_key_path):
            subprocess.run(['dropbearkey', '-t', 'rsa', '-f', private_key_path])

        # Print the public key
        result = subprocess.run(['dropbearkey', '-y', '-f', private_key_path], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'ssh-rsa' in line:
                ret['pubkey'] = line
    else:
        u.set('keepalived', 'ha_receiver', 'track_script')
        u.set('keepalived', 'ha_receiver', 'name', 'receiver')
        u.set('keepalived', 'ha_receiver', 'value', 'ha_sync')
        u.set('keepalived', 'ha_receiver', 'weight', '100')

        u.set('keepalived', 'ha_peer', 'peer')
        u.set('keepalived', 'ha_peer', 'name', 'master')
        u.set('keepalived', 'ha_peer', 'address', ha_main_ipaddress)
        u.set('keepalived', 'ha_peer', 'sync', '1')
        u.set('keepalived', 'ha_peer', 'sync_mode', 'receive')
        u.set('keepalived', 'ha_peer', 'sync_dir', '/usr/share/keepalived/rsync')
        u.set('keepalived', 'ha_peer', 'ssh_pubkey', pubkey)
  
        u.set('keepalived', 'backup', 'vrrp_instance')
        u.set('keepalived', 'backup', 'name', 'backup')
        u.set('keepalived', 'backup', 'state', 'BACKUP')
        u.set('keepalived', 'backup', 'interface', ha_interface)
        u.set('keepalived', 'backup', 'virtual_router_id', '100')
        u.set('keepalived', 'backup', 'priority', '50')
        u.set('keepalived', 'backup', 'advert_int', '1')
        u.set('keepalived', 'backup', 'nopreempt', '0')
        u.set('keepalived', 'backup', 'virtual_ipaddress', [f'{lan_interface}_ha'])
        u.set('keepalived', 'backup', 'unicast_src_ip', ha_secondary_ipaddress)
        u.set('keepalived', 'backup', 'unicast_peer', ['master'])
        u.set('keepalived', 'backup', 'auth_type', 'PASS')
        u.set('keepalived', 'backup', 'auth_pass', password)
        u.set('keepalived', 'backup', 'track_interface', [f'{lan_interface}_ha'])
        u.set('keepalived', 'backup', 'track_script', ['receiver'])

        # Fix OpenVPN permissions
        group_file = '/etc/group'
        rsync_dir = '/usr/share/keepalived/rsync/etc/'

        # Update the group file, if needed
        with open(group_file, 'r') as file:
            group_data = file.read()

        if 'root:x:0:keepalived' not in group_data:
            group_data = group_data.replace('root:x:0:', 'root:x:0:keepalived')

            with open(group_file, 'w') as file:
                file.write(group_data)

        # Create the rsync directory if it doesn't exist
        os.makedirs(rsync_dir, exist_ok=True)

        # Change permissions of the rsync directory
        os.chmod(rsync_dir, 0o2775)

    u.save('keepalived')

    return ret

cmd = sys.argv[1]

if cmd == 'list':
    print(json.dumps({"setup": {
        "role": "main",
        "lan_interface": "eth0",
        "ha_interface": "eth1",
        "virtual_ip": "192.168.1.1",
        "ha_main_ipaddress": "100.100.100.1",
        "ha_secondary_ipaddress": "100.100.100.2",
        "pubkey": "ssh-rsa AAAAB....",
        "password": "admin"
        }}))
else:
    action = sys.argv[2]
    if action == "setup":
        # Paramaters:
        args = json.loads(sys.stdin.read())
        ret = setup(args.get('role'), args.get('lan_interface'), args.get('ha_interface'), args.get('virtual_ip'), args.get('ha_main_ipaddress'), args.get('ha_secondary_ipaddress'), args.get('pubkey'), args.get('password'))

    print(json.dumps(ret))
