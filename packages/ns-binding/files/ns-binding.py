#!/usr/bin/python3

#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from euci import EUci
from nethsec import utils
import subprocess
from jinja2 import Environment, BaseLoader

template = """
table inet ns-binding
delete table inet ns-binding
table inet ns-binding {
    set ipV4Bound {
        type ipv4_addr
        flags interval
        auto-merge
        {% if reservations | length > 0 -%}
        elements = { {{ reservations.values() | join(', ') }} }
        {%- endif %}
    }

    set etherBound {
        type ether_addr
        flags interval
        auto-merge
        {% if reservations | length > 0 -%}
        elements = { {{ reservations.keys() | join(', ') }} }
        {%- endif %}
    }

    set bindingListV4 {
        type ether_addr . ipv4_addr
        policy memory
        flags interval
        auto-merge
        {% if reservations | length > 0 -%}
        elements = {
            {%- for mac, ip in reservations.items() -%}
            {{ mac }} . {{ ip }},
            {%- endfor -%}
        }
        {%- endif %}
    }

    chain input {
        type filter hook input priority -110; policy drop;
        ct state established,related accept
        iifname != { {{ dhcp_interfaces | join(' , ') }} } accept
        udp dport 67-68 accept
        {%- for iface, mode in dhcp_interfaces.items() %}
        {%- if mode == '1' %}
        iifname {{ iface }} jump soft-binding
        {%- elif mode == '2' %}
        iifname {{ iface }} jump binding
        {%- endif %}
        {%- endfor %}
        log flags all prefix "ns-binding DROP: " counter
    }

    chain forward {
        type filter hook forward priority -110; policy drop;
        ct state established,related accept
        iifname != { {{ dhcp_interfaces | join(' , ') }} } accept
        {%- for iface, mode in dhcp_interfaces.items() %}
        {%- if mode == '1' %}
        iifname {{ iface }} jump soft-binding
        {%- elif mode == '2' %}
        iifname {{ iface }} jump binding
        {%- endif %}
        {%- endfor %}
        log flags all prefix "ns-binding DROP: " counter
    }

    chain soft-binding {
        ether saddr @etherBound counter goto binding
        ip saddr @ipV4Bound counter goto binding
        accept
    }

    chain binding {
        ether saddr . ip saddr @bindingListV4 counter accept
    }
}
"""

e_uci = EUci()

# Filter out DHCP servers that are not ns-binding enabled
network_interfaces = {
    name: iface.get('device')
    for name, iface in utils.get_all_by_type(e_uci, 'network', 'interface').items()
}
dhcp_servers = [
    server for server in utils.get_all_by_type(e_uci, 'dhcp', 'dhcp').values()
    if server.get('ns_binding', '0') != '0' and server.get('interface') in network_interfaces
]
# generate list of interfaces used by DHCP servers
dhcp_interfaces = {
    network_interfaces[server.get('interface')]: server.get('ns_binding')
    for server in dhcp_servers
}

if len(dhcp_interfaces) > 0:
    # reservation entry
    reservations = {
        reservation['mac']: reservation['ip']
        for reservation in utils.get_all_by_type(e_uci, 'dhcp', 'host').values()
    }
    template = Environment(loader=BaseLoader()).from_string(template)
    render = template.render(reservations=reservations, dhcp_interfaces=dhcp_interfaces)
    subprocess.run(['/usr/sbin/nft', '-f', '-'], input=render.encode(), check=True)
    print('ns-binding table created')
else:
    subprocess.run(['/usr/sbin/nft', 'delete', 'table', 'inet', 'ns-binding'], capture_output=True)
    print('ns-binding table deleted')
