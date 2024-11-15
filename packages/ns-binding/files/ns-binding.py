#!/usr/bin/python3

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from euci import EUci
from nethsec import utils
import subprocess

e_uci = EUci()

# Filter out DHCP servers that are not ns-binding enabled
network_interfaces = {
    name: iface.get('device')
    for name, iface in utils.get_all_by_type(e_uci, 'network', 'interface').items()
}
dhcp_servers = [
    server for server in utils.get_all_by_type(e_uci, 'dhcp', 'dhcp').values()
    if server.get('ns_binding', '0') == '1' and server.get('interface') in network_interfaces
]
# generate list of interfaces used by DHCP servers
dhcp_interfaces = [
    network_interfaces[server.get('interface')]
    for server in dhcp_servers
]

if len(dhcp_interfaces) > 0:
    # reservation entry
    reservations = {
        reservation['mac']: reservation['ip']
        for reservation in utils.get_all_by_type(e_uci, 'dhcp', 'host').values()
    }
    # file generation
    binding_items = [f'{mac} . {ip}' for mac, ip in reservations.items()]
    file = f"""
    table inet ns-binding
    delete table inet ns-binding

    table inet ns-binding {{
    
        set bindingListV4 {{
            type ether_addr . ipv4_addr
            policy memory
            flags interval
            auto-merge
            {'elements = {' if len(binding_items) > 0 else ''}
                {', '.join(binding_items)}
            {'}' if len(binding_items) > 0 else ''}
        }}
        
        # if interface is not in other_interfaces, allow dhcp queries and check with bindingListV4 for all rest
        chain input {{
            type filter hook input priority -110; policy drop;
            ct state established,related counter accept
            iifname != {{ {' , '.join(dhcp_interfaces)} }} counter accept
            udp dport 67 counter accept
            udp dport 68 counter accept
            ether saddr . ip saddr @bindingListV4 counter accept
        }}
        
        chain lan-forward {{
            type filter hook forward priority -110; policy drop;
            ct state established,related counter accept
            iifname != {{ {' , '.join(dhcp_interfaces)} }} counter accept
            ether saddr . ip saddr @bindingListV4 counter accept
        }}
    }}
    """
    subprocess.run(['/usr/sbin/nft', '-f', '-'], input=file.encode(), check=True)
    print('ns-binding table created')
else:
    subprocess.run(['/usr/sbin/nft', 'delete', 'table', 'inet', 'ns-binding'], capture_output=True)
    print('ns-binding table deleted')
