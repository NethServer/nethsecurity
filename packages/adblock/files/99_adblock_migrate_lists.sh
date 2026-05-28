#!/bin/sh

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Migrate local allow/block list files to staged UCI storage.
# Skip once the dedicated section is already present.
uci -q get adblock.ns_lists >/dev/null 2>&1 && exit 0

uci set adblock.ns_lists=ns_lists

# Local lists changed name since adblock 4.5.5
mv /etc/adblock/adblock.whitelist /etc/adblock/adblock.allowlist 2>/dev/null || :
mv /etc/adblock/adblock.blacklist /etc/adblock/adblock.blocklist 2>/dev/null || :

for type in allowlist blocklist; do
	file="/etc/adblock/adblock.${type}"
	[ -f "${file}" ] || continue

	while IFS= read -r line || [ -n "${line}" ]; do
		[ -z "${line}" ] && continue
		uci add_list "adblock.ns_lists.${type}=${line}"
	done < "${file}"
done

uci commit adblock
