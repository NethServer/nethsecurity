#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""Firewall zones, forwarding, redirect, and exposure analyzer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from ..models import (
        build_finding,
        build_result,
        is_enabled_section,
        option_value,
        section_name,
        section_type,
        string_list,
        to_bool,
        uci_sections,
    )
except ImportError:  # pragma: no cover - supports direct execution during development
    from ns_audit.models import (
        build_finding,
        build_result,
        is_enabled_section,
        option_value,
        section_name,
        section_type,
        string_list,
        to_bool,
        uci_sections,
    )

AREA = "firewall"
WAN_NAMES = {"wan", "wan6", "wwan", "ns_wan", "ns_wan6"}
INTERNAL_NAMES = {
    "lan",
    "guest",
    "dmz",
    "mgmt",
    "ns_lan",
    "ns_guest",
    "ns_dmz",
    "ns_mgmt",
}
# Ports that indicate direct administrative service exposure from WAN (not HTTPS proxy)
ADMIN_PORTS_STRICT = {"22", "80", "4443", "8000", "8080", "8443", "9090", "9091"}
# 443 is treated separately as it commonly hosts legitimate HTTPS proxy pass
HTTPS_PORTS = {"443", "8443"}
# ICMP protocols — WAN-facing ICMP (ping) is intentional and not a risk
ICMP_PROTOS = {"icmp", "icmp6", "ipv6-icmp"}


def _zone_name(section: Mapping[str, Any]) -> str:
    return str(option_value(section, "name", section_name(section))).strip()


def _is_wan_zone(zone: Mapping[str, Any]) -> bool:
    name = str(zone.get("name", "")).lower()
    networks = {str(network).lower() for network in zone.get("networks", [])}
    return (
        name in WAN_NAMES
        or bool(networks & WAN_NAMES)
        or to_bool(zone.get("masq"), default=False)
    )


def _ports(value: Any) -> list[str]:
    ports = []
    for item in string_list(value):
        if ":" in item:
            ports.extend(part for part in item.split(":") if part)
        else:
            ports.append(item)
    return sorted(set(ports))


def _port_is_admin(ports: list[str]) -> bool:
    if not ports:
        return False
    for port in ports:
        if port in ADMIN_PORTS_STRICT:
            return True
        if "-" in port:
            start, _, end = port.partition("-")
            if (
                start.isdigit()
                and end.isdigit()
                and any(int(start) <= int(admin) <= int(end) for admin in ADMIN_PORTS_STRICT)
            ):
                return True
    return False


def _port_is_https_only(ports: list[str]) -> bool:
    """True when the only exposed ports are HTTPS (443/8443) — likely proxy pass."""
    return bool(ports) and all(p in HTTPS_PORTS for p in ports)


def _is_icmp_only(proto_list: list[str]) -> bool:
    """True when the rule only covers ICMP protocols (ping is expected from WAN)."""
    return bool(proto_list) and all(p.lower() in ICMP_PROTOS for p in proto_list)


def _normalize_firewall(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    zones = []
    forwardings = []
    redirects = []
    rules = []
    for section in uci_sections(raw_snapshot, "firewall"):
        stype = section_type(section)
        if stype == "zone":
            zones.append(
                {
                    "id": section_name(section),
                    "name": _zone_name(section),
                    "networks": string_list(
                        option_value(section, ("network", "networks"), [])
                    ),
                    "input": str(option_value(section, "input", "")).upper(),
                    "output": str(option_value(section, "output", "")).upper(),
                    "forward": str(option_value(section, "forward", "")).upper(),
                    "masq": to_bool(option_value(section, "masq"), default=False),
                    "mtu_fix": to_bool(option_value(section, "mtu_fix"), default=False),
                    "enabled": is_enabled_section(section, default=True),
                }
            )
        elif stype == "forwarding":
            forwardings.append(
                {
                    "id": section_name(section),
                    "src": str(option_value(section, "src", "")),
                    "dest": str(option_value(section, "dest", "")),
                    "enabled": is_enabled_section(section, default=True),
                }
            )
        elif stype == "redirect":
            ports = _ports(
                option_value(section, ("src_dport", "src_port", "dest_port"), [])
            )
            redirects.append(
                {
                    "id": section_name(section),
                    "name": str(option_value(section, "name", section_name(section))),
                    "src": str(option_value(section, "src", "")),
                    "dest": str(option_value(section, "dest", "")),
                    "proto": string_list(option_value(section, "proto", [])),
                    "src_dport": ports,
                    "dest_ip_present": bool(option_value(section, "dest_ip")),
                    "dest_port": _ports(option_value(section, "dest_port", [])),
                    "target": str(option_value(section, "target", "DNAT")).upper(),
                    "enabled": is_enabled_section(section, default=True),
                }
            )
        elif stype == "rule":
            proto_list = string_list(option_value(section, "proto", []))
            rules.append(
                {
                    "id": section_name(section),
                    "name": str(option_value(section, "name", section_name(section))),
                    "src": str(option_value(section, "src", "")),
                    "dest": str(option_value(section, "dest", "")),
                    "proto": proto_list,
                    "icmp_only": _is_icmp_only(proto_list),
                    "dest_port": _ports(
                        option_value(section, ("dest_port", "src_dport"), [])
                    ),
                    "target": str(option_value(section, "target", "")).upper(),
                    "family": str(option_value(section, "family", "any")),
                    "system_rule": to_bool(
                        option_value(section, "system_rule"), default=False
                    ),
                    "enabled": is_enabled_section(section, default=True),
                }
            )
    wan_zones = {zone["name"] for zone in zones if _is_wan_zone(zone)}
    exposed_services = []
    for rule in rules:
        if not rule.get("enabled") or rule.get("target") != "ACCEPT":
            continue
        # Skip ICMP-only rules — WAN ping (echo-request) is intentional and not a risk
        if rule.get("icmp_only"):
            continue
        if rule.get("src") in wan_zones or str(rule.get("src")).lower() in WAN_NAMES:
            ports = rule.get("dest_port", [])
            exposed_services.append(
                {
                    "type": "rule",
                    "id": rule.get("id"),
                    "name": rule.get("name"),
                    "ports": ports,
                    "admin_port": _port_is_admin(ports),
                    "https_only": _port_is_https_only(ports),
                }
            )
    for redirect in redirects:
        if not redirect.get("enabled"):
            continue
        if (
            redirect.get("src") in wan_zones
            or str(redirect.get("src")).lower() in WAN_NAMES
        ):
            ports = redirect.get("src_dport", [])
            exposed_services.append(
                {
                    "type": "redirect",
                    "id": redirect.get("id"),
                    "name": redirect.get("name"),
                    "ports": ports,
                    "admin_port": _port_is_admin(ports),
                    "https_only": _port_is_https_only(ports),
                }
            )
    return {
        "zones": zones,
        "wan_zones": sorted(wan_zones),
        "forwardings": forwardings,
        "redirects": redirects,
        "rules": rules,
        "exposed_services": exposed_services,
    }


def analyze(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    inventory = _normalize_firewall(raw_snapshot)
    findings = []
    wan_zones = set(inventory["wan_zones"])

    if not inventory["zones"]:
        findings.append(
            build_finding(
                "firewall-no-zones",
                "No firewall zones found in snapshot",
                "high",
                AREA,
                "firewall",
                "The sanitized snapshot did not contain firewall zone definitions, preventing boundary validation.",
                {},
                "Verify that /etc/config/firewall is collected and define explicit zones with default-deny WAN policy.",
                nist=("AC-4", "CM-6", "SC-7"),
                acn=("network_segmentation", "risk_management"),
            )
        )

    for zone in inventory["zones"]:
        if not zone.get("enabled", True):
            continue
        if zone.get("name") in wan_zones and zone.get("input") == "ACCEPT":
            findings.append(
                build_finding(
                    f"firewall-wan-input-accept-{zone['name']}",
                    "WAN zone accepts inbound traffic by default",
                    "critical",
                    AREA,
                    "zone",
                    "A WAN-like zone has input policy ACCEPT, allowing unsolicited traffic unless later rules block it.",
                    {
                        "zone": zone.get("name"),
                        "input": zone.get("input"),
                        "networks": zone.get("networks"),
                    },
                    "Set WAN input policy to REJECT or DROP and allow only explicitly required services.",
                    nist=("AC-4", "CM-7", "SC-7"),
                    acn=("network_segmentation", "risk_management"),
                )
            )
        if zone.get("name") in wan_zones and zone.get("forward") == "ACCEPT":
            findings.append(
                build_finding(
                    f"firewall-wan-forward-accept-{zone['name']}",
                    "WAN zone forwards traffic by default",
                    "high",
                    AREA,
                    "zone",
                    "A WAN-like zone has forwarding policy ACCEPT, weakening boundary enforcement.",
                    {"zone": zone.get("name"), "forward": zone.get("forward")},
                    "Set WAN forward policy to REJECT or DROP and create scoped forwarding rules only where needed.",
                    nist=("AC-4", "CM-7", "SC-7"),
                    acn=("network_segmentation",),
                )
            )

    for forwarding in inventory["forwardings"]:
        if not forwarding.get("enabled", True):
            continue
        src = str(forwarding.get("src"))
        dest = str(forwarding.get("dest"))
        if src in wan_zones and dest not in wan_zones:
            findings.append(
                build_finding(
                    f"firewall-wan-forwarding-{forwarding['id']}",
                    "Forwarding from WAN to an internal zone is enabled",
                    "high",
                    AREA,
                    "forwarding",
                    "Traffic can be forwarded from a WAN-like zone to an internal destination zone.",
                    forwarding,
                    "Remove broad WAN-to-internal forwardings and replace them with tightly scoped DNAT or proxy rules if required.",
                    nist=("AC-4", "SC-7", "CM-7"),
                    acn=("network_segmentation", "risk_management"),
                )
            )

    for redirect in inventory["redirects"]:
        if not redirect.get("enabled", True):
            continue
        src = str(redirect.get("src"))
        if src not in wan_zones and src.lower() not in WAN_NAMES:
            continue
        ports = redirect.get("src_dport", [])
        severity = "high" if _port_is_admin(ports) or not ports else "medium"
        findings.append(
            build_finding(
                f"firewall-public-redirect-{redirect['id']}",
                "Public port-forward rule is enabled",
                severity,
                AREA,
                "redirect",
                "A DNAT/redirect rule exposes an internal service from a WAN-like source zone.",
                redirect,
                "Confirm business need, restrict source addresses, prefer VPN access, and remove unused public port-forwards.",
                nist=("AC-4", "CM-7", "SC-7"),
                acn=("network_segmentation", "risk_management"),
            )
        )

    for service in inventory["exposed_services"]:
        if service.get("type") == "rule" and service.get("https_only"):
            # Port 443 (HTTPS) is commonly used for proxy pass to legitimate services.
            # This is advisory: it is not a critical risk but the admin UI should
            # ideally not be reachable on the same public HTTPS port.
            findings.append(
                build_finding(
                    f"firewall-https-wan-access-{service['id']}",
                    "HTTPS port 443 is accessible from WAN",
                    "info",
                    AREA,
                    "rule",
                    "Port 443 is allowed from a WAN zone. If this routes to a reverse-proxy or legitimate web service, "
                    "it is not a risk in itself. However, if the administrator UI is reachable on port 443 from WAN, "
                    "consider restricting access to a VPN or a non-standard port.",
                    service,
                    "If the admin UI is on port 443, move it to a non-standard port or restrict WAN access via VPN.",
                    nist=("AC-17", "CM-7", "SC-7"),
                    acn=("network_segmentation", "identity_access_governance"),
                )
            )
        elif service.get("type") == "rule" and service.get("admin_port"):
            findings.append(
                build_finding(
                    f"firewall-admin-service-exposed-{service['id']}",
                    "Administrative service port is allowed from WAN",
                    "critical",
                    AREA,
                    "rule",
                    "A firewall ACCEPT rule exposes a common management port from a WAN-like zone.",
                    service,
                    "Block WAN access to management ports and require access through a VPN or trusted management network.",
                    nist=("AC-4", "AC-17", "CM-7", "SC-7"),
                    acn=("network_segmentation", "identity_access_governance"),
                )
            )
        elif service.get("type") == "rule" and not service.get("ports"):
            findings.append(
                build_finding(
                    f"firewall-broad-accept-{service['id']}",
                    "Broad WAN ACCEPT rule has no destination port scope",
                    "high",
                    AREA,
                    "rule",
                    "A WAN-facing ACCEPT rule lacks destination port scoping.",
                    service,
                    "Restrict the rule to required protocols, destination ports, and source addresses or remove it.",
                    nist=("AC-4", "CM-7", "SC-7"),
                    acn=("network_segmentation", "risk_management"),
                )
            )

    return build_result(AREA, inventory, findings)


analyze_firewall = analyze
