#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

DEFAULT_OUTPUT_DIR = "/var/run/ns-audit/latest"
RAW_SNAPSHOT_NAME = "raw_snapshot.json"
INVENTORY_NAME = "inventory.json"
FINDINGS_NAME = "findings.json"
COMPLIANCE_MAPPING_NAME = "compliance_mapping.json"
SUMMARY_NAME = "summary.json"
REPORT_NAME = "audit-report.html"
REPORT_BUNDLE_NAME = "audit-report.tar.gz"

COMMAND_TIMEOUT = 8
COMMAND_OUTPUT_BYTES = 256 * 1024
MAX_TEXT_FILE_BYTES = 256 * 1024
MAX_LOG_FILE_BYTES = 512 * 1024
MAX_LOG_LINES = 5000

VICTORIA_LOGS_URL = "http://127.0.0.1:9428"
VICTORIA_LOGS_QUERY_LIMIT = 500

LATEST_RELEASE_URL = "https://updates.nethsecurity.nethserver.org/latest_release"
UPDATE_CHECK_TIMEOUT = 10

# All files under /etc/config/ are collected via glob; this tuple holds
# non-UCI files that are also collected for identity/system analysis.
CONFIG_DIR_GLOB = "/etc/config/*"
CONFIG_FILES = (
    "/etc/passwd",
    "/etc/group",
    "/etc/os-release",
    "/etc/openwrt_release",
    "/etc/swanctl/swanctl.conf",
)

LOGROTATE_GLOBS = (
    "/etc/logrotate.conf",
    "/etc/logrotate.d/*",
)

LOG_FILE_GLOBS = (
    "/var/log/messages*",
    "/mnt/data/log/messages*",
)

UCI_PACKAGES = (
    "firewall",
    "network",
    "system",
    "dropbear",
    "rpcd",
    "users",
    "openvpn",
    "snort",
    "suricata",
    "rsyslog",
    "banip",
    "ns-plug",
    "acme",
    "keepalived",
)

UBUS_CALLS = (
    ("system_board", ("ubus", "call", "system", "board")),
    ("system_info", ("ubus", "call", "system", "info")),
    ("service_list", ("ubus", "call", "service", "list")),
)
