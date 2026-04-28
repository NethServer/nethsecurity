---
name: bump-package-version
description: Analyze git history between two commits and determine semantic version bumps for NethSecurity packages. Reads commits and diffs to classify changes as major, minor, patch, or release-only. Use during release preparation to identify which packages need version updates.
compatibility: Requires Python 3.11+ and git. Designed for NethSecurity package structure.
metadata:
  domain: nethsecurity-versioning
  type: release-management
---

## What I do

- Prompt you to select a starting commit from recent git history
- Gather all commits and diffs affecting `ns-*` packages between that commit and HEAD
- Analyze each package's changes and classify them by semantic version impact
- Present recommendations for version and release bumps
- Output dry-run summary (no files modified)

## When to use me

Use this skill when you are:
- Preparing a release and need to bump package versions
- Creating a release tag and want automated version classification
- Reviewing what changed across multiple packages since a specific commit
- Deciding which packages warrant a version bump vs. just a release increment

## How it works

1. **Data gathering**: `scripts/bump.py` runs `git log` and `git diff` to collect commits and changes per package
2. **User selection**: Pick a starting commit SHA (the script lists recent commits)
3. **Analysis**: Agent reads full diffs and commit messages to classify each package
4. **Classification rules**:
   - **major**: Breaking API changes, removed methods/params, incompatible behavior
   - **minor**: New features, new API methods/params, backward-compatible additions
   - **patch**: Bug fixes, refactors, dependency updates, docs
   - **release**: Only OpenWrt packaging files touched (Makefile, config/, patches/) without logic changes
5. **Output**: Dry-run summary table showing current vs. recommended versions

## Running the script

```bash
python3 scripts/bump.py
```

Script outputs:
- List of recent commits
- Prompt for starting commit SHA
- Per-package analysis blocks with commits, files, and full diff
- Agent classifies changes based on diff content

## Version bump logic

| Category | Applies when | Effect |
|---|---|---|
| **major** | Breaking API, removed endpoints, incompatible changes | PKG_VERSION major +1, minor/patch to 0, PKG_RELEASE to 1 |
| **minor** | New features, new endpoints/params, backward-compatible | PKG_VERSION minor +1, patch to 0, PKG_RELEASE to 1 |
| **patch** | Bug fixes, refactors, dependency updates, docs | PKG_VERSION patch +1, PKG_RELEASE to 1 |
| **release** | Only packaging files (Makefile, config/, patches/) | PKG_RELEASE +1, PKG_VERSION unchanged |

If a package has mixed changes, the highest-severity bump "wins".

## Notes

- Script outputs data in parseable format for agent analysis
- No files are modified; output is dry-run only
- Agent applies version bump rules based on full diff content

## SPDX Header

The `bump.py` script includes the required Nethesis copyright header.
