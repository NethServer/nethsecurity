#!/usr/bin/env python

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

import os
import subprocess

from euci import EUci
from jinja2 import Environment, BaseLoader

NFQ_TABLE_FILE = '/tmp/netifyd-nfq-table-definition.nft'

NFQ_TABLE = """
table inet netifyd { }
delete table inet netifyd

table inet netifyd {
    set nfq_bypass_v4 {
        type ipv4_addr; flags interval; auto-merge;
{%- if v4_elements %}
        elements = { {{ v4_elements | join(', ') }} }
{%- endif %}
    }

    set nfq_bypass_v6 {
        type ipv6_addr; flags interval; auto-merge;
{%- if v6_elements %}
        elements = { {{ v6_elements | join(', ') }} }
{%- endif %}
    }

    # push input packets to userspace queues for DPI analysis
    chain nfq_input {
        type filter hook input priority filter + 10; policy accept;
        iifname lo accept

        # Accept traffic matching bypass set
        ip saddr @nfq_bypass_v4 accept
        ip daddr @nfq_bypass_v4 accept
        ip6 saddr @nfq_bypass_v6 accept
        ip6 daddr @nfq_bypass_v6 accept

        # Netifyd only analyzes the first 32 packets
        ct packets > 32 accept

        # Traffic to queues 50-53
        queue flags bypass to 50-53
    }

    # push forward packets to userspace queues for DPI analysis
    chain nfq_forward {
        type filter hook forward priority filter + 10; policy accept;

        # Accept traffic matching bypass set
        ip saddr @nfq_bypass_v4 accept
        ip daddr @nfq_bypass_v4 accept
        ip6 saddr @nfq_bypass_v6 accept
        ip6 daddr @nfq_bypass_v6 accept

        # Netifyd only analyzes the first 32 packets
        ct packets > 32 accept

        # Traffic to queues 50-53
        queue flags bypass to 50-53
    }

    # push output packets to userspace queues for DPI analysis
    chain nfq_output {
        type filter hook output priority filter + 10; policy accept;
        oifname lo accept

        # Accept traffic matching bypass set
        ip saddr @nfq_bypass_v4 accept
        ip daddr @nfq_bypass_v4 accept
        ip6 saddr @nfq_bypass_v6 accept
        ip6 daddr @nfq_bypass_v6 accept

        # Netifyd only analyzes the first 32 packets
        ct packets > 32 accept

        # Traffic to queues 50-53
        queue flags bypass to 50-53
    }
}
"""

def generate_nfq_table():
    e_uci = EUci()
    
    # Read IPv4 and IPv6 bypass lists from UCI
    v4_elements = e_uci.get('netifyd', 'config', 'bypassv4', dtype=str, list=True, default=[])
    v6_elements = e_uci.get('netifyd', 'config', 'bypassv6', dtype=str, list=True, default=[])
    
    template = Environment(loader=BaseLoader()).from_string(NFQ_TABLE)
    render = template.render(
        v4_elements=v4_elements,
        v6_elements=v6_elements,
    )
    
    # Apply nftables
    with open(NFQ_TABLE_FILE, 'w') as f:
        f.write(render)
    try:
        subprocess.run(['nft', '-f', NFQ_TABLE_FILE], check=True, capture_output=True)
        os.unlink(NFQ_TABLE_FILE)
    except subprocess.CalledProcessError as e:
        print(f"Error applying nftables configuration: {e.stderr.decode()}")


if __name__ == "__main__":
    generate_nfq_table()
