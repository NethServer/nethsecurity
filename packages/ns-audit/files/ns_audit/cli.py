#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from __future__ import annotations

import argparse
import hashlib
import html
import json
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ns_audit import __version__
from ns_audit.collectors import collect_all
from ns_audit.config import (
    COMPLIANCE_MAPPING_NAME,
    DEFAULT_OUTPUT_DIR,
    FINDINGS_NAME,
    INVENTORY_NAME,
    RAW_SNAPSHOT_NAME,
    REPORT_NAME,
    REPORT_BUNDLE_NAME,
    SUMMARY_NAME,
)
from ns_audit.models import AuditError
from ns_audit.sanitize import sanitize_snapshot


def _json_default(value: object) -> str:
    return str(value)


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(
            payload,
            handle,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=_json_default,
        )
        handle.write("\n")
    return path


def _read_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise AuditError("input_not_found", f"Input not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AuditError("invalid_json", f"Invalid JSON input {path}: {exc}") from exc


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_path(output: str | Path) -> Path:
    path = Path(output)
    if path.suffix == ".json":
        return path
    return path / RAW_SNAPSHOT_NAME


def _output_dir(output: str | Path) -> Path:
    path = Path(output)
    if path.suffix == ".json":
        return path.parent
    return path


def collect(output: str | Path) -> dict[str, object]:
    snapshot = sanitize_snapshot(collect_all())
    raw_snapshot = _write_json(_snapshot_path(output), snapshot)
    return {"raw_snapshot": str(raw_snapshot), "sha256": _hash_file(raw_snapshot)}


def _source_count(value: object) -> int:
    if isinstance(value, dict | list | tuple):
        return len(value)
    return 0


def _stub_analyze_snapshot(snapshot: dict[str, object]) -> dict[str, object]:
    sources = snapshot.get("sources", {})
    source_counts = (
        {name: _source_count(value) for name, value in sources.items()}
        if isinstance(sources, dict)
        else {}
    )
    generated_at = datetime.now(UTC).isoformat()
    return {
        INVENTORY_NAME: {
            "schema_version": 1,
            "generated_at": generated_at,
            "status": "analysis_stub",
            "source_counts": source_counts,
        },
        FINDINGS_NAME: {
            "schema_version": 1,
            "generated_at": generated_at,
            "status": "analysis_stub",
            "findings": [],
        },
        COMPLIANCE_MAPPING_NAME: {
            "schema_version": 1,
            "generated_at": generated_at,
            "status": "analysis_stub",
            "mappings": [],
        },
        SUMMARY_NAME: {
            "schema_version": 1,
            "generated_at": generated_at,
            "status": "analysis_stub",
            "message": "Analysis engine is not implemented in this package scope.",
            "finding_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        },
    }


def _load_analyzer():
    try:
        from ns_audit.analyzers import build_analysis_outputs
    except ImportError:
        try:
            from ns_audit.analyzers import analyze_snapshot
        except ImportError:
            return _stub_analyze_snapshot
        return analyze_snapshot
    return build_analysis_outputs


def _artifact_file_name(name: str) -> str:
    return {
        "inventory": INVENTORY_NAME,
        "findings": FINDINGS_NAME,
        "compliance": COMPLIANCE_MAPPING_NAME,
        "compliance_mapping": COMPLIANCE_MAPPING_NAME,
        "summary": SUMMARY_NAME,
    }.get(name, name)


def analyze(
    input_path: str | Path, output: str | Path | None = None
) -> dict[str, object]:
    raw_snapshot = (
        _snapshot_path(input_path) if Path(input_path).is_dir() else Path(input_path)
    )
    output_dir = _output_dir(output or raw_snapshot.parent)
    snapshot = _read_json(raw_snapshot)
    if not isinstance(snapshot, dict):
        raise AuditError("invalid_snapshot", "Raw snapshot must contain a JSON object")

    artifacts = _load_analyzer()(snapshot)
    paths = {}
    for file_name, payload in artifacts.items():
        artifact_name = _artifact_file_name(str(file_name))
        paths[artifact_name] = str(
            _write_json(output_dir / artifact_name, sanitize_snapshot(payload))
        )
    return {"artifacts": paths}


def _stub_render_report(input_dir: Path, output_path: Path) -> Path:
    summary_path = input_dir / SUMMARY_NAME
    summary = (
        _read_json(summary_path) if summary_path.exists() else {"status": "report_stub"}
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    escaped_summary = html.escape(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
    )
    body = (
        "<!doctype html>\n"
        '<html><head><meta charset="utf-8"><title>NethSecurity audit report</title></head>\n'
        "<body><h1>NethSecurity audit report</h1>\n"
        "<p>Report rendering is a placeholder in this package scope.</p>\n"
        f"<pre>{escaped_summary}</pre>\n"
        "</body></html>\n"
    )
    output_path.write_text(body, encoding="utf-8")
    return output_path


def _stub_bundle_report(input_dir: Path, output_path: Path) -> Path:
    _stub_render_report(input_dir, input_dir / REPORT_NAME)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    root_name = "audit-report"
    excluded = {output_path.resolve()}
    files = sorted(
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.resolve() not in excluded
    )
    with tarfile.open(output_path, "w:gz") as archive:
        for path in files:
            arcname = str(Path(root_name) / path.relative_to(input_dir))
            info = tarfile.TarInfo(arcname)
            stat = path.stat()
            info.size = stat.st_size
            info.mode = stat.st_mode & 0o777
            info.mtime = int(stat.st_mtime)
            with path.open("rb") as handle:
                archive.addfile(info, handle)
    return output_path


def _load_reporter():
    try:
        from ns_audit.reporting import render_report
    except ImportError:
        return _stub_render_report
    return render_report


def _load_bundle_reporter():
    try:
        from ns_audit.reporting import bundle_report_artifacts
    except ImportError:
        return _stub_bundle_report
    return bundle_report_artifacts


def _is_tarball_path(path: Path) -> bool:
    return path.name.endswith(".tar.gz") or path.suffix == ".tgz"


def report(
    input_path: str | Path, output: str | Path | None = None
) -> dict[str, object]:
    input_dir = Path(input_path)
    if input_dir.is_file():
        input_dir = input_dir.parent
    output_path = Path(output) if output else input_dir / REPORT_NAME
    if _is_tarball_path(output_path):
        bundle_path = _load_bundle_reporter()(input_dir, output_path)
        return {
            "report": str(input_dir / REPORT_NAME),
            "bundle": str(bundle_path),
        }
    report_path = _load_reporter()(input_dir, output_path)
    return {"report": str(report_path)}


def run(output: str | Path) -> dict[str, object]:
    output_dir = Path(output)
    collect_result = collect(output_dir)
    analyze_result = analyze(collect_result["raw_snapshot"], output_dir)
    report_result = report(output_dir, output_dir / REPORT_BUNDLE_NAME)
    return {
        "collect": collect_result,
        "analyze": analyze_result,
        "report": report_result,
    }


def _print_result(payload: object) -> None:
    print(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=_json_default)
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="NethSecurity on-device read-only audit collector"
    )
    parser.add_argument(
        "--version", action="version", version=f"ns-audit {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect_parser = subparsers.add_parser(
        "collect", help="Collect sanitized local evidence"
    )
    collect_parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory or raw_snapshot.json path",
    )
    collect_parser.set_defaults(func=lambda args: collect(args.output))

    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze a sanitized raw snapshot"
    )
    analyze_parser.add_argument(
        "--input",
        required=True,
        help="Input raw_snapshot.json path or containing directory",
    )
    analyze_parser.add_argument("--output", help="Output directory for JSON artifacts")
    analyze_parser.set_defaults(func=lambda args: analyze(args.input, args.output))

    report_parser = subparsers.add_parser(
        "report", help="Render an audit report from analysis artifacts"
    )
    report_parser.add_argument(
        "--input", required=True, help="Directory containing analysis artifacts"
    )
    report_parser.add_argument("--output", help="Output HTML report path")
    report_parser.set_defaults(func=lambda args: report(args.input, args.output))

    run_parser = subparsers.add_parser(
        "run", help="Collect evidence and run available analysis/report stages"
    )
    run_parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for all artifacts",
    )
    run_parser.set_defaults(func=lambda args: run(args.output))

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        _print_result(args.func(args))
    except AuditError as exc:
        _print_result({"error": exc.code, "message": exc.message})
        return 1
    except OSError as exc:
        _print_result({"error": "io_error", "message": str(exc)})
        return 1
    return 0
