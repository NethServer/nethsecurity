#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from __future__ import annotations

import glob
import gzip
import os
from pathlib import Path

from ns_audit.collectors.commands import run_command
from ns_audit.config import MAX_LOG_FILE_BYTES, MAX_LOG_LINES

_STORAGE_LOG_GLOB = "/mnt/data/log/messages*"
_MEMORY_LOG_GLOB = "/var/log/messages*"


def _last_lines(text: str, max_lines: int) -> tuple[str, bool]:
    lines = text.splitlines()
    truncated = len(lines) > max_lines
    if truncated:
        lines = lines[-max_lines:]
    return "\n".join(lines), truncated


def _read_gzip_head(path: Path, max_bytes: int, max_lines: int) -> dict[str, object]:
    try:
        size = path.stat().st_size
        with gzip.open(path, "rb") as handle:
            data = handle.read(max_bytes + 1)
    except OSError as exc:
        return {"path": str(path), "present": True, "readable": False, "error": str(exc)}

    truncated = len(data) > max_bytes
    content, line_truncated = _last_lines(
        data[:max_bytes].decode("utf-8", "replace"), max_lines
    )
    return {
        "path": str(path),
        "present": True,
        "readable": True,
        "size": size,
        "truncated": truncated or line_truncated,
        "content": content,
    }


def _read_text_tail(path: Path, max_bytes: int, max_lines: int) -> dict[str, object]:
    if not path.exists():
        return {"path": str(path), "present": False, "readable": False, "error": "not_found"}
    if not path.is_file():
        return {"path": str(path), "present": True, "readable": False, "error": "not_a_file"}
    if path.suffix == ".gz":
        return _read_gzip_head(path, max_bytes, max_lines)

    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            if size > max_bytes:
                handle.seek(-max_bytes, os.SEEK_END)
            data = handle.read(max_bytes)
    except OSError as exc:
        return {"path": str(path), "present": True, "readable": False, "error": str(exc)}

    content, line_truncated = _last_lines(data.decode("utf-8", "replace"), max_lines)
    return {
        "path": str(path),
        "present": True,
        "readable": True,
        "size": size,
        "truncated": size > max_bytes or line_truncated,
        "content": content,
    }


def _expand_glob(pattern: str) -> list[str]:
    return sorted(glob.glob(pattern))


def _active_log_source() -> str:
    """Return active_source based on storage mount state.

    "storage" if persistent logs exist under /mnt/data/log/, else "memory".
    """
    return "storage" if _expand_glob(_STORAGE_LOG_GLOB) else "memory"


def collect_log_files(
    max_bytes: int = MAX_LOG_FILE_BYTES, max_lines: int = MAX_LOG_LINES
) -> tuple[list[dict[str, object]], list[dict[str, object]], str]:
    """Return (primary_files, secondary_files, active_source).

    primary_files comes from the active source (bundled in tar.gz).
    secondary_files comes from the other source if available (for analysis only,
    not bundled). Both are included in the snapshot so analyzers can see all data.
    """
    active_source = _active_log_source()
    if active_source == "storage":
        primary_pattern, secondary_pattern = _STORAGE_LOG_GLOB, _MEMORY_LOG_GLOB
    else:
        primary_pattern, secondary_pattern = _MEMORY_LOG_GLOB, _STORAGE_LOG_GLOB

    primary = [_read_text_tail(Path(p), max_bytes, max_lines) for p in _expand_glob(primary_pattern)]
    secondary = [_read_text_tail(Path(p), max_bytes, max_lines) for p in _expand_glob(secondary_pattern)]
    return primary, secondary, active_source


def collect_logread(max_lines: int = MAX_LOG_LINES) -> dict[str, object]:
    result = run_command(("logread",), name="logread", max_bytes=MAX_LOG_FILE_BYTES)
    stdout = result.get("stdout")
    if isinstance(stdout, str):
        result["stdout"], lines_truncated = _last_lines(stdout, max_lines)
        result["truncated"] = bool(result.get("truncated")) or lines_truncated
    return result


def collect_logs() -> dict[str, object]:
    primary, secondary, active_source = collect_log_files()
    return {
        "logread": collect_logread(),
        "files": primary,
        "secondary_files": secondary,
        "active_source": active_source,
        "limits": {"max_file_bytes": MAX_LOG_FILE_BYTES, "max_lines": MAX_LOG_LINES},
    }

