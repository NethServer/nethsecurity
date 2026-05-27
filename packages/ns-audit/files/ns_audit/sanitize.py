#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "<redacted>"

_PRIVATE_KEY_BLOCK_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.DOTALL,
)
_OPENSSH_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN OPENSSH PRIVATE KEY-----.*?-----END OPENSSH PRIVATE KEY-----",
    re.DOTALL,
)
_INLINE_SECRET_BLOCK_RE = re.compile(
    r"<(?P<tag>key|tls-auth|tls-crypt|secret)>.*?</(?P=tag)>",
    re.DOTALL | re.IGNORECASE,
)
_UCI_SECRET_RE = re.compile(
    r"(?im)^(?P<prefix>\s*(?:option|list)\s+"
    r"(?:password|passwd|secret|token|api[_-]?key|private[_-]?key|preshared[_-]?key|psk|key|shared[_-]?secret)"
    r"\s+)(?P<quote>['\"]).*?(?P=quote)\s*$",
)
_KEY_VALUE_SECRET_RE = re.compile(
    r"(?im)^(?P<prefix>\s*[^#\n]*\b"
    r"(?:password|passwd|secret|token|credential|api[_-]?key|private[_-]?key|preshared[_-]?key|psk)"
    r"\b\s*[:=]\s*).+$",
)
_WIREGUARD_SECRET_RE = re.compile(
    r"(?im)^(?P<prefix>\s*(?:private key|preshared key):\s*).+$"
)
_AUTH_HEADER_RE = re.compile(
    r"(?im)^(?P<prefix>\s*authorization:\s*(?:bearer|basic)\s+).+$"
)
_PASSWORD_HASH_RE = re.compile(r"\$(?:1|2a|2b|2y|5|6|y|gy)\$[A-Za-z0-9./$]{20,}")

_SENSITIVE_KEYWORDS = (
    "password",
    "passwd",
    "passphrase",
    "secret",
    "token",
    "credential",
    "private_key",
    "private-key",
    "preshared",
    "psk",
    "api_key",
    "api-key",
    "apikey",
    "auth_key",
    "shared_key",
    "key_material",
)


def _is_sensitive_key(key: object) -> bool:
    key_text = str(key).lower().replace("-", "_")
    if key_text == "key":
        return True
    return any(keyword.replace("-", "_") in key_text for keyword in _SENSITIVE_KEYWORDS)


def redact_text(value: str) -> str:
    redacted = _OPENSSH_PRIVATE_KEY_RE.sub(REDACTED, value)
    redacted = _PRIVATE_KEY_BLOCK_RE.sub(REDACTED, redacted)
    redacted = _INLINE_SECRET_BLOCK_RE.sub(
        lambda match: f"<{match.group('tag')}>{REDACTED}</{match.group('tag')}>",
        redacted,
    )
    redacted = _UCI_SECRET_RE.sub(
        lambda match: f"{match.group('prefix')}{match.group('quote')}{REDACTED}{match.group('quote')}",
        redacted,
    )
    redacted = _KEY_VALUE_SECRET_RE.sub(
        lambda match: f"{match.group('prefix')}{REDACTED}", redacted
    )
    redacted = _WIREGUARD_SECRET_RE.sub(
        lambda match: f"{match.group('prefix')}{REDACTED}", redacted
    )
    redacted = _AUTH_HEADER_RE.sub(
        lambda match: f"{match.group('prefix')}{REDACTED}", redacted
    )
    return _PASSWORD_HASH_RE.sub(REDACTED, redacted)


def sanitize_value(value: Any, key: object | None = None) -> Any:
    # Only redact string values under sensitive key names.
    # Booleans, integers, and None are never actual secrets — preserve them as-is.
    if key is not None and _is_sensitive_key(key) and isinstance(value, str) and value:
        return REDACTED
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        return {
            item_key: sanitize_value(item_value, item_key)
            for item_key, item_value in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray | str):
        return [sanitize_value(item) for item in value]
    return value


def sanitize_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    sanitized = sanitize_value(snapshot)
    if isinstance(sanitized, dict):
        collector = sanitized.get("collector")
        if isinstance(collector, dict):
            collector["redaction"] = "secret patterns redacted before persistence"
        return sanitized
    return {"snapshot": sanitized}
