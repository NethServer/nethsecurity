---
name: openwrt-package-update
description: >
  Use when updating any forked OpenWrt package in a NethSecurity workspace from
  the upstream openwrt/packages feed. Covers the full update cycle: version bump,
  merging upstream file changes, updating dependent ns-api handlers and migration
  scripts, UCI overlay defaults, and correlated documentation. Triggers on updating
  a package by name (adblock, mwan3, banip, rsyslog, snort3, keepalived,
  python-jinja2, python-semver, and similar forks), syncing with upstream, or any
  request to align a local package fork with openwrt/packages — even if upstream
  is not mentioned explicitly.
compatibility: Requires git and curl. Works in a NethSecurity workspace with build.conf.defaults present.
metadata:
  domain: nethsecurity-packages
  type: package-update
allowed-tools: Bash(git:*) Bash(curl:*) Bash(diff:*) Bash(tar:*) Bash(grep:*) Bash(sed:*) Bash(awk:*) Read Write
---

## What I do

Update a forked upstream OpenWrt package from the openwrt/packages feed. Auto-discovers the package path, compares the current version against the upstream target, extracts snapshots for comparison, applies upstream changes, propagates impact to ns-api handlers and migration scripts, and updates correlated documentation.

## Quick start

1. **Setup**: `bash scripts/setup-package.sh <package-name>` — auto-discovers upstream path, finds version commits, extracts old/new snapshots into `assets/<name>_old/` and `assets/<name>_new/`
2. **Compare**: `bash scripts/diff-package.sh <package-name>` — shows what changed upstream
3. **Merge**: Read both snapshots, apply upstream changes to local files in `packages/<package-name>/`; update PKG_VERSION and PKG_RELEASE in the Makefile
4. **Cross-package**: Grep for any changed config keys or function names in ns-api, migration scripts, and files/ overlay; update as needed
5. **Documentation**: Update `docs/` and `packages/ns-api/README.md` if user-facing behavior changed
6. **Verify**: Run `ruff check` on any changed Python files; build the package inside the container

For per-step detail on any of the above, read [references/WORKFLOW.md](references/WORKFLOW.md).

## How it works

The skill uses three helper scripts:

- **get-target-commit.sh** — reads `build.conf.defaults` for OWRT_VERSION, fetches `feeds.conf.default` from that tag, extracts the openwrt/packages commit hash
- **setup-package.sh** — auto-discovers package upstream path, uses git pickaxe to find the commit matching current PKG_VERSION then PKG_RELEASE, clones/fetches openwrt/packages bare repo into `assets/.openwrt-packages-repo/` (persistent cache), extracts both versions into named snapshots
- **diff-package.sh** — convenience wrapper: `diff -rN assets/<name>_old/ assets/<name>_new/`

## Snapshot structure

Each snapshot has the exact upstream package files at root level:
```
assets/adblock_old/
├── Makefile
├── files/
│   ├── adblock.sh
│   ├── adblock.init
│   ├── adblock.conf
│   └── ...
```

## Edge cases

- **mwan3**: Deep fork — apply upstream changes conservatively, one by one
- **snort3**: Has local patches — verify patches still apply after update
- **Version not found**: If script fails, local version is very old; check `assets/.openwrt-packages-repo/` git history
- **Empty diff**: Versions match; only update PKG_VERSION/PKG_RELEASE if tracking newer release
