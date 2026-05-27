#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""Firmware version currency and TLS certificate analyzer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

try:
    from ..models import (
        build_finding,
        build_result,
        option_value,
        string_list,
        uci_sections,
    )
except ImportError:  # pragma: no cover - supports direct execution during development
    from ns_audit.models import (
        build_finding,
        build_result,
        option_value,
        string_list,
        uci_sections,
    )

AREA = "updates"

_ACME_DIRS = ("/etc/acme", "/etc/ssl/acme", "/etc/ssl/certs")


def _update_info(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    security_checks = raw_snapshot.get("security_checks") or {}
    return dict(security_checks.get("update") or {})


def _certificate_info(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Check for Let's Encrypt (acme) or uploaded TLS certificates."""
    # Check ACME UCI config
    acme_sections = uci_sections(raw_snapshot, "acme")
    has_acme_config = bool(acme_sections)
    has_acme_cert = False
    domains: list[str] = []
    for section in acme_sections:
        enabled = str(option_value(section, ("enabled", "enable"), "0")).strip()
        if enabled == "1":
            has_acme_cert = True
        domains.extend(string_list(option_value(section, ("domains", "domain"), [])))

    # Check for certificate files in known paths via collected files dict
    files = raw_snapshot.get("files") or {}
    cert_paths = [
        p for p in files if any(
            str(p).startswith(prefix) for prefix in _ACME_DIRS
        ) and str(p).endswith((".crt", ".pem", ".cer", ".fullchain"))
    ]
    if cert_paths:
        has_acme_cert = True

    return {
        "acme_config_present": has_acme_config,
        "acme_cert_active": has_acme_cert,
        "domains": domains,
        "cert_file_evidence": cert_paths,
    }


def _subscription_info(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    security_checks = raw_snapshot.get("security_checks") or {}
    return dict(security_checks.get("subscription") or {})


def _automatic_update_info(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    security_checks = raw_snapshot.get("security_checks") or {}
    return dict(security_checks.get("automatic_updates") or {})


def _ha_status(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    for section in uci_sections(raw_snapshot, "keepalived"):
        name = str(section.get(".name", "") or section.get("name", "")).strip()
        if name == "globals":
            enabled = str(option_value(section, "enabled", "0")).strip()
            return {"configured": True, "enabled": enabled == "1"}
    return {"configured": False, "enabled": False}


def analyze(raw_snapshot: Mapping[str, Any]) -> dict[str, Any]:
    update = _update_info(raw_snapshot)
    automatic_updates = _automatic_update_info(raw_snapshot)
    cert = _certificate_info(raw_snapshot)
    subscription = _subscription_info(raw_snapshot)
    ha = _ha_status(raw_snapshot)
    update_inventory = {
        "version_check_completed": bool(update.get("checked")),
        "up_to_date": update.get("up_to_date"),
        "local_version": update.get("local_version"),
        "latest_version": update.get("latest_version"),
        "automatic_updates_checked": bool(automatic_updates.get("checked")),
        "automatic_updates_enabled": automatic_updates.get("enabled"),
    }
    if update.get("error"):
        update_inventory["version_check_error"] = update.get("error")
    if automatic_updates.get("error"):
        update_inventory["automatic_updates_error"] = automatic_updates.get("error")

    inventory = {
        "update": update_inventory,
        "ha": ha,
        "subscription": subscription,
        "certificate": cert,
    }
    findings = []

    # Version currency check
    if not update.get("checked"):
        error = update.get("error", "unknown")
        findings.append(
            build_finding(
                "updates-version-check-failed",
                "Firmware version currency check could not be completed",
                "info",
                AREA,
                "firmware",
                f"The audit tool could not reach the NethSecurity update server to verify version currency. Error: {error}",
                {"error": error},
                "Verify internet connectivity and re-run the audit to check if the firmware is up to date.",
                nist=("CM-6", "RA-5", "SI-2"),
                acn=("risk_management",),
            )
        )
    elif update.get("up_to_date") is False:
        local = update.get("local_version", "unknown")
        latest = update.get("latest_version", "unknown")
        findings.append(
            build_finding(
                "updates-firmware-outdated",
                "Firmware is not up to date",
                "high",
                AREA,
                "firmware",
                f"The installed firmware version ({local}) is older than the latest stable release ({latest}). "
                "Outdated firmware may contain known security vulnerabilities.",
                {"local_version": local, "latest_version": latest},
                f"Update the firmware to version {latest} or later via the NethSecurity UI or CLI.",
                nist=("CM-6", "RA-5", "SI-2"),
                acn=("risk_management",),
            )
        )

    # TLS certificate check (advisory/positive)
    if not cert.get("acme_cert_active") and not cert.get("cert_file_evidence"):
        findings.append(
            build_finding(
                "updates-no-tls-cert",
                "No Let's Encrypt or uploaded TLS certificate detected",
                "info",
                AREA,
                "certificate",
                "No ACME/Let's Encrypt configuration or certificate file was found. "
                "The web UI may be using a self-signed certificate, which triggers browser warnings and reduces trust.",
                {},
                "Request a Let's Encrypt certificate via the NethSecurity UI (System > Certificates) "
                "or upload a valid TLS certificate for the admin interface.",
                nist=("SC-8", "SC-13", "IA-5"),
                acn=("secure_communications", "risk_management"),
            )
        )

    if subscription.get("available") and not subscription.get("active"):
        findings.append(
            build_finding(
                "updates-no-subscription",
                "No active NethSecurity subscription detected",
                "info",
                AREA,
                "subscription",
                "A NethSecurity subscription provides access to commercial threat feeds, enterprise support, "
                "and automated security updates. No active subscription was found.",
                {},
                "Consider activating a NethSecurity subscription for commercial support and threat intelligence.",
                nist=("SI-2", "SI-3", "RA-5"),
                acn=("risk_management",),
            )
        )

    return build_result(AREA, inventory, findings)


analyze_updates = analyze
