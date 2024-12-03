# Do not edit, automatically generated.  See /usr/share/snort/templates.
{%
// Copyright (c) 2023-2024 Eric Fahlgren <eric.fahlgren@gmail.com>
// SPDX-License-Identifier: GPL-2.0

let queues     = `${nfq.queue_start}-${int(nfq.queue_start)+int(nfq.queue_count)-1}`;
let chain_type = nfq.chain_type;
-%}

table inet snort {
    set bypass_src_v4 {
		type ipv4_addr
		flags interval
		include "/var/ns-snort/bypass_src_v4.conf"
	}
	set bypass_dst_v4 {
		type ipv4_addr
		flags interval
		include "/var/ns-snort/bypass_dst_v4.conf"
	}
	set bypass_src_v6 {
		type ipv6_addr
		flags interval
		include "/var/ns-snort/bypass_src_v6.conf"
	}
	set bypass_dst_v6 {
		type ipv6_addr
		flags interval
		include "/var/ns-snort/bypass_dst_v6.conf"
	}

	chain {{ chain_type }}_{{ snort.mode }} {
		type filter  hook {{ chain_type }}  priority {{ nfq.chain_priority }}
		policy accept
		ip saddr @bypass_src_v4 counter accept
		ip daddr @bypass_dst_v4 counter accept
		ip6 saddr @bypass_src_v6 counter accept
		ip6 daddr @bypass_dst_v6 counter accept
		{% if (nfq.include) {
		  // We use the ucode include here, so that the included file is also
		  // part of the template and can use values passed in from the config.
		  printf("\n\t\t" + rpad(`#-- Include from '${nfq.include}'`, ">", 64) + "\n");
		  include(nfq.include, { snort, nfq });
		  printf("\t\t" + rpad("#-- End of included file.", "<", 64) + "\n\n");
		} %}
		counter  queue flags bypass to {{ queues }}
	}
}
