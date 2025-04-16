#!/usr/bin/python3

#
# Copyright (C) 2024-2025 Nethesis S.r.l.
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
from nethsec import utils
from jinja2 import Template

conntrack_ji_template = """
Sync {
    Mode FTFW {
        DisableExternalCache Off
        CommitTimeout 180
        PurgeTimeout 5
    }

    UDP {
        # Dedicated link for connection replication
        IPv4_address {{ main_ip }}
        IPv4_Destination_Address {{ backup_ip }}
        Port 3780
        Interface {{ ha_interface }}
        SndSocketBuffer 1249280
        RcvSocketBuffer 1249280
        Checksum on
    }
}

General {
    HashSize 32768
    HashLimit 131072
    LogFile off
    Syslog on
    NetlinkOverrunResync 5
    NetlinkEventsReliable on
    PollSecs 5
    EventIterationLimit 200
    LockFile /var/lock/conntrack.lock
    UNIX {
        Path /var/run/conntrackd.ctl
    }
    NetlinkBufferSize 2097152
    NetlinkBufferSizeMaxGrowth 8388608
    Filter From Userspace {
        Protocol Accept {
            TCP
            UDP
        }
        Address Ignore {
            IPv4_address 127.0.0.1 # loopback
            IPv4_address 10.0.0.1
            IPv4_address 10.0.0.2
            IPv4_address 10.0.0.3
            IPv4_address 192.168.255.2
            IPv4_address 192.168.255.52
            IPv4_address 192.168.255.250
        }
    }
}
"""

def get_device_from_ip(uci, ipaddr):
    for n in utils.get_all_by_type(uci, 'network', 'interface'):
        if uci.get('network', n, 'ipaddr', default=None) == ipaddr:
            return uci.get('network', n, 'device', default=None)


def setup(role, main_node_ip, backup_node_ip, virtual_ip, pubkey = "", password = ""):
    ret = {}
    u = EUci()
    if role == "main":
        lan_device = get_device_from_ip(u, main_node_ip)
    else:
        lan_device = get_device_from_ip(u, backup_node_ip)
    if lan_device is None:
        raise utils.ValidationError('main_node_ip', 'no_device_with_static_ip_found')

    u.set('dropbear', 'ha_link', 'dropbear')
    u.set('dropbear', 'ha_link', 'Port', '65022')
    u.set('dropbear', 'ha_link', 'RootPasswordAuth', '0')
    u.set('dropbear', 'ha_link', 'PasswordAuth', '0')
    u.save('dropbear')
    
    u.set('keepalived', 'ha_address', 'ipaddress')
    u.set('keepalived', 'ha_address', 'name', f'{lan_device}_ha')
    u.set('keepalived', 'ha_address', 'address', virtual_ip)
    u.set('keepalived', 'ha_address', 'device', lan_device)
    u.set('keepalived', 'ha_address', 'label_suffix', 'ha')

    u.set('keepalived', 'ha_sync', 'vrrp_script')
    u.set('keepalived', 'ha_sync', 'name', 'ha_sync')
    u.set('keepalived', 'ha_sync', 'script', '/usr/libexec/ns-rsync.sh')
    u.set('keepalived', 'ha_sync', 'interval', '60')
    u.set('keepalived', 'ha_sync', 'weight', '100')

    u.set('keepalived', 'lan_track', 'track_interface')
    u.set('keepalived', 'lan_track', 'name', f'{lan_device}_ha')
    u.set('keepalived', 'lan_track', 'value', lan_device)
    u.set('keepalived', 'lan_track', 'weight', '100')

    if role == 'main':
        u.set('keepalived', 'ha_sender', 'track_script')
        u.set('keepalived', 'ha_sender', 'name', 'sender')
        u.set('keepalived', 'ha_sender', 'value', 'ha_sync')
        u.set('keepalived', 'ha_sender', 'weight', '100')

        u.set('keepalived', 'ha_peer', 'peer')
        u.set('keepalived', 'ha_peer', 'name', 'backup')
        u.set('keepalived', 'ha_peer', 'address', backup_node_ip)
        u.set('keepalived', 'ha_peer', 'sync', '1')
        u.set('keepalived', 'ha_peer', 'sync_mode', 'send')
        u.set('keepalived', 'ha_peer', 'sync_dir', '/usr/share/keepalived/rsync')
        u.set('keepalived', 'ha_peer', 'ssh_port', '65022')
        u.set('keepalived', 'ha_peer', 'ssh_key', '/etc/keepalived/keys/id_rsa')

        u.set('keepalived', 'main', 'vrrp_instance')
        u.set('keepalived', 'main', 'name', 'master')
        u.set('keepalived', 'main', 'state', 'MASTER')
        u.set('keepalived', 'main', 'interface', lan_device)
        u.set('keepalived', 'main', 'virtual_router_id', '100')
        u.set('keepalived', 'main', 'priority', '100')
        u.set('keepalived', 'main', 'advert_int', '1')
        u.set('keepalived', 'main', 'nopreempt', '0')
        u.set('keepalived', 'main', 'virtual_ipaddress', [f'{lan_device}_ha'])
        u.set('keepalived', 'main', 'unicast_src_ip', main_node_ip)
        u.set('keepalived', 'main', 'unicast_peer', ['backup'])
        u.set('keepalived', 'main', 'auth_type', 'PASS')

        password = u.get('keepalived', 'vrrp_instance', 'auth_pass', default=None)
        if not password:
            # generate random password: SHA1 hash based on the current time
            current_time = str(time.time()).encode('utf-8')
            password = hashlib.sha1(current_time).hexdigest()[:8]
        ret['password'] = password
        u.set('keepalived', 'main', 'auth_pass', password)
        u.set('keepalived', 'main', 'track_interface', [f'{lan_device}_ha'])
        u.set('keepalived', 'main', 'track_script', ['sender'])

        # Generate the private key if it does not exist
        private_key_path = '/etc/keepalived/keys/id_rsa'
        if not os.path.isfile(private_key_path):
            subprocess.run(['dropbearkey', '-t', 'rsa', '-f', private_key_path], capture_output=True)

        # Print the public key
        result = subprocess.run(['dropbearkey', '-y', '-f', private_key_path], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'ssh-rsa' in line:
                ret['pubkey'] = line

        # Setup conntrackd configuration
        conntrack_template = Template(conntrack_ji_template)
        conntrack_conf = conntrack_template.render(main_ip=main_node_ip, backup_ip=backup_node_ip, ha_interface=lan_device)
        with open('/etc/conntrackd/conntrackd.conf', 'w') as file:
            file.write(conntrack_conf)
    else:
        u.set('keepalived', 'ha_receiver', 'track_script')
        u.set('keepalived', 'ha_receiver', 'name', 'receiver')
        u.set('keepalived', 'ha_receiver', 'value', 'ha_sync')
        u.set('keepalived', 'ha_receiver', 'weight', '100')

        u.set('keepalived', 'ha_peer', 'peer')
        u.set('keepalived', 'ha_peer', 'name', 'master')
        u.set('keepalived', 'ha_peer', 'address', main_node_ip)
        u.set('keepalived', 'ha_peer', 'sync', '1')
        u.set('keepalived', 'ha_peer', 'sync_mode', 'receive')
        u.set('keepalived', 'ha_peer', 'sync_dir', '/usr/share/keepalived/rsync')
        u.set('keepalived', 'ha_peer', 'ssh_pubkey', pubkey)
  
        u.set('keepalived', 'backup', 'vrrp_instance')
        u.set('keepalived', 'backup', 'name', 'backup')
        u.set('keepalived', 'backup', 'state', 'BACKUP')
        u.set('keepalived', 'backup', 'interface', lan_device)
        u.set('keepalived', 'backup', 'virtual_router_id', '100')
        u.set('keepalived', 'backup', 'priority', '50')
        u.set('keepalived', 'backup', 'advert_int', '1')
        u.set('keepalived', 'backup', 'nopreempt', '0')
        u.set('keepalived', 'backup', 'virtual_ipaddress', [f'{lan_device}_ha'])
        u.set('keepalived', 'backup', 'unicast_src_ip', backup_node_ip)
        u.set('keepalived', 'backup', 'unicast_peer', ['master'])
        u.set('keepalived', 'backup', 'auth_type', 'PASS')
        u.set('keepalived', 'backup', 'auth_pass', password)
        u.set('keepalived', 'backup', 'track_interface', [f'{lan_device}_ha'])
        u.set('keepalived', 'backup', 'track_script', ['receiver'])

        # Append publick key to root dropbear authorized_keys
        with open('/etc/dropbear/authorized_keys', 'a') as file:
            file.write(pubkey + '\n')

        # Create the rsync directory if it doesn't exist
        rsync_dir = '/usr/share/keepalived/rsync/etc/'
        os.makedirs(rsync_dir, exist_ok=True)
        # Change permissions of the rsync directory
        os.chmod(rsync_dir, 0o2775)

        # Setup conntrackd configuration
        conntrack_template = Template(conntrack_ji_template)
        conntrack_conf = conntrack_template.render(main_ip=main_node_ip, backup_ip=backup_node_ip, ha_interface=lan_device)
        with open('/etc/conntrackd/conntrackd.conf', 'w') as file:
            file.write(conntrack_conf)

    u.save('keepalived')
    # enable and start conntrackd
    subprocess.run(['/etc/init.d/conntrackd', 'enable'], capture_output=True)
    subprocess.run(['/etc/init.d/conntrackd', 'restart'], capture_output=True)

    return ret

def status():
    ret = {"role": "", "status": "", "last_sync_status": "", "last_sync_time": ""}
    try:
        subprocess.run("kill -USR2 $(/etc/init.d/keepalived info | jq -r .keepalived.instances.instance1.pid)", shell=True, capture_output=True, check=True)
        ret["status"] = "enabled"
    except:
        ret["status"] = "disabled"

    if os.path.exists('/var/keepalived.stats'):
        with open('/var/keepalived.stats') as f:
            for line in f:
                if 'VRRP Instance' in line:
                    ret["role"] = line.split()[2]
                    break

    # Using uci to query the state, with EUci(confdir="/var/state/"), the library can't read the data
    ret["last_sync_status"] = subprocess.run(["uci", "-P", "/var/state/", "get", "keepalived.ha_peer.last_sync_status"], capture_output=True, text=True).stdout.strip()
    ret["last_sync_time"] = subprocess.run(["uci", "-P", "/var/state/", "get", "keepalived.ha_peer.last_sync_time"], capture_output=True, text=True).stdout.strip()

    return ret


cmd = sys.argv[1]

if cmd == 'list':
    print(json.dumps({"setup": {
        "role": "main",
        "main_node_ip": "100.100.100.1",
        "backup_node_ip": "100.100.100.2",
        "virtual_ip": "192.168.1.1",
        "pubkey": "ssh-rsa AAAAB....",
        "password": "admin"
        },
        "status": {}
        }))
else:
    action = sys.argv[2]
    if action == "setup":
        # Paramaters:
        args = json.loads(sys.stdin.read())
        ret = setup(args.get('role'), args.get('main_node_ip'), args.get('backup_node_ip'), args.get('virtual_ip'), args.get('pubkey'), args.get('password'))
    elif action == "status":
        ret = status()

    print(json.dumps(ret))
