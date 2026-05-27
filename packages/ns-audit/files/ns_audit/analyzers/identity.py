#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""Identity, account, and administrative access analyzer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from ..models import (
        build_finding,
        build_result,
        command_json,
        contains_indicator,
        get_file,
        is_enabled_section,
        json_safe,
        option_value,
        parse_group,
        parse_passwd,
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
        get_file,
        is_enabled_section,
        json_safe,
        option_value,
        parse_group,
        parse_passwd,
        section_name,
        section_type,
        string_list,
        to_bool,
        uci_sections,
    )

AREA = "identity"
NON_INTERACTIVE_SHELLS = {"/bin/false", "/sbin/nologin", "/usr/sbin/nologin", "nologin"}
MFA_INDICATORS = ("totp", "otp", "mfa", "2fa", "two_factor", "two-factor", "webauthn")


def _platform(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    board = command_json(
        raw_snapshot, ("ubus call system board", "system board", "board")
    )
    info = command_json(raw_snapshot, ("ubus call system info", "system info"))
    system = (
        raw_snapshot.get("system")
        if isinstance(raw_snapshot.get("system"), Mapping)
        else {}
    )
    if not board and isinstance(system, Mapping):
        board = system.get("board") or {}
    if not info and isinstance(system, Mapping):
        info = system.get("info") or {}
    return json_safe(
        {
            "hostname": (board or {}).get("hostname") or (system or {}).get("hostname"),
            "model": (board or {}).get("model"),
            "board_name": (board or {}).get("board_name"),
            "release": (board or {}).get("release"),
            "kernel": (board or {}).get("kernel"),
            "uptime": (info or {}).get("uptime"),
            "local_time": (info or {}).get("localtime"),
        }
    )


def _accounts(raw_snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    accounts = parse_passwd(get_file(raw_snapshot, "/etc/passwd"))
    raw_accounts = raw_snapshot.get("accounts")
    if not accounts and isinstance(raw_accounts, list):
        accounts = [
            dict(account) for account in raw_accounts if isinstance(account, Mapping)
        ]
    groups = parse_group(get_file(raw_snapshot, "/etc/group"))
    groups_by_gid = {str(group.get("gid")): name for name, group in groups.items()}
    memberships: dict[str, list[str]] = {
        account.get("username", ""): [] for account in accounts
    }
    for group_name, group in groups.items():
        for member in group.get("members", []):
            memberships.setdefault(member, []).append(group_name)
    normalized = []
    for account in accounts:
        username = str(account.get("username", ""))
        primary_group = groups_by_gid.get(str(account.get("gid")))
        account_groups = sorted(
            set(
                ([primary_group] if primary_group else [])
                + memberships.get(username, [])
            )
        )
        normalized.append(
            {
                "username": username,
                "uid": account.get("uid"),
                "gid": account.get("gid"),
                "groups": account_groups,
                "home": account.get("home"),
                "shell": account.get("shell"),
                "interactive_shell": account.get(
                    "interactive_shell",
                    account.get("shell") not in NON_INTERACTIVE_SHELLS,
                ),
                "is_superuser": account.get("uid") == 0,
            }
        )
    return json_safe(normalized)


def _dropbear(raw_snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    instances = []
    for index, section in enumerate(uci_sections(raw_snapshot, "dropbear")):
        if section_type(section) and section_type(section) != "dropbear":
            continue
        password_auth = to_bool(
            option_value(section, ("PasswordAuth", "password_auth"), "on"), default=True
        )
        root_password_auth = to_bool(
            option_value(section, ("RootPasswordAuth", "root_password_auth"), "on"),
            default=True,
        )
        interface = string_list(option_value(section, ("Interface", "interface"), []))
        ports = string_list(option_value(section, ("Port", "port"), "22"))
        instances.append(
            {
                "id": section_name(section) or f"dropbear-{index}",
                "enabled": is_enabled_section(section, default=True),
                "ports": ports or ["22"],
                "interfaces": interface,
                "password_auth": password_auth,
                "root_password_auth": root_password_auth,
                "gateway_ports": to_bool(
                    option_value(section, ("GatewayPorts", "gateway_ports")),
                    default=False,
                ),
            }
        )
    return json_safe(instances)


def _configured_admins(raw_snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    sections = uci_sections(raw_snapshot, "users") + uci_sections(raw_snapshot, "rpcd")
    admins = []
    for section in sections:
        safe_section = {}
        for key, value in section.items():
            if any(
                token in str(key).lower()
                for token in ("password", "passwd", "secret", "token", "hash")
            ):
                safe_section[f"{key}_present"] = bool(value)
            elif str(key).startswith(".") or key in {
                "username",
                "user",
                "name",
                "role",
                "roles",
                "groups",
                "acl",
            }:
                safe_section[str(key)] = value
        admins.append(safe_section)
    return json_safe(admins)


def _non_root_rpcd_admins(raw_snapshot: Mapping[str, Any]) -> list[str]:
    """Return usernames of non-root, non-controller RPCD login entries."""
    result = []
    for section in uci_sections(raw_snapshot, "rpcd"):
        if section_type(section) != "login":
            continue
        username = str(option_value(section, "username", "") or "").strip()
        if username and username not in {"root", ""}:
            result.append(username)
    return result


def analyze(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Return identity inventory, findings, summary, and compliance placeholders."""
    accounts = _accounts(raw_snapshot)
    dropbear = _dropbear(raw_snapshot)
    configured_admins = _configured_admins(raw_snapshot)
    non_root_admins = _non_root_rpcd_admins(raw_snapshot)
    mfa_detected = contains_indicator(
        {"users": configured_admins, "raw": raw_snapshot.get("mfa")}, MFA_INDICATORS
    ) or contains_indicator(raw_snapshot.get("authentication", {}), MFA_INDICATORS)

    # Default password check (result stored as boolean only — no hash persisted)
    security_checks = raw_snapshot.get("security_checks") or {}
    default_pw_check = security_checks.get("default_pw_check") or {}
    default_password_detected = bool(default_pw_check.get("is_default"))
    default_password_checked = bool(default_pw_check.get("checked"))

    inventory = {
        "platform": _platform(raw_snapshot),
        "local_accounts": accounts,
        "configured_admins": configured_admins,
        "non_root_admins": non_root_admins,
        "dropbear": dropbear,
        "mfa_detected": mfa_detected,
        "default_password_detected": default_password_detected,
        "default_password_checked": default_password_checked,
    }
    findings = []

    uid0_accounts = [account for account in accounts if account.get("uid") == 0]
    extra_uid0 = [
        account for account in uid0_accounts if account.get("username") != "root"
    ]
    if extra_uid0:
        findings.append(
            build_finding(
                "identity-extra-uid0-accounts",
                "Additional UID 0 accounts detected",
                "critical",
                AREA,
                "local_accounts",
                "Accounts other than root have UID 0 and therefore full administrative privileges.",
                {"accounts": [account.get("username") for account in extra_uid0]},
                "Remove unnecessary UID 0 accounts or assign them unique non-privileged UIDs with explicit sudo/role access.",
                nist=("AC-2", "AC-6", "IA-2"),
                acn=("identity_access_governance", "risk_management"),
            )
        )

    interactive_root = [
        account for account in uid0_accounts if account.get("interactive_shell")
    ]
    if interactive_root and not non_root_admins:
        findings.append(
            build_finding(
                "identity-root-only-administration",
                "Only the root account is used for administration",
                "medium",
                AREA,
                "local_accounts",
                "No named administrative users were found in RPCD login configuration. "
                "Creating dedicated admin accounts follows the principle of least privilege and improves accountability.",
                {"root_shells": [account.get("shell") for account in interactive_root]},
                "Create named administrator accounts with least-privilege roles and keep root access for emergency use only.",
                nist=("AC-2", "AC-6", "IA-2"),
                acn=("identity_access_governance",),
            )
        )

    # Default password check
    if default_password_detected:
        findings.append(
            build_finding(
                "identity-default-password",
                "Root account uses the factory-default password",
                "critical",
                AREA,
                "local_accounts",
                "The root account password matches the factory default (Nethesis,1234). "
                "This is a critical credential risk and must be changed immediately.",
                {"default_password_checked": default_password_checked},
                "Change the root password to a strong, unique passphrase immediately.",
                nist=("IA-5", "AC-2", "AC-6"),
                acn=("identity_access_governance", "risk_management"),
            )
        )

    for instance in dropbear:
        if not instance.get("enabled", True):
            continue
        if instance.get("password_auth"):
            findings.append(
                build_finding(
                    f"identity-dropbear-password-auth-{instance['id']}",
                    "SSH password authentication is enabled",
                    "high",
                    AREA,
                    "dropbear",
                    "Password-based SSH access increases exposure to brute-force and credential reuse attacks.",
                    {
                        "instance": instance["id"],
                        "ports": instance.get("ports"),
                        "interfaces": instance.get("interfaces"),
                    },
                    "Disable SSH password authentication and require public-key or centrally governed administrative access.",
                    nist=("IA-2", "IA-5", "AC-17"),
                    acn=("identity_access_governance", "secure_communications"),
                )
            )
        if instance.get("root_password_auth"):
            findings.append(
                build_finding(
                    f"identity-dropbear-root-password-{instance['id']}",
                    "Root SSH password login is enabled",
                    "high",
                    AREA,
                    "dropbear",
                    "Root password login exposes the most privileged account directly on SSH.",
                    {"instance": instance["id"], "ports": instance.get("ports")},
                    "Set RootPasswordAuth to off and use named administrators with key-based authentication.",
                    nist=("AC-2", "AC-6", "IA-2", "IA-5"),
                    acn=("identity_access_governance",),
                )
            )
        if not instance.get("interfaces") or any(
            str(item).lower() in {"wan", "*", "0.0.0.0"}
            for item in instance.get("interfaces", [])
        ):
            findings.append(
                build_finding(
                    f"identity-dropbear-broad-listener-{instance['id']}",
                    "SSH listener is not restricted to a management interface",
                    "medium",
                    AREA,
                    "dropbear",
                    "The Dropbear listener has no explicit management interface restriction in UCI.",
                    {
                        "instance": instance["id"],
                        "interfaces": instance.get("interfaces"),
                    },
                    "Bind SSH to a trusted management interface and enforce firewall rules that block WAN access.",
                    nist=("AC-17", "CM-7", "SC-7"),
                    acn=("identity_access_governance", "network_segmentation"),
                )
            )

    if not mfa_detected:
        findings.append(
            build_finding(
                "identity-mfa-not-detected",
                "Multi-factor authentication indicator not detected",
                "medium",
                AREA,
                "administrative_access",
                "The sanitized snapshot does not show OTP, TOTP, MFA, or WebAuthn indicators for administrative access.",
                {"configured_admins": len(configured_admins)},
                "Enable MFA for administrator logins where supported and document compensating controls for emergency accounts.",
                nist=("IA-2", "IA-5"),
                acn=("identity_access_governance", "risk_management"),
            )
        )

    return build_result(AREA, inventory, findings)


analyze_identity = analyze
