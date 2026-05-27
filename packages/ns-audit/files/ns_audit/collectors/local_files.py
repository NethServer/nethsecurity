#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from __future__ import annotations

import glob
from pathlib import Path

from ns_audit.config import CONFIG_DIR_GLOB, CONFIG_FILES, LOGROTATE_GLOBS, MAX_TEXT_FILE_BYTES
from ns_audit.models import FileEvidence


def _read_limited_text(path: Path, max_bytes: int) -> FileEvidence:
    if not path.exists():
        return FileEvidence(
            path=str(path), present=False, readable=False, error="not_found"
        )
    if not path.is_file():
        return FileEvidence(
            path=str(path), present=True, readable=False, error="not_a_file"
        )

    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            data = handle.read(max_bytes + 1)
    except OSError as exc:
        return FileEvidence(
            path=str(path), present=True, readable=False, error=str(exc)
        )

    truncated = len(data) > max_bytes or size > max_bytes
    content = data[:max_bytes].decode("utf-8", "replace")
    return FileEvidence(
        path=str(path),
        present=True,
        readable=True,
        size=size,
        truncated=truncated,
        content=content,
    )


def _expand_globs(patterns: tuple[str, ...]) -> list[str]:
    paths: set[str] = set()
    for pattern in patterns:
        paths.update(glob.glob(pattern))
    return sorted(paths)


def collect_local_files(
    max_bytes: int = MAX_TEXT_FILE_BYTES,
) -> list[dict[str, object]]:
    # All files under /etc/config/ plus explicit non-UCI config files and logrotate
    paths = [
        *_expand_globs((CONFIG_DIR_GLOB,)),
        *CONFIG_FILES,
        *_expand_globs(LOGROTATE_GLOBS),
    ]
    return [
        _read_limited_text(Path(path), max_bytes).to_dict()
        for path in dict.fromkeys(paths)
    ]
