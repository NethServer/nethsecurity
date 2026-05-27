#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""Shared JSON-compatible helpers for the NethSecurity audit analyzers."""

from __future__ import annotations

import hashlib
import json
import re
import shlex
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

JsonDict = dict[str, Any]


class AuditError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class FileEvidence:
    path: str
    present: bool
    readable: bool
    size: int | None = None
    truncated: bool = False
    content: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class CommandEvidence:
    name: str
    args: list[str]
    found: bool
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    truncated: bool = False
    parsed_json: object | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


SEVERITY_ORDER = ("critical", "high", "medium", "low", "info")
SEVERITY_RANK = {severity: index for index, severity in enumerate(SEVERITY_ORDER)}
SEVERITY_RISK_POINTS = {
    "critical": 100,
    "high": 75,
    "medium": 45,
    "low": 20,
    "info": 0,
}

AREA_WEIGHTS = {
    "identity": 25,
    "firewall": 25,
    "vpn": 20,
    "ips": 15,
    "logging": 15,
}
AREA_SCORE_GROUP = {
    "identity": "identity",
    "firewall": "firewall",
    "vpn": "vpn",
    "ips": "ips",
    "logging": "logging",
    "telemetry": "logging",
}
AREA_TITLES = {
    "identity": "Identity and access control",
    "firewall": "Firewall and exposed services",
    "vpn": "VPN cryptography and remote access",
    "ips": "IPS/IDS and threat detection",
    "logging": "Logging and audit trail",
    "telemetry": "Telemetry and security indicators",
}

NIST_CONTROLS = {
    "AC-2": "Account Management",
    "AC-4": "Information Flow Enforcement",
    "AC-6": "Least Privilege",
    "AC-17": "Remote Access",
    "AU-2": "Event Logging",
    "AU-6": "Audit Record Review, Analysis, and Reporting",
    "AU-9": "Protection of Audit Information",
    "AU-11": "Audit Record Retention",
    "CM-6": "Configuration Settings",
    "CM-7": "Least Functionality",
    "IA-2": "Identification and Authentication",
    "IA-5": "Authenticator Management",
    "RA-5": "Vulnerability Monitoring and Scanning",
    "SC-7": "Boundary Protection",
    "SC-8": "Transmission Confidentiality and Integrity",
    "SC-13": "Cryptographic Protection",
    "SI-3": "Malicious Code Protection",
    "SI-4": "System Monitoring",
}

ACN_NIS2_CATEGORIES = {
    "identity_access_governance": "Identity and access governance",
    "network_segmentation": "Network segmentation and boundary protection",
    "secure_communications": "Secure communications and cryptography",
    "threat_detection": "Vulnerability and threat detection",
    "logging_monitoring": "Logging, monitoring, and incident evidence",
    "risk_management": "Risk management and remediation tracking",
}

TRUE_VALUES = {"1", "true", "yes", "on", "enabled", "enable", "active", "running"}
FALSE_VALUES = {
    "0",
    "false",
    "no",
    "off",
    "disabled",
    "disable",
    "inactive",
    "stopped",
    "none",
    "",
}
SECRET_FIELD_RE = re.compile(
    r"(secret|password|passwd|private[_-]?key|preshared|token|hash|credential)", re.I
)
REDACTED_VALUES = {
    "",
    "redacted",
    "<redacted>",
    "[redacted]",
    "***",
    "******",
    "x",
    "<hidden>",
    "hidden",
}
ADMIN_PORTS = {"22", "80", "443", "4443", "8000", "8080", "8443", "9090", "9091"}


def json_safe(value: Any) -> Any:
    """Return a JSON-serializable copy of *value*."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, set):
        return [json_safe(item) for item in sorted(value, key=str)]
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [json_safe(item) for item in value]
    if isinstance(value, bytes | bytearray):
        return value.decode("utf-8", "replace")
    return str(value)


def as_dict(value: Any) -> JsonDict:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple | set):
        return list(value)
    return [value]


def string_list(value: Any) -> list[str]:
    """Normalize UCI strings/lists into a list of non-empty strings."""
    result: list[str] = []
    for item in as_list(value):
        if item is None:
            continue
        if isinstance(item, str):
            parts = (
                re.split(r"[\s,]+", item.strip())
                if "," in item or " " in item.strip()
                else [item.strip()]
            )
            result.extend(part for part in parts if part)
        else:
            result.append(str(item))
    return result


def normalize_severity(severity: Any) -> str:
    normalized = str(severity or "info").strip().lower()
    return normalized if normalized in SEVERITY_RANK else "info"


def worst_severity(severities: Sequence[Any]) -> str:
    normalized = [normalize_severity(severity) for severity in severities]
    if not normalized:
        return "info"
    return min(normalized, key=lambda severity: SEVERITY_RANK[severity])


def severity_counts(findings: Sequence[Mapping[str, Any]]) -> JsonDict:
    counts = {severity: 0 for severity in SEVERITY_ORDER}
    for finding in findings:
        counts[normalize_severity(finding.get("severity"))] += 1
    return counts


def to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, int | float):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return default


def option_value(
    section: Mapping[str, Any], names: str | Sequence[str], default: Any = None
) -> Any:
    """Read a UCI option from a section, accepting case and dash/underscore variants."""
    wanted = [names] if isinstance(names, str) else list(names)
    if not isinstance(section, Mapping):
        return default
    lowered = {
        str(key).lower().replace("-", "_"): value for key, value in section.items()
    }
    for name in wanted:
        key = str(name)
        if key in section:
            return section[key]
        normalized = key.lower().replace("-", "_")
        if normalized in lowered:
            return lowered[normalized]
    return default


def section_type(section: Mapping[str, Any]) -> str:
    return str(
        option_value(section, (".type", "_type", "section_type", "type"), "")
    ).strip()


def section_name(section: Mapping[str, Any]) -> str:
    return str(
        option_value(section, (".name", "_name", "section", "id", "name"), "")
    ).strip()


def is_enabled_section(section: Mapping[str, Any], default: bool = True) -> bool:
    if option_value(section, ("disabled", "disable")) is not None:
        return not to_bool(
            option_value(section, ("disabled", "disable")), default=False
        )
    return to_bool(
        option_value(section, ("enabled", "enable"), default), default=default
    )


def slugify(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return slug or "item"


def fingerprint(value: Any, prefix: str = "sha256") -> str:
    text = str(value or "").strip()
    if not text or is_redacted_value(text):
        return ""
    return f"{prefix}:{hashlib.sha256(text.encode()).hexdigest()[:16]}"


def is_redacted_value(value: Any) -> bool:
    if value is None:
        return True
    normalized = str(value).strip().lower()
    return (
        normalized in REDACTED_VALUES
        or "redact" in normalized
        or set(normalized) <= {"*", "x", "-"}
    )


def secret_field_name(name: Any) -> bool:
    return bool(SECRET_FIELD_RE.search(str(name)))


def has_unredacted_secret(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, Mapping):
        return any(
            secret_field_name(key) and has_unredacted_secret(item)
            for key, item in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return any(has_unredacted_secret(item) for item in value)
    text = str(value).strip()
    return bool(text and len(text) > 8 and not is_redacted_value(text))


def _looks_like_uci_show(text: str) -> bool:
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            return False
        left, _, _ = line.partition("=")
        return left.count(".") >= 1 and not left.startswith(
            ("config ", "option ", "list ")
        )
    return False


def _uci_show_value(value: str) -> Any:
    try:
        parts = shlex.split(value, comments=False, posix=True)
    except ValueError:
        parts = [value.strip().strip("'\"")]
    if not parts:
        return ""
    return parts[0] if len(parts) == 1 else parts


def parse_uci_show(text: str) -> list[JsonDict]:
    """Parse `uci show <package>` output into UCI-like sections."""
    sections: dict[str, JsonDict] = {}
    order: list[str] = []
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        left, _, right = line.partition("=")
        parts = left.split(".", 2)
        if len(parts) < 2:
            continue
        section_ref = parts[1]
        if section_ref not in sections:
            sections[section_ref] = {".name": section_ref}
            order.append(section_ref)
        value = _uci_show_value(right)
        if len(parts) == 2:
            sections[section_ref][".type"] = str(value)
            continue
        option = parts[2]
        if option in sections[section_ref]:
            existing = sections[section_ref][option]
            sections[section_ref][option] = as_list(existing) + as_list(value)
        else:
            sections[section_ref][option] = value
    return [sections[section_ref] for section_ref in order]


def parse_uci_config(text: str) -> list[JsonDict]:
    """Parse enough UCI syntax for audit normalization."""
    if _looks_like_uci_show(text):
        return parse_uci_show(text)
    sections: list[JsonDict] = []
    current: JsonDict | None = None
    counters: dict[str, int] = {}
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parts = shlex.split(line, comments=True, posix=True)
        except ValueError:
            parts = line.split()
        if not parts:
            continue
        keyword = parts[0]
        if keyword == "config" and len(parts) >= 2:
            current_type = parts[1]
            index = counters.get(current_type, 0)
            counters[current_type] = index + 1
            current_name = parts[2] if len(parts) > 2 else f"@{current_type}[{index}]"
            current = {".type": current_type, ".name": current_name}
            sections.append(current)
            continue
        if current is None or len(parts) < 3:
            continue
        key = parts[1]
        value = " ".join(parts[2:])
        if keyword == "option":
            current[key] = value
        elif keyword == "list":
            current.setdefault(key, []).append(value)
    return sections


def _normalize_section(name: str, value: Any) -> JsonDict | None:
    if not isinstance(value, Mapping):
        return None
    section = dict(value)
    section.setdefault(".name", name)
    if ".type" not in section:
        for key in ("_type", "section_type", "type"):
            if key in section:
                section[".type"] = section[key]
                break
    return section


def _sections_from_package_data(data: Any) -> list[JsonDict]:
    if isinstance(data, str):
        return parse_uci_config(data)
    if isinstance(data, Sequence) and not isinstance(data, str | bytes | bytearray):
        return [dict(item) for item in data if isinstance(item, Mapping)]
    if not isinstance(data, Mapping):
        return []
    if isinstance(data.get("sections"), Sequence):
        return [dict(item) for item in data["sections"] if isinstance(item, Mapping)]
    for content_key in ("content", "raw", "text", "config"):
        if isinstance(data.get(content_key), str):
            return parse_uci_config(data[content_key])
    if any(str(key).startswith(".") for key in data):
        return [dict(data)]
    sections: list[JsonDict] = []
    for name, value in data.items():
        normalized = _normalize_section(str(name), value)
        if normalized is not None:
            sections.append(normalized)
    return sections


def _file_entry_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        for key in ("content", "text", "data", "stdout"):
            if isinstance(value.get(key), str):
                return value[key]
    return ""


def file_map(raw_snapshot: Mapping[str, Any]) -> JsonDict:
    for key in ("files", "file_contents", "sources"):
        value = raw_snapshot.get(key)
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def get_file(raw_snapshot: Mapping[str, Any], path: str) -> str:
    files = file_map(raw_snapshot)
    if path in files:
        return _file_entry_content(files[path])
    for file_path, value in files.items():
        if str(file_path).rstrip("/").endswith(path):
            return _file_entry_content(value)
    return ""


def file_metadata(raw_snapshot: Mapping[str, Any], path: str) -> JsonDict:
    files = file_map(raw_snapshot)
    entry = files.get(path)
    if entry is None:
        for file_path, value in files.items():
            if str(file_path).rstrip("/").endswith(path):
                entry = value
                break
    if isinstance(entry, Mapping):
        return as_dict(entry.get("metadata") or entry.get("stat") or {})
    return {}


def files_matching(raw_snapshot: Mapping[str, Any], *needles: str) -> JsonDict:
    files = file_map(raw_snapshot)
    lowered_needles = [needle.lower() for needle in needles]
    return {
        str(path): value
        for path, value in files.items()
        if all(needle in str(path).lower() for needle in lowered_needles)
    }


def uci_sections(
    raw_snapshot: Mapping[str, Any], package: str, wanted_type: str | None = None
) -> list[JsonDict]:
    data = None
    for key in ("uci", "configs", "uci_configs"):
        container = raw_snapshot.get(key)
        if isinstance(container, Mapping) and package in container:
            data = container[package]
            break
    if data is None:
        data = get_file(raw_snapshot, f"/etc/config/{package}")
    sections = _sections_from_package_data(data)
    if wanted_type is not None:
        sections = [
            section for section in sections if section_type(section) == wanted_type
        ]
    return [json_safe(section) for section in sections]


def _command_entry(raw_snapshot: Mapping[str, Any], candidates: Sequence[str]) -> Any:
    commands = (
        raw_snapshot.get("commands")
        or raw_snapshot.get("command_outputs")
        or raw_snapshot.get("safe_commands")
    )
    if not isinstance(commands, Mapping):
        return None
    normalized_candidates = [candidate.lower() for candidate in candidates]
    for command, value in commands.items():
        command_text = str(command).lower()
        if any(
            candidate == command_text or candidate in command_text
            for candidate in normalized_candidates
        ):
            return value
    return None


def _json_from_text(text: str) -> Any:
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return None


def command_text(raw_snapshot: Mapping[str, Any], candidates: Sequence[str]) -> str:
    entry = _command_entry(raw_snapshot, candidates)
    if isinstance(entry, str):
        return entry
    if isinstance(entry, Mapping):
        for key in ("stdout", "output", "text", "content"):
            if isinstance(entry.get(key), str):
                return entry[key]
    return ""


def command_json(raw_snapshot: Mapping[str, Any], candidates: Sequence[str]) -> Any:
    entry = _command_entry(raw_snapshot, candidates)
    if isinstance(entry, Mapping):
        for key in ("json", "data", "parsed"):
            if key in entry:
                return entry[key]
        text = command_text(raw_snapshot, candidates)
        parsed = _json_from_text(text)
        return parsed if parsed is not None else entry
    if isinstance(entry, str):
        parsed = _json_from_text(entry)
        return parsed if parsed is not None else {}
    return {}


def service_state(
    raw_snapshot: Mapping[str, Any], service_names: Sequence[str]
) -> JsonDict:
    services = raw_snapshot.get("services")
    if not isinstance(services, Mapping):
        services = command_json(
            raw_snapshot, ("ubus call service list", "service list")
        )
    if not isinstance(services, Mapping):
        return {"present": False, "enabled": False, "running": False, "instances": []}
    names = [name.lower() for name in service_names]
    result = {"present": False, "enabled": False, "running": False, "instances": []}
    for service_name, service_data in services.items():
        if not any(name in str(service_name).lower() for name in names):
            continue
        data = as_dict(service_data)
        result["present"] = True
        result["enabled"] = result["enabled"] or to_bool(
            option_value(data, ("enabled", "autostart")), default=False
        )
        result["running"] = result["running"] or to_bool(
            option_value(data, ("running", "active")), default=False
        )
        instances = as_dict(data.get("instances"))
        for instance_name, instance_data in instances.items():
            instance = as_dict(instance_data)
            running = to_bool(instance.get("running"), default=False) or bool(
                instance.get("pid")
            )
            result["running"] = result["running"] or running
            result["instances"].append(
                {
                    "name": str(instance_name),
                    "running": running,
                    "pid_present": bool(instance.get("pid")),
                }
            )
    return json_safe(result)


def parse_passwd(content: str) -> list[JsonDict]:
    accounts: list[JsonDict] = []
    for line in str(content or "").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) < 7:
            continue
        username, password_marker, uid, gid, gecos, home, shell = parts[:7]
        try:
            uid_number = int(uid)
        except ValueError:
            uid_number = -1
        try:
            gid_number = int(gid)
        except ValueError:
            gid_number = -1
        accounts.append(
            {
                "username": username,
                "uid": uid_number,
                "gid": gid_number,
                "gecos": gecos,
                "home": home,
                "shell": shell,
                "password_marker": "set"
                if password_marker and password_marker not in {"x", "*", "!"}
                else password_marker,
                "interactive_shell": shell
                not in {"/bin/false", "/sbin/nologin", "/usr/sbin/nologin", "nologin"},
            }
        )
    return accounts


def parse_group(content: str) -> JsonDict:
    groups: JsonDict = {}
    for line in str(content or "").splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) < 4:
            continue
        name, _, gid, members = parts[:4]
        member_list = [member for member in members.split(",") if member]
        groups[name] = {"gid": gid, "members": member_list}
    return groups


def iter_text(value: Any) -> list[str]:
    texts: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            texts.append(str(key))
            texts.extend(iter_text(item))
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for item in value:
            texts.extend(iter_text(item))
    elif value is not None:
        texts.append(str(value))
    return texts


def contains_indicator(value: Any, indicators: Sequence[str]) -> bool:
    lowered = [indicator.lower() for indicator in indicators]
    return any(
        indicator in text.lower() for text in iter_text(value) for indicator in lowered
    )


def build_finding(
    finding_id: str,
    title: str,
    severity: str,
    area: str,
    component: str,
    description: str,
    evidence: Mapping[str, Any] | None,
    remediation: str,
    nist: Sequence[str] | None = None,
    acn: Sequence[str] | None = None,
) -> JsonDict:
    normalized_severity = normalize_severity(severity)
    nist_controls = sorted(dict.fromkeys(nist or []))
    acn_categories = sorted(dict.fromkeys(acn or []))
    return json_safe(
        {
            "id": finding_id or slugify(f"{area}-{title}"),
            "title": title,
            "severity": normalized_severity,
            "area": area,
            "score_area": AREA_SCORE_GROUP.get(area, area),
            "component": component,
            "description": description,
            "evidence": evidence or {},
            "remediation": remediation,
            "compliance": {
                "nist_800_53r5": nist_controls,
                "acn_nis2": acn_categories,
            },
            "risk_score": SEVERITY_RISK_POINTS[normalized_severity],
        }
    )


def build_result(
    area: str, inventory: Mapping[str, Any], findings: Sequence[Mapping[str, Any]]
) -> JsonDict:
    counts = severity_counts(findings)
    max_severity = worst_severity([finding.get("severity") for finding in findings])
    status = (
        "red"
        if counts["critical"] or counts["high"]
        else "yellow"
        if counts["medium"]
        else "green"
    )
    return json_safe(
        {
            "inventory": {area: inventory},
            "findings": list(findings),
            "summary": {
                area: {
                    "title": AREA_TITLES.get(area, area.title()),
                    "status": status,
                    "max_severity": max_severity,
                    "finding_counts": counts,
                    "finding_count": sum(counts.values()),
                }
            },
            "compliance": {},
        }
    )
