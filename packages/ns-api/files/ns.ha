#!/usr/bin/python3

#
# Copyright (C) 2024-2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Read and set HA configuration

import signal
import sys
import json
from euci import EUci
import os
import subprocess
import hashlib
import time
from nethsec import utils
from jinja2 import Template
import tempfile
import shutil
import re

### Utilities functions

conntrack_ji_template = """
Sync {
    Mode FTFW {
        DisableExternalCache Off
        CommitTimeout 180
        PurgeTimeout 5
    }

    UDP {
        # Dedicated link for connection replication
        IPv4_address {{ primary_ip }}
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
            # Return a tuple with the (interface, device)
            return (n, uci.get('network', n, 'device', default=None))
    return (None, None)

def ssh_execute(command, host, port=22, username='root', password=None, private_key_path=None):
    """
    Execute SSH command using subprocess
    """
    ssh_cmd = ['ssh', '-o', 'StrictHostKeyChecking=no']
    # Add port if not default
    if port != 22:
        ssh_cmd.extend(['-p', str(port)])

    # Handle authentication
    if private_key_path:
        ssh_cmd.extend(['-i', private_key_path])

    # Add user@host
    ssh_cmd.append(f'{username}@{host}')

    # Add command
    ssh_cmd.append(command)

    try:
        if password:
            # Use sshpass for password authentication
            sshpass_cmd = ['sshpass', '-p', password] + ssh_cmd
            proc = subprocess.run(sshpass_cmd, capture_output=True, text=True, timeout=30)
        else:
            proc = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
        return proc.stdout, proc.stderr, proc.returncode
    except:
        raise utils.ValidationError('ssh_command_failed')

def ssh_upload_file(local_file_path, remote_file_path, host, port=22, username='root', password=None, private_key_path=None):
    """
    Upload file via SCP using subprocess
    """
    # First create the destination directory
    destination_dir = os.path.dirname(remote_file_path)
    if destination_dir:
        _, _, returncode = ssh_execute(f"mkdir -p {destination_dir}", host, port, username, password, private_key_path)
        if returncode != 0:
            return False
    scp_cmd = ['scp', '-o', 'StrictHostKeyChecking=no']
    # Add port if not default
    if port != 22:
        scp_cmd.extend(['-P', str(port)])

    # Handle authentication
    if private_key_path:
        scp_cmd.extend(['-i', private_key_path])

    # Add source and destination
    scp_cmd.append(local_file_path)
    scp_cmd.append(f'{username}@{host}:{remote_file_path}')
    try:
        if password:
            # Use sshpass for password authentication
            sshpass_cmd = ['sshpass', '-p', password] + scp_cmd
            proc = subprocess.run(sshpass_cmd, capture_output=True, text=True, timeout=60)
        else:
            proc = subprocess.run(scp_cmd, capture_output=True, text=True, timeout=60)
        return proc.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def allocate_fake_ips(uci):
    wan_counter = 0
    for n in utils.get_all_by_type(uci, 'network', 'interface'):
        ipaddr = uci.get('network', n, 'ipaddr', default=None)
        if ipaddr and ipaddr.startswith('169.254.'):
            wan_counter += 1
    # Each WAN interface gets 2 fake IP addresses:
    # 169.254.<wan_counter>.1 and 169.254.<wan_counter>.2
    next_wan = wan_counter + 1
    primary_ip = f"169.254.{next_wan}.1"
    backup_ip = f"169.254.{next_wan}.2"
    return primary_ip, backup_ip

def validate_network(role, lan_interface, wan_interface):
    errors = []
    uci = EUci()
    try:
        proto = uci.get('network', lan_interface, 'proto')
    except:
        proto = ""
        errors.append('lan_network_not_found')

    if proto != 'static':
        errors.append('lan_network_not_static')

    if role == 'primary':
        try:
            proto = uci.get('network', wan_interface, 'proto')
        except:
            proto = ""
            errors.append('wan_network_not_found')
        if proto == 'pppoe':
            errors.append('wan_network_is_pppoe')

    return errors

def validate_dhcp(lan_interface):
    errors = []
    uci = EUci()
    is_keeplived_configured = len(utils.get_all_by_type(uci, 'keepalived', 'vrrp_instance')) > 0
    for server in utils.get_all_by_type(uci, 'dhcp', 'dhcp'):
        # Check if IPv4 DHCP server is enabled
        if uci.get('dhcp', server, 'dhcpv4', default=None) == 'server':
            if uci.get('dhcp', server, 'interface', default=None) != lan_interface:
                continue  # Skip if the DHCP server is not on the given lan interface

            # 1. Make sure configured DHCP server has force option enabled
            # This is already enforced by the 500-dhcp-force hotplug script

            # 2. Make sure configured DHCP server has the router and dns options
            try:
                options = uci.get_all('dhcp', server, 'dhcp_option')
            except:
                options = []
            if not any("option:router" in option for option in options):
                errors.append('dhcp_router_option_not_found')
            else:
                # 3. Make sure the router option matches the VIP address, if keepalived is configured
                if is_keeplived_configured:
                    interface = uci.get('dhcp', server, 'interface', default=None)
                    vips = utils.get_all_by_type(uci, 'keepalived', 'ipaddress')
                    for key in vips:
                        vip = vips[key]
                        if vip.get('name').split('_')[0] == interface:
                            option_router = next((option for option in options if "option:router" in option), None)
                            router_ip = option_router.split(",")[1]
                            vip_address = vip.get('address').split('/')[0]
                            if vip_address.strip() != router_ip.strip():
                                errors.append(f'dhcp_router_option_does_not_match_vip: {interface}')
                                break
            if not any("option:dns" in option for option in options):
                errors.append('dhcp_dns_option_not_found')
    return errors

def execute_remote_command(command, backup_node_ip=None, port=None):
    """Execute a command on the remote backup node using SSH."""
    uci = EUci()
    if port is None:
        port = uci.get('dropbear', 'ha_link', 'Port', default=None)
    if backup_node_ip is None:
        backup_node_ip = uci.get('keepalived', 'ha_peer', 'address', default=None)
    if not port or not backup_node_ip:
        raise utils.ValidationError('backup_node_ip', 'missing_backup_node_ip')
    stdout, stderr, returncode = ssh_execute(
        command,
        backup_node_ip,
        port=int(port),
        private_key_path='/etc/keepalived/keys/id_rsa'
    )
    if returncode == 0:
        # Callers will check for errors in stderr
        stderr = ''
    return stdout, stderr

def upload_remote_file(local_file_path, remote_file_path, backup_node_ip=None, port=None):
    """Upload a file to the remote backup node using SCP."""
    uci = EUci()
    if port is None:
        port = uci.get('dropbear', 'ha_link', 'Port', default=None)
    if backup_node_ip is None:
        backup_node_ip = uci.get('keepalived', 'ha_peer', 'address', default=None)
    if not port or not backup_node_ip:
        raise utils.ValidationError('backup_node_ip', 'missing_backup_node_ip')
    return ssh_upload_file(
        local_file_path,
        remote_file_path,
        backup_node_ip,
        port=int(port),
        private_key_path='/etc/keepalived/keys/id_rsa'
    )

def find_device_config(uci, device, config=None):
    if config is None:
        config = []
    # Find the device configuration in UCI
    for n in utils.get_all_by_type(uci, 'network', 'device'):
        if uci.get('network', n, 'name', default=None) == device:
            device_config = uci.get_all('network', n)
            device_config['record_type'] = 'device'
            device_config['record_id'] = n
            
            if device_config.get('type') == 'bridge':
                # List all ports of the bridge
                for port in device_config.get('ports', []):
                    config = config + find_device_config(uci, port, config)
            elif device_config.get('type', '').startswith('802'):
                ifname = device_config.get('ifname')
                if not ifname:
                    continue
                # Get the underlying device of the 802.1q interface
                for underlying_device in utils.get_all_by_type(uci, 'network', 'device'):
                    if uci.get('network', underlying_device, 'name', default=None) == ifname:
                        config = config + find_device_config(uci, ifname, config)
                        break
            config.append(device_config)
 
    return config

def parse_node_state():
    state_map = {
        -1: "unknown",
        0: "init",
        1: "backup",
        2: "master",
        3: "fault"
    }
    # Check if keepalived is running
    try:
        proc = subprocess.run(["/etc/init.d/keepalived", "info"], check=True, capture_output=True, text=True)
        status = json.loads(proc.stdout)
        if not status['keepalived']['instances']['instance1']['running']:
            return "unknown", {}, -1, -1
    except:
        return "unknown", {}, -1, -1

     # Using uci to query the state, with EUci(confdir="/var/state/"), the library can't read the data
    last_sync_status = subprocess.run(["uci", "-P", "/var/state/", "get", "keepalived.ha_peer.last_sync_status"], capture_output=True, text=True).stdout.strip()
    last_sync_time = subprocess.run(["uci", "-P", "/var/state/", "get", "keepalived.ha_peer.last_sync_time"], capture_output=True, text=True).stdout.strip()

    # Integrate keepalived stats and state
    stats = {}
    state = -1
    try:
        # Send 37 signal to keepalived to dump stats
        pid_file = "/tmp/run/keepalived.pid"
        stats_file = "/tmp/keepalived.json"
        if os.path.isfile(pid_file):
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 37)
            # Wait a moment for stats to be written
            time.sleep(0.2)
            if os.path.isfile(stats_file):
                with open(stats_file, "r") as f:
                    stats_content = json.load(f)
                # Parse stats into the required structure
                if len(stats_content) == 0:
                    ret["keepalived_stats"] = {}
                else:
                    stats = stats_content[0].get("stats", {})
                state = stats_content[0].get("data", {}).get("state", -1)
    except Exception as e:
        pass

    return state_map.get(state, "unknown"), stats, last_sync_status, last_sync_time


### API functions

def import_network_config(configs):
    # config is a dictionary with the network configuration
    uci = EUci()

    for config in configs:
        subprocess.run(["logger", "-t", "ns-ha", f"Importing network configuration: {json.dumps(config)}"], check=True)

    for config in configs:
        if config.get('record_type') == 'device':
            # Remove existing devices for the same name
            for n in utils.get_all_by_type(uci, 'network', 'device'):
                if uci.get('network', n, 'name', default=None) == config['name']:
                    uci.delete('network', n)
        # Create the configuration
        uci.set('network', config['record_id'], config['record_type'])
        for k, v in config.items():
            if k not in ['record_id', 'record_type']:
                uci.set('network', config['record_id'], k, v)
    uci.commit('network')

    return { "success": True }


def add_wan_interface(role, interface, virtual_ip, gateway):
    # Add a new WAN interface to the keepalived configuration:
    # 1. find a fake unused address inside the fake network 169.254.0.0/16 (reserved for documentation by RFC)
    # 2. set the fake address to the interface, remove the gateway
    # 3. create keepalived configuration: ipaddress, track_interface, route
    u = EUci()

    # Check if the interface exists
    if not u.get('network', interface, default=None):
        raise utils.ValidationError('interface', 'interface_not_found')

    # Gateway is mandatory for WAN interfaces
    if not gateway:
        raise utils.ValidationError('gateway', 'gateway_must_be_set')

    if role == 'primary':
        # Before adding the interface, configure interface and device on the backup node:
        # 1. get the device configuration from the primary node and send it to the backup node
        # 2. create the interface on the backup node
        network_config = []
        device = u.get('network', interface, 'device', default=None)
        device_config = find_device_config(u, device)
        # Please note that device_config could be emptry for a WAN on a clean machine
        network_config = network_config + device_config
        
        interface_config = u.get_all('network', interface)
        interface_config['record_type'] = 'interface'
        interface_config['record_id'] = interface
        # Check if the interface is a bonding interface
        if interface_config.get('device').startswith('bond-'):
            # List all the slaves of the bonding interface, strip the prefix 'bond-'
            try:
                bond_config = u.get_all('network', interface_config.get('device')[5:])
                bond_config['record_type'] = 'interface'
                bond_config['record_id'] = interface_config.get('device')[5:]
                network_config = network_config + [bond_config]
            except:
                return utils.generic_error("bonding_interface_not_found")
            # Send the slaves to the backup node
            for slave in bond_config.get('slaves', []):
                network_config = network_config + find_device_config(u, slave)
        network_config = network_config + [interface_config]

        # Send the interface configuration to the backup node:
        _, stderr = execute_remote_command(f"echo '{json.dumps(network_config)}' | /usr/libexec/rpcd/ns.ha call import-network-config")
        if stderr:
            return utils.generic_error("error_executing_import_network_config_on_backup_node")

    # Get the fake IP address
    primary_ip, backup_ip = allocate_fake_ips(u)

    # Select keepalived instance and set the fake IP address
    if role == 'primary':
        kinstance_name = 'primary'
        u.set('network', interface, 'ipaddr', primary_ip)
    else:
        kinstance_name = 'backup'
        u.set('network', interface, 'ipaddr', backup_ip)
    u.set('network', interface, 'netmask', '255.255.255.0')
    u.set('network', interface, 'proto', 'static')
    virtual_ips = list(u.get_all('keepalived', kinstance_name, 'virtual_ipaddress'))
    track_interfaces = list(u.get_all('keepalived', kinstance_name, 'track_interface'))
    try:
        virtual_routes = list(u.get_all('keepalived', kinstance_name, 'virtual_routes'))
    except:
        virtual_routes = []

    device = u.get('network', interface, 'device', default=None)

    # Set the fake IP address to the interface and remove the gateway
    u.delete('network', interface, 'gateway')
    # Create a virtual route is needed
    u.set('keepalived', f'{interface}_route', 'route')
    u.set('keepalived', f'{interface}_route', 'table', 'main')
    u.set('keepalived', f'{interface}_route', 'address', '0.0.0.0/0')
    u.set('keepalived', f'{interface}_route', 'name', f'{interface}_route')
    u.set('keepalived', f'{interface}_route', 'device', device)
    u.set('keepalived', f'{interface}_route', 'gateway', gateway)
    u.set('keepalived', f'{interface}_route', 'src_addr', virtual_ip.split('/')[0])
    u.set('keepalived', f'{interface}_route', 'ns_link', f'network/{interface}')
    # Add the route to the list of virtual routes
    u.set('keepalived', kinstance_name, 'virtual_routes', list(set(virtual_routes + [f'{interface}_route'])))

    # Create the VIP address
    u.set('keepalived', f'{interface}_ipaddress', 'ipaddress')
    u.set('keepalived', f'{interface}_ipaddress', 'name', f'{interface}_ha')
    u.set('keepalived', f'{interface}_ipaddress', 'address', virtual_ip)
    u.set('keepalived', f'{interface}_ipaddress', 'device', device)
    u.set('keepalived', f'{interface}_ipaddress', 'label_suffix', 'ha')
    u.set('keepalived', f'{interface}_ipaddress', 'ns_link', f'network/{interface}')
    # Add the VIP to the list of virtual IPs
    u.set('keepalived', kinstance_name, 'virtual_ipaddress', list(set(virtual_ips + [f'{interface}_ha'])))

    # Create the track interface
    u.set('keepalived', f'{interface}_track', 'track_interface')
    u.set('keepalived', f'{interface}_track', 'name', f'{interface}_ha')
    u.set('keepalived', f'{interface}_track', 'value', device)
    u.set('keepalived', f'{interface}_track', 'weight', '100')
    u.set('keepalived', f'{interface}_track', 'ns_link', f'network/{interface}')
    # Add the track interface to the list of tracked interfaces
    u.set('keepalived', kinstance_name, 'track_interface', list(set(track_interfaces + [f'{interface}_ha'])))

    u.commit('keepalived')
    u.commit('network')
    subprocess.run(["/sbin/reload_config"], capture_output=True)
    # Restart mwan3 that was stopped during the init_local phase
    subprocess.run(['/etc/init.d/mwan3', 'restart'], capture_output=True)

    if role == 'primary':
        # Execute the add-interface API on the backup node
        command = json.dumps({
            "role": "backup",
            "interface": interface,
            "virtual_ip": virtual_ip,
            "gateway": gateway
        })

        output, error = execute_remote_command(f"echo '{command}' | /usr/libexec/rpcd/ns.ha call add-wan-interface")
        if error:
            return utils.generic_error("error_executing_add_wan_interface_on_backup_node")
        return json.loads(output)
    else:
        return { "success": True }


def add_lan_interface(role, primary_node_ip, backup_node_ip, virtual_ip):
    # The inteface must already exists in the primary and backup nodes.
    # This function just adds the keepalived configuration for the interface.
    # This function should be used to add all non-WAN interfaces, this is a requirement
    # for interfaces that handle a DHCP server: dnsmasq requires the interface has a static IP
    # address in the same network of the DHCP range.

    u = EUci()
    if role == "primary":
        kinstance_name = 'primary'
        (interface, device) = get_device_from_ip(u, primary_node_ip)
    else:
        kinstance_name = 'backup'
        (interface, device) = get_device_from_ip(u, backup_node_ip)
    if device is None:
        raise utils.ValidationError(f'{role}_node_ip', 'no_device_with_static_ip_found')

    dhcp_errors = validate_dhcp(interface)
    if len(dhcp_errors) > 0:
        raise utils.ValidationError("dhcp_configuration_errors", dhcp_errors[0])

    virtual_ips = list(u.get_all('keepalived', kinstance_name, 'virtual_ipaddress'))
    track_interfaces = list(u.get_all('keepalived', kinstance_name, 'track_interface'))

    # Create the VIP address
    u.set('keepalived', f'{interface}_ipaddress', 'ipaddress')
    u.set('keepalived', f'{interface}_ipaddress', 'name', f'{interface}_ha')
    u.set('keepalived', f'{interface}_ipaddress', 'address', virtual_ip)
    u.set('keepalived', f'{interface}_ipaddress', 'device', device)
    u.set('keepalived', f'{interface}_ipaddress', 'label_suffix', 'ha')
    u.set('keepalived', f'{interface}_ipaddress', 'ns_link', f'network/{interface}')
    # Add the VIP to the list of virtual IPs
    u.set('keepalived', kinstance_name, 'virtual_ipaddress', list(set(virtual_ips + [f'{interface}_ha'])))

    # Create the track interface
    u.set('keepalived', f'{interface}_track', 'track_interface')
    u.set('keepalived', f'{interface}_track', 'name', f'{interface}_ha')
    u.set('keepalived', f'{interface}_track', 'value', device)
    u.set('keepalived', f'{interface}_track', 'weight', '100')
    u.set('keepalived', f'{interface}_track', 'ns_link', f'network/{interface}')
    # Add the track interface to the list of tracked interfaces
    u.set('keepalived', kinstance_name, 'track_interface', list(set(track_interfaces + [f'{interface}_ha'])))

    u.commit('keepalived')
    subprocess.run(["/sbin/reload_config"], capture_output=True)

    if role == 'primary':
        # Execute the add-interface API on the backup node
        command = json.dumps({
            "role": "backup",
            "primary_node_ip": primary_node_ip,
            "backup_node_ip": backup_node_ip,
            "virtual_ip": virtual_ip
        })

        output, error = execute_remote_command(f"echo '{command}' | /usr/libexec/rpcd/ns.ha call add-lan-interface")
        if error:
            return utils.generic_error("error_executing_add_lan_interface_on_backup_node")

        return json.loads(output)
    else:
        return { "success": True }

# This function initializes the local node for high availability (HA) using Keepalived.
# It is called locally on the primary node and remotly using SSH on the backup node.
def init_local(role, primary_node_ip, backup_node_ip, virtual_ip, pubkey = "", password = ""):
    u = EUci()
    sync_list = [
        '/etc/ha',
        '/etc/acme/',
        '/etc/ssl/acme',
        '/etc/openvpn',
        '/etc/nginx',
        '/etc/adblock',
        '/etc/banip',
        '/etc/netify.d',
        '/tmp/dhcp.leases'
    ]
    exclude_list = [
        '/etc/config/network',
        '/etc/config/keepalived',
        '/etc/dropbear/authorized_keys'
    ]
    if role == "primary":
        (interface, lan_device) = get_device_from_ip(u, primary_node_ip)
    else:
        (interface, lan_device) = get_device_from_ip(u, backup_node_ip)
    if lan_device is None:
        raise utils.ValidationError('primary_node_ip', 'no_device_with_static_ip_found')

    u.set('dropbear', 'ha_link', 'dropbear')
    u.set('dropbear', 'ha_link', 'Port', '65022')
    u.set('dropbear', 'ha_link', 'RootPasswordAuth', '0')
    u.set('dropbear', 'ha_link', 'PasswordAuth', '0')
    u.commit('dropbear')
    
    u.set('keepalived', 'globals', 'enabled', '1')

    u.set('keepalived', f'{interface}_ipaddress', 'ipaddress')
    u.set('keepalived', f'{interface}_ipaddress', 'name', 'lan_ha')
    u.set('keepalived', f'{interface}_ipaddress', 'address', virtual_ip)
    u.set('keepalived', f'{interface}_ipaddress', 'device', lan_device)
    u.set('keepalived', f'{interface}_ipaddress', 'label_suffix', 'ha')
    u.set('keepalived', f'{interface}_ipaddress', 'ns_link', f'network/{interface}')

    u.set('keepalived', 'ha_sync', 'vrrp_script')
    u.set('keepalived', 'ha_sync', 'name', 'ha_sync')
    u.set('keepalived', 'ha_sync', 'script', '/usr/libexec/ns-rsync.sh')
    u.set('keepalived', 'ha_sync', 'interval', '60')
    u.set('keepalived', 'ha_sync', 'weight', '100')

    u.set('keepalived', 'lan_track', 'track_interface')
    u.set('keepalived', 'lan_track', 'name', 'lan_ha')
    u.set('keepalived', 'lan_track', 'value', lan_device)
    u.set('keepalived', 'lan_track', 'weight', '100')
    u.set('keepalived', 'lan_track', 'ns_link', f'network/{interface}')

    if role == 'primary':
        u.set('keepalived', 'globals', 'vrrp_down_timer_adverts', '5')

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
        u.set('keepalived', 'ha_peer', 'exclude_list', exclude_list)
        u.set('keepalived', 'ha_peer', 'sync_list', sync_list)

        u.set('keepalived', 'primary', 'vrrp_instance')
        u.set('keepalived', 'primary', 'name', 'master')
        u.set('keepalived', 'primary', 'state', 'MASTER')
        u.set('keepalived', 'primary', 'interface', lan_device)
        u.set('keepalived', 'primary', 'virtual_router_id', '100')
        u.set('keepalived', 'primary', 'priority', '100')
        u.set('keepalived', 'primary', 'advert_int', '1')
        u.set('keepalived', 'primary', 'nopreempt', '0')
        u.set('keepalived', 'primary', 'virtual_ipaddress', ['lan_ha'])
        u.set('keepalived', 'primary', 'unicast_src_ip', primary_node_ip)
        u.set('keepalived', 'primary', 'unicast_peer', ['backup'])
        u.set('keepalived', 'primary', 'auth_type', 'PASS')

        password = u.get('keepalived', 'vrrp_instance', 'auth_pass', default=None)
        if not password:
            # generate random password: SHA1 hash based on the current time
            current_time = str(time.time()).encode('utf-8')
            password = hashlib.sha1(current_time).hexdigest()[:8]

        u.set('keepalived', 'primary', 'auth_pass', password)
        u.set('keepalived', 'primary', 'track_interface', ['lan_ha'])
        u.set('keepalived', 'primary', 'track_script', ['sender'])

        # Generate the private key if it does not exist
        private_key_path = '/etc/keepalived/keys/id_rsa'
        if not os.path.isfile(private_key_path):
            subprocess.run(['dropbearkey', '-t', 'rsa', '-f', private_key_path], capture_output=True)

        # Setup conntrackd configuration
        conntrack_template = Template(conntrack_ji_template)
        conntrack_conf = conntrack_template.render(primary_ip=primary_node_ip, backup_ip=backup_node_ip, ha_interface=lan_device)
        with open('/etc/conntrackd/conntrackd.conf', 'w') as file:
            file.write(conntrack_conf)
    else:
        # make the secondary node more tolerant to network issues
        u.set('keepalived', 'globals', 'vrrp_down_timer_adverts', '10')

        u.set('keepalived', 'ha_receiver', 'track_script')
        u.set('keepalived', 'ha_receiver', 'name', 'receiver')
        u.set('keepalived', 'ha_receiver', 'value', 'ha_sync')
        u.set('keepalived', 'ha_receiver', 'weight', '100')

        u.set('keepalived', 'ha_peer', 'peer')
        u.set('keepalived', 'ha_peer', 'name', 'master')
        u.set('keepalived', 'ha_peer', 'address', primary_node_ip)
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
        u.set('keepalived', 'backup', 'virtual_ipaddress', ['lan_ha'])
        u.set('keepalived', 'backup', 'unicast_src_ip', backup_node_ip)
        u.set('keepalived', 'backup', 'unicast_peer', ['master'])
        u.set('keepalived', 'backup', 'auth_type', 'PASS')
        u.set('keepalived', 'backup', 'auth_pass', password)
        u.set('keepalived', 'backup', 'track_interface', ['lan_ha'])
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
        conntrack_conf = conntrack_template.render(primary_ip=backup_node_ip, backup_ip=primary_node_ip, ha_interface=lan_device)
        with open('/etc/conntrackd/conntrackd.conf', 'w') as file:
            file.write(conntrack_conf)

    u.commit('keepalived')

    # Stop mwan3: it can mess up routes configuration in this phase, it will be restarted later
    subprocess.run(['/etc/init.d/mwan3', 'stop'], capture_output=True)

    # Enable and start conntrackd
    subprocess.run(['/etc/init.d/conntrackd', 'enable'], capture_output=True)
    subprocess.run(['/etc/init.d/conntrackd', 'restart'], capture_output=True)

    # Enable keepalived if previously disabled by reset API
    subprocess.run(['/etc/init.d/keepalived', 'enable'], capture_output=True)
    # Sometimes keepalived does not start correctly, so we need to restart it
    subprocess.run(['/etc/init.d/keepalived', 'restart'], capture_output=True)

    # Apply the changes
    subprocess.run(["/sbin/reload_config"], capture_output=True)

    return { "success": True }

# This function assumes it's called on the primary node
def init_remote(ssh_password):
    u = EUci()
    # Check if it's running on the primary node and the primary node is already configured
    try:
        u.get('keepalived', 'primary')
    except:
        raise utils.ValidationError('primary_node_ip', 'no_primary_keepalived_instance_found')

    primary_node_ip = u.get('keepalived', 'primary', 'unicast_src_ip', default=None)
    backup_node_ip = u.get('keepalived', 'ha_peer', 'address', default=None)
    password = u.get('keepalived', 'primary', 'auth_pass', default=None)

    pubkey = None
    private_key_path = '/etc/keepalived/keys/id_rsa'
    if os.path.isfile(private_key_path):
        result = subprocess.run(['dropbearkey', '-y', '-f', private_key_path], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'ssh-rsa' in line:
                pubkey = line
                break

    if not all([primary_node_ip, backup_node_ip, password, pubkey]):
        raise utils.ValidationError('paramters', 'missing_required_configuration_values')

    # Prepare the init-local command
    virtual_ip_sections = utils.get_all_by_type(u, 'keepalived', 'ipaddress')
    virtual_ip = None
    for section, details in virtual_ip_sections.items():
        if 'address' in details:
            virtual_ip = details['address']
            break
    if not virtual_ip:
        return utils.generic_error("no_virtual_ip_found")
    init_local_command = json.dumps({
        "role": "backup",
        "primary_node_ip": primary_node_ip,
        "backup_node_ip": backup_node_ip,
        "virtual_ip": virtual_ip,
        "pubkey": pubkey,
        "password": password
    })

    # Execute the init-local command on the backup
    stdout, stderr, returncode = ssh_execute(
        f"echo '{init_local_command}' | /usr/libexec/rpcd/ns.ha call init-local",
        backup_node_ip,
        port=22,
        password=ssh_password
    )
    if returncode != 0:
        return utils.generic_error(f"ssh_connection_failed: {stderr}")
    return json.loads(stdout)


def status():
    ret = {
        "role": "unknown",
        "state": "unknown",
        "status": "unknown",
        "last_sync_status": "",
        "last_sync_time": "",
        "virtual_ips": [],
        "keepalived_stats": {}
    }

    u = EUci()
    try:
        u.get('keepalived', 'primary')
        ret["role"] = "primary"
        ret["status"] = "enabled"
    except:
        try:
            u.get('keepalived', 'backup')
            ret["role"] = "backup"
            ret["status"] = "enabled"
        except:
            ret["status"] = "disabled"

    if ret["status"] == "enabled":
        ret["state"], ret["keepalived_stats"], ret["last_sync_status"], ret["last_sync_time"]= parse_node_state()

    # List all configured virtual IPs
    try:
        virtual_ips = utils.get_all_by_type(u, 'keepalived', 'ipaddress')
        ret["virtual_ips"] = virtual_ips
    except:
        ret["virtual_ips"] = []

    return ret

def validate_requirements(role, lan_interface, wan_interface):
    errors = []
    errors = errors + validate_network(role, lan_interface, wan_interface)
    if role == "primary":
        errors = errors + validate_dhcp(lan_interface)
        
    return {"success": len(errors) == 0, "errors": errors}

def check_remote(backup_node_ip, ssh_password, lan_interface, wan_interface):
    errors = []

    # Call validate-configuration on the remote node
    validate_command = json.dumps({
        "role": "backup",
        "lan_interface": lan_interface,
        "wan_interface": wan_interface
    })

    try:
        stdout, stderr, returncode = ssh_execute(
            f"echo '{validate_command}' | /usr/libexec/rpcd/ns.ha call validate-requirements",
            backup_node_ip,
            port=22,
            password=ssh_password
        )
        if returncode != 0:
            errors.append('ssh_connection_failed: ' + stderr)
            return {"success": False, "errors": errors}
    except Exception as e:
        errors.append('ssh_connection_failed: ' + str(e))
        return {"success": False, "errors": errors}

    try:
        if stdout:
            result = json.loads(stdout)
            if not result.get("success"):
                errors.extend(result.get("errors", []))
    except:
        errors.append('invalid_json_response_from_remote_node')
       
    return {"success": len(errors) == 0, "errors": errors}

def list_interfaces():
    u = EUci()
    interfaces = []
    for n in utils.get_all_by_type(u, 'network', 'interface'):
        if n == 'loopback':
            continue
        device = u.get('network', n, 'device', default=None)
        if device and not device.startswith('@'): # exclude aliases
            ha_configured = False
            virtual_ip = ""
            # Find a keepalived instance for the interface named like <interface>_address of type ipaddress
            for ipaddress in utils.get_all_by_type(u, 'keepalived', 'ipaddress'):
                if ipaddress == f"{n}_ipaddress":
                    ha_configured = True
                    virtual_ip = u.get('keepalived', ipaddress, 'address', default=None)
                    break
            interfaces.append({"device": device, "name": n, "ha_configured": ha_configured, "virtual_ip": virtual_ip})
    return { "interfaces": interfaces }

def list_aliases():
    u = EUci()
    aliases = []

    for section in utils.get_all_by_type(u, 'keepalived', 'ipaddress'):
        # Check if section name matches pattern like lan_192_168_100_66_24_ipaddress
        if re.match(r'^[a-zA-Z0-9_]+_\d+_\d+_\d+_\d+_\d+_ipaddress$', section):
            ns_link = u.get('keepalived', section, 'ns_link', default="")
            aliases.append({
                "interface": ns_link.split('/')[-1] if ns_link else "",
                "ipaddr": u.get('keepalived', section, 'address', default=''),
                })
    return { "aliases": aliases }

def add_alias(role, interface, virtual_ip, gateway):
    u = EUci()
    # Retrive interfaces configured for HA
    ha_configured_interfaces = [iface['name'] for iface in list_interfaces()['interfaces'] if iface['ha_configured']]
    if interface not in ha_configured_interfaces:
        raise utils.ValidationError('interface', 'interface_not_configured_for_ha')

    device = u.get('network', interface, 'device', default=None)
    if role == 'primary':
        kinstance_name = 'primary'
    else:
        kinstance_name = 'backup'

    virtual_ips = list(u.get_all('keepalived', kinstance_name, 'virtual_ipaddress'))
    try:
        virtual_routes = list(u.get_all('keepalived', kinstance_name, 'virtual_routes'))
    except:
        virtual_routes = []

    # Create the VIP address for alias
    record_prefix = f'{interface}_{virtual_ip.replace("/", "_").replace(".", "_")}'
    u.set('keepalived', f'{record_prefix}_ipaddress', 'ipaddress')
    u.set('keepalived', f'{record_prefix}_ipaddress', 'name', f'{record_prefix}_ha')
    u.set('keepalived', f'{record_prefix}_ipaddress', 'address', virtual_ip)
    u.set('keepalived', f'{record_prefix}_ipaddress', 'device', device)
    u.set('keepalived', f'{record_prefix}_ipaddress', 'label_suffix', 'ha')
    u.set('keepalived', f'{record_prefix}_ipaddress', 'ns_link', f'network/{interface}')
    # Add the alias VIP to the list of virtual IPs
    u.set('keepalived', kinstance_name, 'virtual_ipaddress', list(set(virtual_ips + [f'{record_prefix}_ha'])))

    if gateway:
        # If there is a gateway, a virtual route for the alias is needed
        u.set('keepalived', f'{record_prefix}_route', 'route')
        u.set('keepalived', f'{record_prefix}_route', 'table', 'main')
        u.set('keepalived', f'{record_prefix}_route', 'address', '0.0.0.0/0')
        u.set('keepalived', f'{record_prefix}_route', 'name', f'{record_prefix}_route')
        u.set('keepalived', f'{record_prefix}_route', 'device', device)
        u.set('keepalived', f'{record_prefix}_route', 'gateway', gateway)
        u.set('keepalived', f'{record_prefix}_route', 'src_addr', virtual_ip.split('/')[0])
        u.set('keepalived', f'{record_prefix}_route', 'ns_link', f'network/{interface}')
        # Add the route to the list of virtual routes
        u.set('keepalived', kinstance_name, 'virtual_routes', list(set(virtual_routes + [f'{record_prefix}_route'])))

    u.commit('keepalived')
    u.commit('network')
    subprocess.run(["/sbin/reload_config"], capture_output=True)

    if role == 'primary':
        # Execute the add-interface API on the backup node
        command = json.dumps({
            "role": "backup",
            "interface": interface,
            "virtual_ip": virtual_ip,
            "gateway": gateway
        })

        output, error = execute_remote_command(f"echo '{command}' | /usr/libexec/rpcd/ns.ha call add-alias")
        if error:
            return utils.generic_error("error_executing_add_alias_on_backup_node")

        return json.loads(output)
    else:
        return { "success": True }
    
def remove_alias(role, interface, virtual_ip):
    u = EUci()
    # Retrive interfaces configured for HA
    ha_configured_interfaces = [iface['name'] for iface in list_interfaces()['interfaces'] if iface['ha_configured']]
    if interface not in ha_configured_interfaces:
        raise utils.ValidationError('interface', 'interface_not_configured_for_ha')

    if role == 'primary':
        kinstance_name = 'primary'
    else:
        kinstance_name = 'backup'

    record_prefix = f'{interface}_{virtual_ip.replace("/", "_").replace(".", "_")}'
    try:
        u.delete('keepalived', f'{record_prefix}_ipaddress')
        u.delete('keepalived', f'{record_prefix}_route')
    except:
        pass

    # Remove the virtual IP from the list of virtual IPs
    try:
        virtual_ips = list(u.get_all('keepalived', kinstance_name, 'virtual_ipaddress'))
    except:
        virtual_ips = []
    virtual_ips = [ip for ip in virtual_ips if ip != f'{record_prefix}_ha']
    u.set('keepalived', kinstance_name, 'virtual_ipaddress', virtual_ips)

    # Remove the virtual route from the list of virtual routes
    try:
        virtual_routes = list(u.get_all('keepalived', kinstance_name, 'virtual_routes'))
    except:
        virtual_routes = []
    virtual_routes = [route for route in virtual_routes if route != f'{record_prefix}_route']
    u.set('keepalived', kinstance_name, 'virtual_routes', virtual_routes)
    
    u.commit('keepalived')
    subprocess.run(["/sbin/reload_config"], capture_output=True)

    if role == 'primary':
        # Execute the add-interface API on the backup node
        command = json.dumps({
            "role": "backup",
            "interface": interface,
            "virtual_ip": virtual_ip
        })

        output, error = execute_remote_command(f"echo '{command}' | /usr/libexec/rpcd/ns.ha call remove-alias")
        if error:
            return utils.generic_error("error_executing_remove_alias_on_backup_node")

        return json.loads(output)
    else:
        return { "success": True }

def remove_interface(role, interface):
    u = EUci()
    # Retrive interfaces configured for HA
    ha_configured_interfaces = [iface['name'] for iface in list_interfaces()['interfaces'] if iface['ha_configured']]
    if interface not in ha_configured_interfaces:
        raise utils.ValidationError('interface', 'interface_not_configured_for_ha')

    if role == 'primary':
        kinstance_name = 'primary'
    else:
        kinstance_name = 'backup'

    original_address = ""
    # Cleanup the keepalived configuration
    for section in u.get_all('keepalived'):
        if u.get('keepalived', section,) == "ipaddress" and u.get('keepalived', section, 'name', default=None) == f'{interface}_ha':
            original_address = u.get('keepalived', section, 'address', default='')
        if u.get('keepalived', section, 'ns_link', default=None) == f'network/{interface}':
            # Remove the section from keepalived
            u.delete('keepalived', section)

    # Remove the virtual IP from the list of virtual IPs
    try:
        virtual_ips = list(u.get_all('keepalived', kinstance_name, 'virtual_ipaddress'))
    except:
        virtual_ips = []
    virtual_ips = [ip for ip in virtual_ips if ip != f'{interface}_ha']
    u.set('keepalived', kinstance_name, 'virtual_ipaddress', virtual_ips)

    # Remove the virtual route from the list of virtual routes
    try:
        virtual_routes = list(u.get_all('keepalived', kinstance_name, 'virtual_routes'))
    except:
        virtual_routes = []
    virtual_routes = [route for route in virtual_routes if route != f'{interface}_route']
    u.set('keepalived', kinstance_name, 'virtual_routes', virtual_routes)

    # Remove the track interface from the list of tracked interfaces
    try:
        track_interfaces = list(u.get_all('keepalived', kinstance_name, 'track_interface'))
    except:
        track_interfaces = []
    track_interfaces = [iface for iface in track_interfaces if iface != f'{interface}_ha']
    u.set('keepalived', kinstance_name, 'track_interface', track_interfaces)

    # Restore the original address of the interface on the primary node
    if role == 'primary' and original_address:
        if '/' in original_address:
            # If the address is a CIDR, split it to get the IP address
            original_address = original_address.split('/')[0]
        u.set('network', interface, 'ipaddr', original_address)

    # Delete the interface from the backup node
    if role == 'backup':
        try:
            u.delete('network', interface)
        except:
            pass

    u.commit('network')
    u.commit('keepalived')
    subprocess.run(["/sbin/reload_config"], capture_output=True)

    if role == 'primary':
        # Execute the add-interface API on the backup node
        command = json.dumps({
            "role": "backup",
            "interface": interface
        })

        output, error = execute_remote_command(f"echo '{command}' | /usr/libexec/rpcd/ns.ha call remove-interface")
        if error:
            return utils.generic_error("error_executing_remove_interface_on_backup_node")

        return json.loads(output)
    else:
        return { "success": True }

def upgrade_remote(image):
    if not os.path.isfile(image):
        return utils.generic_error("image_file_not_found")

    # Upload the image to the backup node
    if not upload_remote_file(image, "/var/run/ns-api-server/uploads/upgrade.img"):
        return utils.generic_error("error_uploading_image_to_backup_node")

    # Prepare the upgrade command
    upgrade_command = json.dumps({
        "image": "upgrade.img"
    })

    # Execute the upgrade command on the backup node
    _, stderr = execute_remote_command(f"echo '{upgrade_command}' | /usr/libexec/rpcd/ns.update call install-uploaded-image")
    if stderr:
        return utils.generic_error("error_executing_upgrade_on_backup_node")
    return {"result": "success"}

def reset(role, pubkey = None):
    # Reset the HA configuration
    uci = EUci()

    # Load SSH configuration to be used later
    port = uci.get('dropbear', 'ha_link', 'Port')
    backup_node_ip = uci.get('keepalived', 'ha_peer', 'address')

    if pubkey is None:
        private_key_path = '/etc/keepalived/keys/id_rsa'
        if os.path.isfile(private_key_path):
            result = subprocess.run(['dropbearkey', '-y', '-f', private_key_path], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if 'ssh-rsa' in line:
                    pubkey = line
                    break

    # Cleanup dropbear configuration
    uci.delete('dropbear', 'ha_link')
    uci.commit('dropbear')

    # Stop and disable keepalived and conntrackd services
    uci.set('keepalived', 'globals', 'enabled', '0')
    uci.commit('keepalived')
    subprocess.run(['/etc/init.d/keepalived', 'stop'], capture_output=True)
    subprocess.run(['/etc/init.d/keepalived', 'disable'], capture_output=True)
    subprocess.run(['/etc/init.d/conntrackd', 'stop'], capture_output=True)
    subprocess.run(['/etc/init.d/conntrackd', 'disable'], capture_output=True)

    # Remove files and directories
    try:
        shutil.rmtree('/usr/share/keepalived/rsync')
        os.remove('/etc/conntrackd/conntrackd.conf')
    except:
        pass

    # Remove public key from root dropbear authorized_keys
    if role == 'backup':
        try:
            # Read the authorized_keys file and remove the public key
            with open('/etc/dropbear/authorized_keys', 'r') as file:
                lines = file.readlines()
            # Write back the lines that do not match the public key
            with open('/etc/dropbear/authorized_keys', 'w') as file:
                for line in lines:
                    if line.strip() != pubkey.strip():
                        file.write(line)
        except:
            pass

    # Reset the keepalived configuration, create an empty configuration file /etc/confik/keepalive
    with open('/etc/config/keepalived', 'w') as file:
        file.write("config globals 'globals'\n")

    # Reload the configuration to apply changes
    subprocess.run(["/sbin/reload_config"], capture_output=True)

    # Re-enable all cron jobs, then restart crond
    if role == 'backup':
        try:
            with open('/etc/crontabs/root', 'r') as file:
                crontab_content = file.read()

            # Uncomment all commented lines (lines starting with #)
            modified_crontab = '\n'.join([
                line[1:] if line.strip().startswith('#') else line
                for line in crontab_content.splitlines()
            ])
            # Write the modified content back
            with open('/etc/crontabs/root', 'w') as file:
                file.write(modified_crontab)
            # Restart crond service
            subprocess.run(['/etc/init.d/cron', 'restart'], capture_output=True)
        except:
            pass

    if role == 'primary':
        # Execute the reset API on the backup node
        command = json.dumps({
            "role": "backup",
            "pubkey": pubkey
        })

        output, error = execute_remote_command(f"echo '{command}' | /usr/libexec/rpcd/ns.ha call reset", backup_node_ip=backup_node_ip, port=port)

        # Remove ssh key after using it inside the execute_remote_command
        try:
            os.remove('/etc/keepalived/keys/id_rsa')
        except:
            pass

        if error:
            return utils.generic_error("error_executing_reset_on_backup_node")

        return json.loads(output)
    else:
        return { "success": True }


cmd = sys.argv[1]

if cmd == 'list':
    print(json.dumps({
        "init-local": {
            "role": "primary",
            "primary_node_ip": "100.100.100.1",
            "backup_node_ip": "100.100.100.2",
            "virtual_ip": "192.168.100.253",
            "pubkey": "ssh-rsa AAAAB....",
            "password": "xxxxxxxx"
        },
        "init-remote": {
            "ssh_password": "Nethesis,1234",
        },
        "check-remote": {
            "backup_node_ip": "100.100.100.2",
            "ssh_password": "Nethesis,1234",
            "lan_interface": "lan",
            "wan_interface": "wan"
        },
        "validate-requirements": { "role": "primary", "lan_interface": "lan", "wan_interface": "wan" },
        "add-wan-interface": {  "role": "primary", "interface": "wan", "virtual_ip": "1.2.3.4/24", "gateway": "1.2.3.5" },
        "add-lan-interface": {
            "role": "primary",
            "primary_node_ip": "100.100.200.1",
            "backup_node_ip": "100.100.200.2",
            "virtual_ip": "192.168.200.250/24"
        },
        "remove-interface": { "role": "primary", "interface": "wan" },
        "add-alias": { "role": "primary", "interface": "wan", "virtual_ip": "1.2.3.5/24" },
        "remove-alias": { "role": "primary", "interface": "wan", "virtual_ip": "1.2.3.5/24" },
        "import-network-config": { [ { "type": "device", "id": "wan", "name": "wan", "device": "eth0.2", "proto": "static", "ipaddr": ""} ] },
        "status": {},
        "list-interfaces": {},
        "list-aliases": {},
        "reset": {"role": "primary", "pubkey": "ssh-rsa AAAAB...."},
        "upgrade-remote": { "image": "/tmp/upgrade.img.gz" }
        }))
else:
    action = sys.argv[2]
    if action == "status":
        ret = status()
    elif action == "list-interfaces":
        ret = list_interfaces()
    elif action == "list-aliases":
        ret = list_aliases()
    else:
        # Paramaters:
        args = json.loads(sys.stdin.read())
        if action == "init-local":
            ret = init_local(args.get('role'), args.get('primary_node_ip'), args.get('backup_node_ip'), args.get('virtual_ip'), args.get('pubkey'), args.get('password'))
        elif action == "init-remote":
            ret = init_remote(args.get('ssh_password'))
        elif action == "add-wan-interface":
            ret = add_wan_interface(args.get('role'), args.get('interface'), args.get('virtual_ip'), args.get('gateway', ''))
        elif action == "add-lan-interface":
            ret = add_lan_interface(args.get('role'), args.get('primary_node_ip'), args.get('backup_node_ip'), args.get('virtual_ip'))
        elif action == "remove-interface":
            ret = remove_interface(args.get('role'), args.get('interface'))
        elif action == "check-remote":
            ret = check_remote(args.get('backup_node_ip'), args.get('ssh_password'), args.get('lan_interface'), args.get('wan_interface'))
        elif action == "validate-requirements":
            ret = validate_requirements(args.get('role'), args.get('lan_interface'), args.get('wan_interface'))
        elif action == "import-network-config":
            ret = import_network_config(args)
        elif action == "add-alias":
            ret = add_alias(args.get('role'), args.get('interface'), args.get('virtual_ip'), args.get('gateway', ''))
        elif action == "remove-alias":
            ret = remove_alias(args.get('role'), args.get('interface'), args.get('virtual_ip'))
        elif action == "reset":
            ret = reset(args.get('role'), args.get('pubkey'))
        elif action == "upgrade-remote":
            ret = upgrade_remote(args.get('image'))

    print(json.dumps(ret))
