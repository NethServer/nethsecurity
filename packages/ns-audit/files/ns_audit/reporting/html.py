#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""Render sanitized NethSecurity audit JSON artifacts as an HTML report."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tarfile
from datetime import datetime, timezone
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ns_audit.config import REPORT_BUNDLE_NAME

DEFAULT_TEMPLATE_NAME = "audit-report.html.j2"
DEFAULT_CSS_NAME = "audit-report.css"
DEFAULT_OUTPUT_NAME = "audit-report.html"
DEFAULT_BUNDLE_NAME = REPORT_BUNDLE_NAME
EXPECTED_JSON_ARTIFACTS = (
    "raw_snapshot.json",
    "inventory.json",
    "findings.json",
    "compliance_mapping.json",
    "summary.json",
)
SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
    "informational": 4,
}
SECRET_PATTERNS = {
    "private_key_block": re.compile(
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", re.IGNORECASE
    ),
    "openvpn_static_key": re.compile(
        r"-----BEGIN OpenVPN Static key V1-----", re.IGNORECASE
    ),
    "password_hash": re.compile(r"\$(?:1|2a|2b|2y|5|6|y|gy)\$[A-Za-z0-9./$]{20,}"),
    "wireguard_private_key": re.compile(
        r"\bprivate[_-]?key\b\s*[:=]\s*(?!\[?redacted\]?)[\"']?[A-Za-z0-9+/=]{32,}",
        re.IGNORECASE,
    ),
    "wireguard_preshared_key": re.compile(
        r"\bpreshared[_-]?key\b\s*[:=]\s*(?!\[?redacted\]?)[\"']?[A-Za-z0-9+/=]{32,}",
        re.IGNORECASE,
    ),
    "api_token": re.compile(
        r"\b(api[_-]?token|secret[_-]?token)\b\s*[:=]\s*(?!\[?redacted\]?)[\"']?[A-Za-z0-9._-]{24,}",
        re.IGNORECASE,
    ),
}


class ReportRenderingError(RuntimeError):
    """Raised when sanitized report artifacts cannot be rendered safely."""


def load_json_artifact(path: str | Path, default: Any | None = None) -> Any:
    """Load a JSON artifact or return the provided default when it is missing."""
    artifact_path = Path(path)
    if not artifact_path.exists():
        return {} if default is None else default
    with artifact_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_report_context(
    input_dir: str | Path,
    asset_dir: str | Path | None = None,
    log_artifacts: list[dict[str, Any]] | None = None,
    config_files: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a template context from sanitized JSON artifacts in input_dir."""
    report_dir = Path(input_dir)
    assets = (
        Path(asset_dir) if asset_dir else Path(__file__).resolve().parent / "assets"
    )
    raw_snapshot = load_json_artifact(report_dir / "raw_snapshot.json", {})
    summary = load_json_artifact(report_dir / "summary.json", {})
    inventory = load_json_artifact(report_dir / "inventory.json", {})
    findings_artifact = load_json_artifact(report_dir / "findings.json", {})
    compliance_artifact = load_json_artifact(report_dir / "compliance_mapping.json", {})
    findings = normalize_findings(findings_artifact)
    source_artifacts = describe_source_artifacts(report_dir)
    log_entries = (
        log_artifacts
        if log_artifacts is not None
        else sanitize_log_artifacts(build_log_artifacts(raw_snapshot))
    )
    api_audit = normalize_api_audit(inventory)
    cfg_files = config_files if config_files is not None else build_config_files(raw_snapshot)

    return {
        "generated_at": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "summary": normalize_summary(summary, findings),
        "hostname": _extract_hostname(inventory),
        "subscription": _extract_subscription(raw_snapshot),
        "ha_enabled": _extract_ha(raw_snapshot),
        "inventory_sections": normalize_inventory_sections(inventory),
        "api_audit": api_audit,
        "auth_events": build_auth_events(raw_snapshot),
        "config_changes": api_audit.get("config_changes", []),
        "config_files": cfg_files,
        "log_artifacts": log_entries,
        "findings": findings,
        "compliance_mappings": normalize_compliance_mappings(compliance_artifact),
        "remediation_plan": build_remediation_plan(findings),
        "source_artifacts": source_artifacts,
        "snapshot_hash": source_artifacts.get("raw_snapshot.json", {}).get("sha256"),
        "stylesheet": read_text(assets / DEFAULT_CSS_NAME),
    }


def _extract_hostname(inventory: Any) -> str:
    if not isinstance(inventory, dict):
        return ""
    identity = inventory.get("identity") or {}
    if not isinstance(identity, dict):
        return ""
    platform = identity.get("platform") or {}
    if not isinstance(platform, dict):
        return ""
    return str(platform.get("hostname", "") or "").strip()


def _extract_subscription(raw_snapshot: Any) -> dict[str, Any]:
    if not isinstance(raw_snapshot, dict):
        return {}
    security_checks = raw_snapshot.get("security_checks") or {}
    if not isinstance(security_checks, dict):
        return {}
    return dict(security_checks.get("subscription") or {})


def _extract_ha(raw_snapshot: Any) -> bool:
    if not isinstance(raw_snapshot, dict):
        return False
    uci = raw_snapshot.get("uci") or {}
    if not isinstance(uci, dict):
        return False
    keepalived = uci.get("keepalived") or {}
    sections = keepalived if isinstance(keepalived, list) else []
    if not sections and isinstance(keepalived, dict):
        sections = list(keepalived.values())
    for section in sections:
        if not isinstance(section, dict):
            continue
        name = str(section.get(".name", "") or section.get("name", "")).strip()
        if name == "globals":
            return str(section.get("enabled", "0")).strip() == "1"
    return False


def render_report(
    input_dir: str | Path,
    output_path: str | Path | None = None,
    template_dir: str | Path | None = None,
    asset_dir: str | Path | None = None,
    validate: bool = True,
) -> Path:
    """Render audit-report.html from sanitized JSON artifacts."""
    report_dir = Path(input_dir)
    destination = Path(output_path) if output_path else report_dir / DEFAULT_OUTPUT_NAME
    output_dir = destination.parent
    templates = (
        Path(template_dir)
        if template_dir
        else Path(__file__).resolve().parent / "templates"
    )
    raw_snapshot = load_json_artifact(report_dir / "raw_snapshot.json", {})
    log_artifacts = build_log_artifacts(raw_snapshot)
    materialize_log_artifacts(output_dir, log_artifacts)
    config_files = build_config_files(raw_snapshot)
    materialize_config_files(output_dir, config_files)
    context = build_report_context(
        report_dir, asset_dir, sanitize_log_artifacts(log_artifacts),
        sanitize_config_files(config_files),
    )

    env = Environment(
        loader=FileSystemLoader(str(templates)),
        autoescape=select_autoescape(("html", "xml", "j2")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["humanize"] = humanize
    env.filters["json_pretty"] = json_pretty
    env.filters["severity_class"] = severity_class
    env.filters["status_class"] = status_class
    env.filters["format_value"] = format_value

    html = env.get_template(DEFAULT_TEMPLATE_NAME).render(**context)
    if validate:
        matches = find_secret_pattern_matches_in_text(html)
        if matches:
            raise ReportRenderingError(
                f"refusing to write report with possible secret content: {matches}"
            )

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, encoding="utf-8")
    return destination


def describe_source_artifacts(report_dir: Path) -> dict[str, dict[str, Any]]:
    """Return existence, size, and SHA-256 metadata for expected JSON artifacts."""
    artifacts: dict[str, dict[str, Any]] = {}
    for name in EXPECTED_JSON_ARTIFACTS:
        path = report_dir / name
        exists = path.exists()
        artifacts[name] = {
            "exists": exists,
            "size": path.stat().st_size if exists else 0,
            "sha256": sha256sum(path) if exists else None,
        }
    return artifacts


def normalize_summary(summary: Any, findings: list[dict[str, Any]]) -> dict[str, Any]:
    data = summary if isinstance(summary, dict) else {}
    counts = severity_counts(findings)
    summary_counts = {}
    for count_key in ("severity_counts", "finding_counts", "findings_by_severity"):
        if isinstance(data.get(count_key), dict):
            summary_counts = data[count_key]
            break
    for severity, count in summary_counts.items():
        counts[str(severity).lower()] = int(count or 0)

    score = first_present(
        data,
        ("score", "overall_score", "security_score", "compliance_score"),
        default=None,
    )
    if score is None and isinstance(data.get("summary"), dict):
        score = first_present(
            data["summary"], ("score", "overall_score", "security_score"), default=None
        )

    return {
        "title": data.get("title", "NethSecurity Audit Report"),
        "appliance": first_present(
            data,
            ("appliance", "hostname", "device", "system"),
            default="NethSecurity appliance",
        ),
        "run_id": first_present(
            data, ("run_id", "id", "audit_id"), default="not available"
        ),
        "score": score if score is not None else derive_score(counts),
        "status": first_present(
            data, ("status", "overall_status"), default=derive_status(counts)
        ),
        "finding_count": first_present(
            data,
            ("finding_count", "total_findings"),
            default=sum(counts.values()) if summary_counts else len(findings),
        ),
        "severity_counts": counts,
        "areas": normalize_area_scores(
            first_present(data, ("areas", "area_scores", "scores"), default={})
        ),
        "highlights": normalize_text_list(
            first_present(
                data, ("highlights", "executive_summary", "summary"), default=[]
            ),
        ),
    }


def normalize_findings(findings_artifact: Any) -> list[dict[str, Any]]:
    raw_findings = extract_sequence(findings_artifact, ("findings", "items", "results"))
    normalized = []
    for index, raw in enumerate(raw_findings, start=1):
        if not isinstance(raw, dict):
            raw = {"description": raw}
        severity = str(
            first_present(raw, ("severity", "level", "risk"), default="info")
        ).lower()
        normalized.append(
            {
                "id": first_present(
                    raw, ("id", "code", "finding_id"), default=f"finding-{index}"
                ),
                "title": first_present(
                    raw, ("title", "name", "summary"), default=f"Finding {index}"
                ),
                "severity": severity,
                "component": first_present(
                    raw, ("component", "area", "category", "scope"), default="General"
                ),
                "description": first_present(
                    raw,
                    ("description", "message", "details"),
                    default="No description provided.",
                ),
                "impact": first_present(
                    raw, ("impact", "risk_description"), default=""
                ),
                "remediation": first_present(
                    raw, ("remediation", "recommendation", "fix", "action"), default=""
                ),
                "evidence": normalize_evidence(
                    first_present(
                        raw, ("evidence", "evidence_refs", "references"), default=[]
                    ),
                ),
                "compliance": normalize_compliance_refs(
                    first_present(
                        raw, ("compliance", "controls", "mapping"), default=[]
                    ),
                ),
                "status": first_present(raw, ("status", "state"), default="open"),
                "raw": raw,
            }
        )
    return sorted(
        normalized,
        key=lambda item: (SEVERITY_ORDER.get(item["severity"], 5), str(item["id"])),
    )


def normalize_inventory_sections(inventory: Any) -> list[dict[str, Any]]:
    if not isinstance(inventory, dict):
        return []

    sections = []
    section_items = (
        inventory.get("sections")
        if isinstance(inventory.get("sections"), list)
        else None
    )
    if section_items:
        for section in section_items:
            if isinstance(section, dict):
                rows = normalize_rows(section.get("rows", section.get("items", [])))
                sections.append(
                    {
                        "title": first_present(
                            section, ("title", "name", "id"), default="Inventory"
                        ),
                        "description": section.get("description", ""),
                        "columns": columns_for_rows(rows),
                        "rows": rows,
                    }
                )
        return sections

    for name, value in inventory.items():
        if name == "updates":
            sections.extend(_normalize_updates_inventory_sections(value))
            continue
        if name == "logging":
            sections.extend(_normalize_logging_inventory_sections(value))
            continue
        sections.append(_build_inventory_section(humanize(name), value))
    return sections


def _build_inventory_section(
    title: str, value: Any, description: str = ""
) -> dict[str, Any]:
    rows = normalize_rows(value)
    return {
        "title": title,
        "description": description,
        "columns": columns_for_rows(rows),
        "rows": rows,
    }


def _normalize_updates_inventory_sections(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        return [_build_inventory_section("Updates", value)]

    section_definitions = (
        (
            "update",
            "Updates",
            "Firmware currency and automatic update policy for the appliance.",
        ),
        (
            "ha",
            "High Availability",
            "High availability configuration and current enablement status.",
        ),
        (
            "subscription",
            "Subscription",
            "NethSecurity subscription status, plan, and related support coverage.",
        ),
        (
            "certificate",
            "TLS Certificate",
            "Certificate evidence for the administrator UI, including ACME/Let's Encrypt state.",
        ),
    )
    sections = []
    for key, title, description in section_definitions:
        if key in value:
            sections.append(
                _build_inventory_section(title, value.get(key), description)
            )
    return sections or [_build_inventory_section("Updates", value)]


def _normalize_logging_inventory_sections(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        return [_build_inventory_section("Logging", value)]

    overview_keys = {"assessment", "storage_status", "controller", "remote_targets"}
    overview = {key: value[key] for key in overview_keys if key in value}
    details = {key: item for key, item in value.items() if key not in overview_keys}
    sections = []
    if overview:
        sections.append(
            _build_inventory_section(
                "Logging posture",
                overview,
                "Local retention and remote forwarding posture for audit evidence.",
            )
        )
    if details:
        sections.append(
            _build_inventory_section(
                "Logging details",
                details,
                "Log files, rotation evidence, and storage-backed retention details.",
            )
        )
    return sections or [_build_inventory_section("Logging", value)]


def normalize_compliance_mappings(compliance_artifact: Any) -> list[dict[str, Any]]:
    mapping_keys = ("mappings", "controls", "items", "compliance_mapping")
    if isinstance(compliance_artifact, dict) and not any(
        key in compliance_artifact for key in mapping_keys
    ):
        raw_mappings = flatten_mapping_dict(compliance_artifact)
    else:
        raw_mappings = extract_sequence(compliance_artifact, mapping_keys)

    mappings = []
    for index, raw in enumerate(raw_mappings, start=1):
        if not isinstance(raw, dict):
            raw = {"control": raw}
        mappings.append(
            {
                "framework": first_present(
                    raw, ("framework", "standard"), default="Compliance"
                ),
                "control": first_present(
                    raw, ("control", "id", "code"), default=f"control-{index}"
                ),
                "title": first_present(
                    raw, ("title", "name", "description"), default=""
                ),
                "category": first_present(
                    raw, ("category", "domain", "area"), default=""
                ),
                "status": first_present(
                    raw, ("status", "state", "result"), default="not assessed"
                ),
                "findings": normalize_text_list(
                    first_present(raw, ("findings", "finding_ids", "gaps"), default=[])
                ),
                "evidence": normalize_evidence(
                    first_present(raw, ("evidence", "evidence_refs"), default=[])
                ),
            }
        )
    return mappings


def build_remediation_plan(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan = []
    for finding in findings:
        remediation = str(finding.get("remediation", "")).strip()
        if remediation:
            plan.append(
                {
                    "priority": len(plan) + 1,
                    "finding_id": finding["id"],
                    "title": finding["title"],
                    "severity": finding["severity"],
                    "component": finding["component"],
                    "remediation": remediation,
                    "compliance": finding["compliance"],
                }
            )
    return plan


def _normalize_log_text(content: str) -> tuple[str, bool]:
    lines = content.splitlines()
    truncated = bool(lines and lines[-1] == "<truncated>")
    if truncated:
        lines = lines[:-1]
    return "\n".join(lines), truncated


def _log_archive_path(source_path: str) -> str:
    if source_path == "logread":
        return "logs/logread.txt"
    normalized = source_path.lstrip("/")
    return f"logs/{normalized}.txt"


def build_log_artifacts(raw_snapshot: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_snapshot, Mapping):
        return []

    logs = raw_snapshot.get("logs")
    if not isinstance(logs, Mapping):
        return []

    # Use active_source to decide which log files to include (storage-aware).
    # If active_source is "storage", only /mnt/data files are included.
    # If active_source is "memory" (or not set), only /var/log files are included.
    # logread output is always included as a memory fallback when no files are present.
    active_source = str(logs.get("active_source", "memory"))

    candidates: list[dict[str, Any]] = []

    log_files = logs.get("files")
    if isinstance(log_files, Sequence) and not isinstance(
        log_files, (str, bytes, bytearray)
    ):
        for entry in log_files:
            if not isinstance(entry, Mapping):
                continue
            source_path = str(entry.get("path", "")).strip()
            content = entry.get("content")
            if not source_path or not isinstance(content, str) or not content.strip():
                continue
            normalized_content, truncated_marker = _normalize_log_text(content)
            if not normalized_content:
                continue
            candidates.append(
                {
                    "source_path": source_path,
                    "source_kind": active_source,
                    "content": normalized_content,
                    "truncated": bool(entry.get("truncated")) or truncated_marker,
                }
            )

    # Include logread only when no file-based logs were collected
    if not candidates:
        logread = logs.get("logread")
        if isinstance(logread, Mapping):
            stdout = logread.get("stdout")
            if isinstance(stdout, str) and stdout.strip():
                content, truncated_marker = _normalize_log_text(stdout)
                if content:
                    candidates.append(
                        {
                            "source_path": "logread",
                            "source_kind": "memory",
                            "content": content,
                            "truncated": bool(logread.get("truncated")) or truncated_marker,
                        }
                    )

    return [
        {
            "archive_path": _log_archive_path(c["source_path"]),
            "display_path": c["source_path"],
            "source_kind": c["source_kind"],
            "source_paths": [c["source_path"]],
            "size": len(c["content"].encode("utf-8")),
            "sha256": hashlib.sha256(c["content"].encode("utf-8")).hexdigest(),
            "truncated": c["truncated"],
            "content": c["content"],
        }
        for c in candidates
    ]


def sanitize_log_artifacts(
    log_artifacts: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    sanitized = []
    for artifact in log_artifacts:
        sanitized.append(
            {
                "archive_path": str(artifact.get("archive_path", "")),
                "display_path": str(artifact.get("display_path", "")),
                "source_kind": str(artifact.get("source_kind", "")),
                "source_paths": [
                    str(path) for path in artifact.get("source_paths", [])
                ],
                "size": int(artifact.get("size", 0) or 0),
                "sha256": str(artifact.get("sha256", "")),
                "truncated": bool(artifact.get("truncated")),
            }
        )
    return sanitized


def materialize_log_artifacts(
    report_dir: Path, log_artifacts: Sequence[Mapping[str, Any]]
) -> list[Path]:
    logs_dir = report_dir / "logs"
    if logs_dir.exists():
        shutil.rmtree(logs_dir)

    written = []
    for artifact in log_artifacts:
        archive_path = Path(str(artifact.get("archive_path", "")))
        content = artifact.get("content")
        if not archive_path.parts or not isinstance(content, str):
            continue
        destination = report_dir / archive_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        written.append(destination)
    return written


def build_config_files(raw_snapshot: Any) -> list[dict[str, Any]]:
    """Extract /etc/config/* entries from the sanitized snapshot for bundling."""
    if not isinstance(raw_snapshot, Mapping):
        return []
    files = raw_snapshot.get("files")
    if not isinstance(files, Mapping):
        return []
    result = []
    for path, entry in sorted(files.items()):
        if not str(path).startswith("/etc/config/"):
            continue
        if not isinstance(entry, Mapping):
            continue
        content = entry.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        name = str(path).removeprefix("/etc/config/")
        archive_path = f"config/{name}"
        preview_lines = content.splitlines()[:60]
        result.append(
            {
                "name": name,
                "source_path": str(path),
                "archive_path": archive_path,
                "size": len(content.encode("utf-8")),
                "preview": "\n".join(preview_lines),
                "content": content,
            }
        )
    return result


def sanitize_config_files(config_files: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Strip raw content from config file descriptors for template rendering."""
    return [
        {
            "name": str(cf.get("name", "")),
            "source_path": str(cf.get("source_path", "")),
            "archive_path": str(cf.get("archive_path", "")),
            "size": int(cf.get("size", 0) or 0),
            "preview": str(cf.get("preview", "")),
        }
        for cf in config_files
    ]


def materialize_config_files(
    report_dir: Path, config_files: Sequence[Mapping[str, Any]]
) -> list[Path]:
    """Write config file contents under report_dir/config/."""
    config_dir = report_dir / "config"
    if config_dir.exists():
        shutil.rmtree(config_dir)
    written = []
    for cf in config_files:
        archive_path = Path(str(cf.get("archive_path", "")))
        content = cf.get("content")
        if not archive_path.parts or not isinstance(content, str):
            continue
        destination = report_dir / archive_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        written.append(destination)
    return written


def build_auth_events(raw_snapshot: Any) -> dict[str, Any]:
    """Extract structured authentication events from the victoria_logs snapshot key."""
    if not isinstance(raw_snapshot, Mapping):
        return {"available": False, "events": [], "event_count": 0}
    vl = raw_snapshot.get("victoria_logs")
    if not isinstance(vl, Mapping):
        return {"available": False, "events": [], "event_count": 0}
    events = vl.get("events", [])
    if not isinstance(events, list):
        events = []
    return {
        "available": bool(vl.get("available")),
        "event_count": int(vl.get("event_count", len(events))),
        "events": [
            {
                "time": str(ev.get("time", ""))[:23].replace("T", " "),
                "source": str(ev.get("source", "")),
                "event_type": str(ev.get("event_type", "")),
                "user": str(ev.get("user", "")),
                "detail": str(ev.get("detail", ""))[:160],
            }
            for ev in events
            if isinstance(ev, Mapping)
        ],
        "errors": vl.get("errors", {}),
    }


def _archive_file(archive: tarfile.TarFile, path: Path, arcname: str) -> None:
    stat = path.stat()
    info = tarfile.TarInfo(arcname)
    info.size = stat.st_size
    info.mode = stat.st_mode & 0o777
    info.mtime = int(stat.st_mtime)
    with path.open("rb") as handle:
        archive.addfile(info, handle)


def bundle_report_artifacts(
    report_dir: str | Path,
    output_path: str | Path | None = None,
    *,
    validate: bool = True,
) -> Path:
    report_dir = Path(report_dir)
    render_report(report_dir, report_dir / DEFAULT_OUTPUT_NAME, validate=validate)
    bundle_path = Path(output_path) if output_path else report_dir / DEFAULT_BUNDLE_NAME
    bundle_path.parent.mkdir(parents=True, exist_ok=True)

    root_name = "audit-report"
    excluded = {bundle_path.resolve()}
    files = sorted(
        path
        for path in report_dir.rglob("*")
        if path.is_file() and path.resolve() not in excluded
    )

    with tarfile.open(bundle_path, "w:gz") as archive:
        for path in files:
            arcname = str(Path(root_name) / path.relative_to(report_dir))
            _archive_file(archive, path, arcname)

    return bundle_path


def normalize_api_audit(inventory: Any) -> dict[str, Any]:
    """Extract the API audit trail sub-section from the inventory dict."""
    if not isinstance(inventory, dict):
        return {}
    raw = inventory.get("api_audit", {})
    if not isinstance(raw, dict):
        return {}
    counts = raw.get("counts", {})
    return {
        "available": bool(raw.get("api_log_lines", 0)),
        "api_log_lines": raw.get("api_log_lines", 0),
        "counts": counts,
        "logins": raw.get("login_events", []),
        "logouts": raw.get("logout_events", []),
        "auth_failures": raw.get("auth_failure_events", []),
        "config_changes": raw.get("config_change_events", []),
    }


def find_secret_pattern_matches(paths: list[str | Path]) -> list[dict[str, Any]]:
    matches = []
    for path in paths:
        artifact = Path(path)
        if artifact.is_dir():
            matches.extend(
                find_secret_pattern_matches(
                    sorted(artifact.glob("*.json")) + sorted(artifact.glob("*.html"))
                ),
            )
        elif artifact.exists():
            matches.extend(
                find_secret_pattern_matches_in_text(
                    artifact.read_text(encoding="utf-8", errors="replace"),
                    artifact,
                ),
            )
    return matches


def find_secret_pattern_matches_in_text(
    text: str, path: Path | None = None
) -> list[dict[str, Any]]:
    matches = []
    for name, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(text):
            matches.append(
                {
                    "pattern": name,
                    "path": str(path) if path else None,
                    "offset": match.start(),
                }
            )
    return matches


def normalize_rows(value: Any) -> list[dict[str, str]]:
    if isinstance(value, list):
        return [normalize_row(item, index) for index, item in enumerate(value, start=1)]
    if isinstance(value, dict):
        if all(isinstance(item, dict) for item in value.values()):
            return [
                {"name": str(key), **normalize_row(item, index)}
                for index, (key, item) in enumerate(value.items(), start=1)
            ]
        return [
            {"property": humanize(key), "value": format_inventory_value(item)}
            for key, item in value.items()
        ]
    if value in (None, ""):
        return []
    return [{"property": "Value", "value": format_inventory_value(value)}]


def normalize_row(value: Any, index: int) -> dict[str, str]:
    if isinstance(value, dict):
        return {
            str(key): format_inventory_value(item) for key, item in value.items()
        }
    return {"index": str(index), "value": format_inventory_value(value)}


def columns_for_rows(rows: list[dict[str, Any]]) -> list[str]:
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    return columns


def normalize_area_scores(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [
            normalize_area_score(item, index)
            for index, item in enumerate(value, start=1)
        ]
    if isinstance(value, dict):
        return [
            normalize_area_score(
                {"name": key, **(item if isinstance(item, dict) else {"score": item})},
                index,
            )
            for index, (key, item) in enumerate(value.items(), start=1)
        ]
    return []


def normalize_area_score(value: Any, index: int) -> dict[str, Any]:
    if not isinstance(value, dict):
        value = {"name": f"Area {index}", "score": value}
    return {
        "name": humanize(
            first_present(value, ("name", "area", "category"), default=f"Area {index}")
        ),
        "score": first_present(value, ("score", "value"), default="not assessed"),
        "status": first_present(value, ("status", "state"), default="not assessed"),
        "weight": first_present(value, ("weight",), default=""),
    }


def normalize_evidence(value: Any) -> list[dict[str, str]]:
    evidence_items = extract_sequence(
        value, ("evidence", "items", "refs", "references")
    )
    normalized = []
    for index, item in enumerate(evidence_items, start=1):
        if isinstance(item, dict):
            normalized.append(
                {
                    "id": str(
                        first_present(
                            item, ("id", "ref", "name"), default=f"evidence-{index}"
                        )
                    ),
                    "source": str(
                        first_present(item, ("source", "file", "artifact"), default="")
                    ),
                    "detail": format_value(
                        first_present(
                            item,
                            ("detail", "description", "value", "line"),
                            default=item,
                        ),
                    ),
                }
            )
        else:
            normalized.append(
                {"id": f"evidence-{index}", "source": "", "detail": format_value(item)}
            )
    return normalized


def normalize_compliance_refs(value: Any) -> list[str]:
    refs = []
    for item in extract_sequence(value, ("controls", "items", "mappings")):
        if isinstance(item, dict):
            framework = first_present(item, ("framework", "standard"), default="")
            control = first_present(item, ("control", "id", "code"), default="")
            title = first_present(item, ("title", "name"), default="")
            refs.append(
                " ".join(
                    str(part) for part in (framework, control, title) if part
                ).strip()
            )
        else:
            refs.append(str(item))
    return [ref for ref in refs if ref]


def flatten_mapping_dict(mapping: dict[str, Any]) -> list[dict[str, Any]]:
    flattened = []
    for framework, controls in mapping.items():
        if isinstance(controls, dict):
            for control, value in controls.items():
                if isinstance(value, dict):
                    flattened.append(
                        {"framework": framework, "control": control, **value}
                    )
                else:
                    flattened.append(
                        {"framework": framework, "control": control, "status": value}
                    )
    return flattened


def extract_sequence(value: Any, keys: tuple[str, ...]) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, list):
                return candidate
            if isinstance(candidate, dict):
                return list(candidate.values())
        if "by_severity" in value and isinstance(value["by_severity"], dict):
            return [
                item
                for items in value["by_severity"].values()
                for item in extract_sequence(items, keys)
            ]
    if value in (None, ""):
        return []
    return [value]


def normalize_text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [format_value(item) for item in value]
    if isinstance(value, dict):
        return [f"{humanize(key)}: {format_value(item)}" for key, item in value.items()]
    if value:
        return [format_value(value)]
    return []


def severity_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = {severity: 0 for severity in ("critical", "high", "medium", "low", "info")}
    for finding in findings:
        severity = str(finding.get("severity", "info")).lower()
        counts[severity if severity in counts else "info"] += 1
    return counts


def derive_status(counts: dict[str, int]) -> str:
    if counts.get("critical", 0) or counts.get("high", 0):
        return "red"
    if counts.get("medium", 0):
        return "yellow"
    return "green"


def derive_score(counts: dict[str, int]) -> int:
    deductions = (
        counts.get("critical", 0) * 25
        + counts.get("high", 0) * 15
        + counts.get("medium", 0) * 7
        + counts.get("low", 0) * 2
    )
    return max(0, 100 - deductions)


def first_present(
    data: dict[str, Any], keys: tuple[str, ...], default: Any = None
) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return default


def format_value(value: Any) -> str:
    if value is None:
        return "not available"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Mapping):
        items = [
            f"{humanize(key)}: {format_value(item)}" for key, item in value.items()
        ]
        return "; ".join(items) if items else "{}"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if not value:
            return "[]"
        rendered = [format_value(item) for item in value]
        return (
            ", ".join(rendered)
            if all(not isinstance(item, Mapping) for item in value)
            else " | ".join(rendered)
        )
    return str(value)


def format_inventory_value(value: Any) -> str:
    if value is None:
        return "not available"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Mapping):
        items = []
        for key, item in value.items():
            rendered = format_inventory_value(item)
            if "\n" in rendered:
                rendered = rendered.replace("\n", "\n  ")
            items.append(f"{humanize(key)}: {rendered}")
        return "\n".join(items) if items else "{}"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if not value:
            return "[]"
        rendered = [format_inventory_value(item) for item in value]
        return (
            "\n\n".join(rendered)
            if any(isinstance(item, Mapping) for item in value)
            else ", ".join(rendered)
        )
    return str(value)


def humanize(value: Any) -> str:
    return str(value).replace("_", " ").replace("-", " ").strip().title()


def json_pretty(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def severity_class(value: Any) -> str:
    severity = str(value).lower()
    return severity if severity in SEVERITY_ORDER else "info"


def status_class(value: Any) -> str:
    status = str(value).lower()
    if status in ("pass", "passed", "ok", "green", "compliant", "implemented"):
        return "green"
    if status in ("warn", "warning", "yellow", "partial", "partially implemented"):
        return "yellow"
    if status in ("fail", "failed", "red", "non-compliant", "not implemented"):
        return "red"
    return "neutral"


def sha256sum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render or validate NethSecurity audit report artifacts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser(
        "render", help="render audit-report.html from JSON artifacts"
    )
    render_parser.add_argument(
        "--input",
        required=True,
        help="directory containing sanitized audit JSON artifacts",
    )
    render_parser.add_argument(
        "--output", help="output HTML path; defaults to INPUT/audit-report.html"
    )
    render_parser.add_argument(
        "--template-dir", help="directory containing audit-report.html.j2"
    )
    render_parser.add_argument(
        "--asset-dir", help="directory containing audit-report.css"
    )
    render_parser.add_argument(
        "--no-validation",
        action="store_true",
        help="skip generated HTML secret-pattern validation",
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="scan generated HTML/JSON artifacts for known secret patterns",
    )
    validate_parser.add_argument(
        "paths", nargs="+", help="files or directories to validate"
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    if args.command == "render":
        output = render_report(
            input_dir=args.input,
            output_path=args.output,
            template_dir=args.template_dir,
            asset_dir=args.asset_dir,
            validate=not args.no_validation,
        )
        print(json.dumps({"output": str(output), "status": "ok"}))
        return 0

    matches = find_secret_pattern_matches([Path(path) for path in args.paths])
    print(
        json.dumps(
            {"status": "failed" if matches else "ok", "matches": matches},
            sort_keys=True,
        )
    )
    return 1 if matches else 0


if __name__ == "__main__":
    sys.exit(main())
