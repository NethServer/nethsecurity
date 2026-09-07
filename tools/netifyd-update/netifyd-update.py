#!/usr/bin/env python3

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

import argparse
import hashlib
import shutil
import subprocess
import sys
import requests
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_WORK_DIR = SCRIPT_DIR / "work"
DEFAULT_DIST_DIR = SCRIPT_DIR / "dist"
NETIFYD_PKG_DIR = SCRIPT_DIR.parent.parent / "packages" / "netifyd"
DIST_MK = NETIFYD_PKG_DIR / "netify-dist.mk"

SOURCES: dict[str, str] = {
    "x86": "https://download.netify.ai/5/openwrt/25.12/x86/index.json",
}

# maps a SOURCES key to the OpenWrt $(ARCH) value used by the Makefile
MAKEFILE_ARCH: dict[str, str] = {"x86": "x86_64", "aarch64": "aarch64"}

PACKAGES: list[str] = [
    "netify-plm",
    "netify-proc-aggregator",
    "netify-proc-core",
    "netify-proc-flow-actions",
    "netify-sink-http",
    "netify-sink-log",
    "netifyd",
]

# maps an apk package to the extracted files whose name and sha256 feed the matching
# Makefile variables; netifyd ships both the binary and libnetifyd.so
DIST_TARGETS: dict[str, list[tuple[str, str]]] = {
    "netifyd": [("usr/sbin/netifyd", "NETIFYD"), ("usr/lib/libnetifyd.so.*", "LIBNETIFYD")],
    "netify-plm": [("usr/lib/libnetify-plm.so.*", "PLM")],
    "netify-proc-aggregator": [("usr/lib/libnetify-proc-aggregator.so.*", "PROC_AGGREGATOR")],
    "netify-proc-core": [("usr/lib/libnetify-proc-core.so.*", "PROC_CORE")],
    "netify-proc-flow-actions": [("usr/lib/libnetify-proc-flow-actions.so.*", "PROC_FLOW_ACTIONS")],
    "netify-sink-http": [("usr/lib/libnetify-sink-http.so.*", "SINK_HTTP")],
    "netify-sink-log": [("usr/lib/libnetify-sink-log.so.*", "SINK_LOG")],
}

# flattened, stable order of the variable suffixes for netify-dist.mk
DIST_SUFFIX_ORDER: list[str] = [suffix for targets in DIST_TARGETS.values() for _, suffix in targets]

# collected field -> Makefile variable infix, in emission order
FIELD_ORDER: list[tuple[str, str]] = [
    ("file", "FILE"),
    ("soname", "SONAME"),
    ("link", "LINK"),
    ("hash", "HASH"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    update = subparsers.add_parser("update", help="download the upstream apks, regenerate netify-dist.mk and dist/")
    update.add_argument("--force", action="store_true", help="remove existing work and dist directories and redo")

    return parser.parse_args()


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def download_file(url: str, dest: Path) -> None:
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"Downloaded {dest.name} to {dest.parent}")


def extract_apk(apk_path: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    print(f"Extracting {apk_path.name} to {dest_dir}")
    subprocess.run(["apk", "extract", "--allow-untrusted", "--destination", str(dest_dir), str(apk_path)], check=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def symlinks_to(target: Path) -> list[str]:
    """Names of the sibling symlinks pointing at target, shortest first."""
    resolved = target.resolve()
    names = [p.name for p in target.parent.iterdir() if p.is_symlink() and p.resolve() == resolved]
    return sorted(names, key=len)


def collect_targets(
    package: str,
    extract_dir: Path,
    dist_dir: Path,
    makefile_arch: str,
    entries: dict[str, dict[str, dict]],
) -> None:
    for pattern, suffix in DIST_TARGETS.get(package, []):
        matches = [p for p in extract_dir.glob(pattern) if not p.is_symlink()]
        if len(matches) != 1:
            fail(f"expected exactly one file matching {pattern} in {extract_dir}, found {len(matches)}")

        target = matches[0]
        fields = {"file": target.name, "hash": sha256_file(target)}

        # shared objects ship an unversioned and a soname symlink, plain binaries ship none
        links = symlinks_to(target)
        if links:
            if len(links) != 2:
                fail(f"expected exactly two symlinks to {target.name} in {target.parent}, found {len(links)}")
            fields["link"], fields["soname"] = links

        entries.setdefault(suffix, {})[makefile_arch] = fields

        # mirror the file under the layout the Makefile downloads from; the symlinks are
        # recreated at install time, only the real files get published
        published = dist_dir / target.relative_to(extract_dir)
        published.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, published)


def warn_on_diverging_filenames(entries: dict[str, dict[str, dict]], arches: list[str]) -> None:
    for suffix in DIST_SUFFIX_ORDER:
        names = {arch: entries[suffix][arch]["file"] for arch in arches}
        if len(set(names.values())) > 1:
            detail = " ".join(f"{arch}={name}" for arch, name in names.items())
            warn(f"{suffix} filename differs across arches, upstream feeds are not aligned: {detail}")


def write_dist_mk(entries: dict[str, dict[str, dict]], arches: list[str]) -> None:
    lines = [
        "#",
        "# Copyright (C) 2026 Nethesis S.r.l.",
        "# SPDX-License-Identifier: GPL-2.0-only",
        "#",
        "",
        "# generated by tools/netifyd-update/netifyd-update.py, do not edit by hand",
        "",
    ]
    for i, arch in enumerate(arches):
        keyword = "ifeq" if i == 0 else "else ifeq"
        lines.append(f"{keyword} ($(ARCH),{arch})")
        for suffix in DIST_SUFFIX_ORDER:
            fields = entries[suffix][arch]
            for field, infix in FIELD_ORDER:
                if field in fields:
                    lines.append(f"NETIFYD_{infix}_{suffix}:={fields[field]}")
    # the remaining branch covers the metadata scan, which runs with DUMP=1 and therefore
    # without .config, leaving $(ARCH) empty, and any arch the package is not selectable
    # on; the Download macro rejects an empty FILE either way, so hand it the unversioned
    # names as placeholders, nothing gets fetched in those cases
    lines.append("else")
    lines.append("# metadata scan (DUMP=1, no .config) or an arch we ship no binaries for:")
    lines.append("# placeholders only, netifyd is not selectable there and nothing is downloaded")
    for suffix in DIST_SUFFIX_ORDER:
        fields = entries[suffix][arches[0]]
        placeholder = fields.get("link", fields["file"])
        lines.append(f"NETIFYD_FILE_{suffix}:={placeholder}")
        if "soname" in fields:
            lines.append(f"NETIFYD_SONAME_{suffix}:={placeholder}")
            lines.append(f"NETIFYD_LINK_{suffix}:={placeholder}")
    lines.append("endif")
    lines.append("")

    DIST_MK.write_text("\n".join(lines))
    print(f"Wrote {DIST_MK}")


def run_update(args: argparse.Namespace) -> None:
    if shutil.which("apk") is None:
        fail("apk-tools is required: install it with 'dnf install apk-tools' or 'apt-get install apk-tools'")

    # bail out if a previous run's directories are still there
    for stale in (DEFAULT_WORK_DIR, DEFAULT_DIST_DIR):
        if stale.exists():
            if not args.force:
                fail(f"{stale} already exists, use --force to remove it and redo")
            shutil.rmtree(stale)

    entries: dict[str, dict[str, dict]] = {}
    makefile_arches: list[str] = []

    for arch, index_url in SOURCES.items():
        makefile_arch = MAKEFILE_ARCH[arch]
        makefile_arches.append(makefile_arch)

        # fetch the list of available packages
        with requests.get(index_url) as response:
            response.raise_for_status()
            index = response.json()

        # generate urls and directories to download the packages
        base_url = index_url.rsplit("/", 1)[0]
        apk_dir = DEFAULT_WORK_DIR / arch / "apk"
        apk_dir.mkdir(parents=True, exist_ok=True)
        extract_dir = DEFAULT_WORK_DIR / arch / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        dist_dir = DEFAULT_DIST_DIR / makefile_arch
        dist_dir.mkdir(parents=True, exist_ok=True)

        # download only the used packages
        for package, pkg_version in index.get("packages", {}).items():
            if package not in PACKAGES:
                continue
            filename = f"{package}-{pkg_version}.apk"
            download_file(f"{base_url}/{filename}", apk_dir / filename)
            extract_apk(apk_dir / filename, extract_dir)
            collect_targets(package, extract_dir, dist_dir, makefile_arch, entries)

    missing = [suffix for suffix in DIST_SUFFIX_ORDER if len(entries.get(suffix, {})) != len(makefile_arches)]
    if missing:
        fail(f"missing entries for {', '.join(missing)}, check the upstream indexes")

    warn_on_diverging_filenames(entries, makefile_arches)
    write_dist_mk(entries, makefile_arches)

    print(f"Upload tree ready in {DEFAULT_DIST_DIR}, publish it manually to the netifyd-dist mirror")


def main() -> None:
    args = parse_args()
    run_update(args)


if __name__ == "__main__":
    main()
