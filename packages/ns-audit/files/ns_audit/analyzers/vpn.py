#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""OpenVPN and WireGuard crypto posture analyzer."""

from __future__ import annotations

import re
import time
from collections.abc import Mapping
from typing import Any

try:
    from ..models import (
        build_finding,
        build_result,
        command_json,
        contains_indicator,
        fingerprint,
        get_file,
        has_unredacted_secret,
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
        command_json,
        contains_indicator,
        fingerprint,
        get_file,
        has_unredacted_secret,
        is_enabled_section,
        option_value,
        section_name,
        section_type,
        string_list,
        to_bool,
        uci_sections,
    )

AREA = "vpn"
WEAK_CIPHER_TOKENS = ("BF-CBC", "DES", "3DES", "RC2", "NULL", "MD5")
WEAK_AUTH_TOKENS = ("MD5", "SHA1")
MFA_INDICATORS = ("totp", "otp", "mfa", "2fa", "two_factor", "two-factor")
FULL_TUNNEL_ALLOWED_IPS = {"0.0.0.0/0", "::/0"}
STALE_HANDSHAKE_SECONDS = 7 * 24 * 60 * 60


def _tls_version_number(value: Any) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", str(value or ""))
    return float(match.group(1)) if match else None


def _cipher_values(section: Mapping[str, Any]) -> list[str]:
    values = []
    for key in (
        "data_ciphers",
        "ncp_ciphers",
        "tls_cipher",
        "tls_ciphersuites",
        "cipher",
    ):
        values.extend(string_list(option_value(section, key, [])))
    return [value.upper() for value in values]


def _weak_cipher_values(values: list[str]) -> list[str]:
    return sorted(
        {value for value in values for token in WEAK_CIPHER_TOKENS if token in value}
    )


def _openvpn_instances(raw_snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    instances = []
    for section in uci_sections(raw_snapshot, "openvpn"):
        if section_type(section) and section_type(section) != "openvpn":
            continue
        ciphers = _cipher_values(section)
        instance = {
            "id": section_name(section),
            "enabled": is_enabled_section(section, default=False),
            "proto": str(option_value(section, "proto", "")),
            "port": str(option_value(section, "port", "")),
            "dev": str(option_value(section, "dev", "")),
            "mode": str(option_value(section, "mode", "")),
            "tls_version_min": str(option_value(section, "tls_version_min", "")),
            "cipher_values": ciphers,
            "weak_cipher_values": _weak_cipher_values(ciphers),
            "auth_digest": str(option_value(section, "auth", "")).upper(),
            "compression_enabled": any(
                to_bool(option_value(section, key), default=False)
                for key in ("comp_lzo", "compress", "allow_compression")
            ),
            "duplicate_cn": to_bool(
                option_value(section, "duplicate_cn"), default=False
            ),
            "client_to_client": to_bool(
                option_value(section, "client_to_client"), default=False
            ),
            "user_password_auth": bool(
                option_value(
                    section, ("auth_user_pass_verify", "plugin", "script_security")
                )
            ),
            "mfa_indicator": contains_indicator(section, MFA_INDICATORS),
            "secret_material_present": any(
                bool(option_value(section, key))
                for key in ("key", "pkcs12", "secret", "tls_auth", "tls_crypt")
            ),
            "unredacted_secret_detected": has_unredacted_secret(section),
        }
        instances.append(instance)
    return instances


def _wireguard_status(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    status = command_json(raw_snapshot, ("wg-json", "wg show", "wireguard"))
    return status if isinstance(status, Mapping) else {}


def _handshake_age(value: Any) -> int | None:
    if value in (None, "", 0, "0"):
        return None
    try:
        number = int(float(str(value)))
    except ValueError:
        return None
    if number > 1_000_000_000:
        return max(0, int(time.time()) - number)
    return number


def _status_peers(
    status: Mapping[str, Any], interface_name: str
) -> list[dict[str, Any]]:
    interface_status = (
        status.get(interface_name) if isinstance(status, Mapping) else None
    )
    if not isinstance(interface_status, Mapping):
        return []
    raw_peers = interface_status.get("peers", [])
    if isinstance(raw_peers, Mapping):
        iterator = raw_peers.items()
    elif isinstance(raw_peers, list):
        iterator = [(str(index), peer) for index, peer in enumerate(raw_peers)]
    else:
        return []
    peers = []
    for peer_id, peer_data in iterator:
        if not isinstance(peer_data, Mapping):
            continue
        latest = (
            peer_data.get("latest_handshake")
            or peer_data.get("latestHandshake")
            or peer_data.get("last_handshake")
        )
        peers.append(
            {
                "id": str(peer_id),
                "public_key_fingerprint": fingerprint(peer_id),
                "allowed_ips": string_list(
                    peer_data.get("allowed_ips") or peer_data.get("allowedIps")
                ),
                "endpoint_present": bool(peer_data.get("endpoint")),
                "latest_handshake_age_seconds": _handshake_age(latest),
            }
        )
    return peers


def _wireguard_inventory(raw_snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    network_sections = uci_sections(raw_snapshot, "network")
    status = _wireguard_status(raw_snapshot)
    interfaces = []
    for section in network_sections:
        if (
            section_type(section) != "interface"
            or str(option_value(section, "proto", "")).lower() != "wireguard"
        ):
            continue
        name = section_name(section)
        peers = []
        for peer in network_sections:
            peer_type = section_type(peer)
            if not peer_type.startswith("wireguard_"):
                continue
            peer_interface = peer_type.replace("wireguard_", "", 1)
            if peer_interface != name:
                continue
            public_key = option_value(peer, "public_key", "")
            peers.append(
                {
                    "id": section_name(peer),
                    "interface": peer_interface,
                    "public_key_present": bool(public_key),
                    "public_key_fingerprint": fingerprint(public_key),
                    "preshared_key_present": bool(option_value(peer, "preshared_key")),
                    "allowed_ips": string_list(option_value(peer, "allowed_ips", [])),
                    "route_allowed_ips": to_bool(
                        option_value(peer, "route_allowed_ips"), default=False
                    ),
                    "endpoint_present": bool(
                        option_value(peer, "endpoint_host")
                        or option_value(peer, "endpoint_port")
                    ),
                    "persistent_keepalive": str(
                        option_value(peer, "persistent_keepalive", "")
                    ),
                    "unredacted_secret_detected": has_unredacted_secret(peer),
                }
            )
        status_peers = _status_peers(status, name)
        if status_peers:
            peers_by_fingerprint = {
                peer.get("public_key_fingerprint"): peer
                for peer in peers
                if peer.get("public_key_fingerprint")
            }
            for status_peer in status_peers:
                match = peers_by_fingerprint.get(
                    status_peer.get("public_key_fingerprint")
                )
                if match:
                    match["latest_handshake_age_seconds"] = status_peer.get(
                        "latest_handshake_age_seconds"
                    )
                    match["endpoint_present"] = match.get(
                        "endpoint_present"
                    ) or status_peer.get("endpoint_present")
                else:
                    peers.append(status_peer)
        private_key = option_value(section, "private_key", "")
        interfaces.append(
            {
                "id": name,
                "listen_port": str(option_value(section, "listen_port", "")),
                "addresses": string_list(
                    option_value(section, ("addresses", "ipaddr"), [])
                ),
                "private_key_present": bool(private_key),
                "unredacted_secret_detected": has_unredacted_secret(
                    {"private_key": private_key}
                ),
                "peers": peers,
            }
        )
    return interfaces


def _swanctl_inventory(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    content = get_file(raw_snapshot, "/etc/swanctl/swanctl.conf")
    if not content:
        return {"file_present": False, "configured": False}
    active_lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return {
        "file_present": True,
        "configured": bool(active_lines),
        "active_directive_count": len(active_lines),
    }


def _ipsec_inventory(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    remotes = []
    tunnels = []
    proposals = []
    for section in uci_sections(raw_snapshot, "ipsec"):
        item_type = section_type(section)
        if item_type == "remote":
            remotes.append(
                {
                    "id": section_name(section),
                    "name": str(option_value(section, "ns_name", "")),
                    "enabled": is_enabled_section(section, default=False),
                    "gateway": str(option_value(section, "gateway", "")),
                    "authentication_method": str(
                        option_value(section, "authentication_method", "")
                    ),
                    "keyexchange": str(option_value(section, "keyexchange", "")),
                    "preshared_key_present": bool(
                        option_value(section, "pre_shared_key")
                    ),
                    "tunnels": string_list(option_value(section, "tunnel", [])),
                    "crypto_proposals": string_list(
                        option_value(section, "crypto_proposal", [])
                    ),
                }
            )
        elif item_type == "tunnel":
            tunnels.append(
                {
                    "id": section_name(section),
                    "local_subnets": string_list(
                        option_value(section, "local_subnet", [])
                    ),
                    "remote_subnets": string_list(
                        option_value(section, "remote_subnet", [])
                    ),
                    "startaction": str(option_value(section, "startaction", "")),
                    "closeaction": str(option_value(section, "closeaction", "")),
                }
            )
        elif item_type == "crypto_proposal":
            proposals.append(
                {
                    "id": section_name(section),
                    "encryption_algorithm": str(
                        option_value(section, "encryption_algorithm", "")
                    ),
                    "hash_algorithm": str(
                        option_value(section, "hash_algorithm", "")
                    ),
                    "dh_group": str(option_value(section, "dh_group", "")),
                }
            )
    return {
        "configured": bool(remotes or tunnels or proposals),
        "enabled_connection_count": len(
            [remote for remote in remotes if remote.get("enabled")]
        ),
        "remote_count": len(remotes),
        "tunnel_count": len(tunnels),
        "authentication_methods": sorted(
            {
                method
                for method in (
                    str(remote.get("authentication_method", "")) for remote in remotes
                )
                if method
            }
        ),
        "connections": remotes,
        "proposals": proposals,
        "swanctl": _swanctl_inventory(raw_snapshot),
    }


def analyze(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    openvpn_instances = _openvpn_instances(raw_snapshot)
    wireguard_interfaces = _wireguard_inventory(raw_snapshot)
    ipsec_inventory = _ipsec_inventory(raw_snapshot)
    inventory = {
        "openvpn": openvpn_instances,
        "wireguard": wireguard_interfaces,
        "ipsec": ipsec_inventory,
        "enabled_openvpn_count": len(
            [instance for instance in openvpn_instances if instance.get("enabled")]
        ),
        "wireguard_interface_count": len(wireguard_interfaces),
        "enabled_ipsec_count": int(ipsec_inventory.get("enabled_connection_count", 0)),
    }
    findings = []

    for instance in openvpn_instances:
        if instance.get("unredacted_secret_detected"):
            findings.append(
                build_finding(
                    f"vpn-openvpn-unredacted-secret-{instance['id']}",
                    "OpenVPN analyzer input contains unredacted secret material",
                    "critical",
                    AREA,
                    "openvpn",
                    "The sanitized snapshot still appears to contain OpenVPN secret material.",
                    {"instance": instance.get("id")},
                    "Fix collection redaction rules and regenerate the sanitized snapshot before sharing report artifacts.",
                    nist=("AU-9", "IA-5", "SC-13"),
                    acn=("secure_communications", "risk_management"),
                )
            )
        if not instance.get("enabled"):
            continue
        tls_min = _tls_version_number(instance.get("tls_version_min"))
        if tls_min is None:
            findings.append(
                build_finding(
                    f"vpn-openvpn-no-tls-min-{instance['id']}",
                    "OpenVPN TLS minimum version is not explicit",
                    "medium",
                    AREA,
                    "openvpn",
                    "An enabled OpenVPN instance does not declare tls_version_min in the sanitized UCI data.",
                    {"instance": instance.get("id")},
                    "Set tls-version-min to 1.2 or higher, preferably 1.3 where compatible.",
                    nist=("SC-8", "SC-13", "CM-6"),
                    acn=("secure_communications", "risk_management"),
                )
            )
        elif tls_min < 1.2:
            findings.append(
                build_finding(
                    f"vpn-openvpn-old-tls-{instance['id']}",
                    "OpenVPN permits deprecated TLS versions",
                    "high",
                    AREA,
                    "openvpn",
                    "An enabled OpenVPN instance allows TLS versions older than 1.2.",
                    {
                        "instance": instance.get("id"),
                        "tls_version_min": instance.get("tls_version_min"),
                    },
                    "Raise tls-version-min to 1.2 or newer and test client compatibility.",
                    nist=("SC-8", "SC-13"),
                    acn=("secure_communications",),
                )
            )
        if instance.get("weak_cipher_values"):
            findings.append(
                build_finding(
                    f"vpn-openvpn-weak-cipher-{instance['id']}",
                    "OpenVPN uses weak or legacy cipher settings",
                    "high",
                    AREA,
                    "openvpn",
                    "Weak OpenVPN cipher tokens were found in enabled instance settings.",
                    {
                        "instance": instance.get("id"),
                        "weak_cipher_values": instance.get("weak_cipher_values"),
                    },
                    "Use AEAD ciphers such as AES-256-GCM, AES-128-GCM, or CHACHA20-POLY1305.",
                    nist=("SC-8", "SC-13", "CM-6"),
                    acn=("secure_communications", "risk_management"),
                )
            )
        if any(token in instance.get("auth_digest", "") for token in WEAK_AUTH_TOKENS):
            findings.append(
                build_finding(
                    f"vpn-openvpn-weak-auth-{instance['id']}",
                    "OpenVPN uses weak digest authentication",
                    "medium",
                    AREA,
                    "openvpn",
                    "The OpenVPN auth directive references a deprecated digest algorithm.",
                    {
                        "instance": instance.get("id"),
                        "auth_digest": instance.get("auth_digest"),
                    },
                    "Use SHA256 or stronger digest settings where an auth directive is still required.",
                    nist=("SC-8", "SC-13"),
                    acn=("secure_communications",),
                )
            )
        if instance.get("compression_enabled"):
            findings.append(
                build_finding(
                    f"vpn-openvpn-compression-{instance['id']}",
                    "OpenVPN compression is enabled",
                    "medium",
                    AREA,
                    "openvpn",
                    "VPN compression can expose traffic to compression oracle attacks and is discouraged.",
                    {"instance": instance.get("id")},
                    "Disable comp-lzo/compress/allow-compression unless a documented exception is approved.",
                    nist=("SC-8", "SC-13", "CM-6"),
                    acn=("secure_communications", "risk_management"),
                )
            )
        if instance.get("duplicate_cn"):
            findings.append(
                build_finding(
                    f"vpn-openvpn-duplicate-cn-{instance['id']}",
                    "OpenVPN duplicate certificate common names are allowed",
                    "high",
                    AREA,
                    "openvpn",
                    "duplicate-cn weakens user/device accountability for remote access sessions.",
                    {"instance": instance.get("id")},
                    "Disable duplicate-cn and issue unique certificates per user or device.",
                    nist=("AC-2", "IA-2", "IA-5", "AC-17"),
                    acn=("identity_access_governance", "secure_communications"),
                )
            )
        if instance.get("client_to_client"):
            findings.append(
                build_finding(
                    f"vpn-openvpn-client-to-client-{instance['id']}",
                    "OpenVPN clients can communicate directly with each other",
                    "medium",
                    AREA,
                    "openvpn",
                    "client-to-client allows lateral traffic between VPN clients.",
                    {"instance": instance.get("id")},
                    "Disable client-to-client unless required and enforce segmentation with firewall rules.",
                    nist=("AC-4", "SC-7", "CM-7"),
                    acn=("network_segmentation", "secure_communications"),
                )
            )
        if instance.get("user_password_auth") and not (
            instance.get("mfa_indicator")
            or contains_indicator(raw_snapshot, MFA_INDICATORS)
        ):
            findings.append(
                build_finding(
                    f"vpn-openvpn-mfa-missing-{instance['id']}",
                    "OpenVPN user authentication lacks an MFA indicator",
                    "medium",
                    AREA,
                    "openvpn",
                    "The enabled OpenVPN instance appears to use user/password authentication without MFA evidence.",
                    {"instance": instance.get("id")},
                    "Enable OTP/MFA for VPN users or document an equivalent compensating control.",
                    nist=("IA-2", "IA-5", "AC-17"),
                    acn=("identity_access_governance", "secure_communications"),
                )
            )

    for interface in wireguard_interfaces:
        if interface.get("unredacted_secret_detected"):
            findings.append(
                build_finding(
                    f"vpn-wireguard-unredacted-secret-{interface['id']}",
                    "WireGuard analyzer input contains unredacted key material",
                    "critical",
                    AREA,
                    "wireguard",
                    "The sanitized snapshot still appears to contain WireGuard private key material.",
                    {"interface": interface.get("id")},
                    "Fix collection redaction rules and regenerate the sanitized snapshot before sharing report artifacts.",
                    nist=("AU-9", "IA-5", "SC-13"),
                    acn=("secure_communications", "risk_management"),
                )
            )
        if not interface.get("private_key_present"):
            findings.append(
                build_finding(
                    f"vpn-wireguard-missing-private-key-{interface['id']}",
                    "WireGuard interface has no private key indicator",
                    "high",
                    AREA,
                    "wireguard",
                    "A WireGuard interface was found without a private key presence indicator in the sanitized snapshot.",
                    {"interface": interface.get("id")},
                    "Verify the interface configuration; the collector should record presence while redacting the key value.",
                    nist=("CM-6", "SC-13"),
                    acn=("secure_communications", "risk_management"),
                )
            )
        for peer in interface.get("peers", []):
            if peer.get("unredacted_secret_detected"):
                findings.append(
                    build_finding(
                        f"vpn-wireguard-peer-unredacted-secret-{interface['id']}-{peer.get('id')}",
                        "WireGuard peer input contains unredacted preshared key material",
                        "critical",
                        AREA,
                        "wireguard_peer",
                        "The sanitized snapshot still appears to contain WireGuard peer secret material.",
                        {"interface": interface.get("id"), "peer": peer.get("id")},
                        "Fix collection redaction rules and regenerate the sanitized snapshot before sharing report artifacts.",
                        nist=("AU-9", "IA-5", "SC-13"),
                        acn=("secure_communications", "risk_management"),
                    )
                )
            if not peer.get("preshared_key_present"):
                findings.append(
                    build_finding(
                        f"vpn-wireguard-peer-no-psk-{interface['id']}-{peer.get('id')}",
                        "WireGuard peer has no preshared key indicator",
                        "low",
                        AREA,
                        "wireguard_peer",
                        "WireGuard works without PSKs, but PSKs provide additional protection if static keys are exposed later.",
                        {"interface": interface.get("id"), "peer": peer.get("id")},
                        "Consider enabling per-peer preshared keys and rotate them periodically.",
                        nist=("IA-5", "SC-13"),
                        acn=("secure_communications", "risk_management"),
                    )
                )
            allowed = set(peer.get("allowed_ips", []))
            if allowed & FULL_TUNNEL_ALLOWED_IPS:
                findings.append(
                    build_finding(
                        f"vpn-wireguard-peer-full-tunnel-{interface['id']}-{peer.get('id')}",
                        "WireGuard peer is allowed a full-tunnel route",
                        "medium",
                        AREA,
                        "wireguard_peer",
                        "A peer allowed_ips entry permits 0.0.0.0/0 or ::/0, which can expand remote access scope.",
                        {
                            "interface": interface.get("id"),
                            "peer": peer.get("id"),
                            "allowed_ips": peer.get("allowed_ips"),
                        },
                        "Confirm full-tunnel access is required; otherwise restrict allowed_ips to specific networks.",
                        nist=("AC-4", "AC-17", "SC-7"),
                        acn=("network_segmentation", "secure_communications"),
                    )
                )
            age = peer.get("latest_handshake_age_seconds")
            if isinstance(age, int) and age > STALE_HANDSHAKE_SECONDS:
                findings.append(
                    build_finding(
                        f"vpn-wireguard-stale-peer-{interface['id']}-{peer.get('id')}",
                        "WireGuard peer handshake is stale",
                        "low",
                        AREA,
                        "wireguard_peer",
                        "A configured peer has not completed a handshake within the expected audit window.",
                        {
                            "interface": interface.get("id"),
                            "peer": peer.get("id"),
                            "age_seconds": age,
                        },
                        "Review whether the peer is still needed and remove or disable unused remote access entries.",
                        nist=("AC-2", "AC-17", "CM-7"),
                        acn=("identity_access_governance", "risk_management"),
                    )
                )

    return build_result(AREA, inventory, findings)


analyze_vpn = analyze
