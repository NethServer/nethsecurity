# AGENTS.md

## Project Overview

**NethSecurity** is an OpenWrt-based Linux firewall, built inside a rootless Podman container. Versions: OpenWrt `v24.10.5`, NethSecurity `8.7.2` (from `build.conf.example`).

---

## Build System

**Do not commit `build.conf`** — it is git-ignored. Copy from `build.conf.example` and populate locally.

```bash
# Full image build
./build-nethsec.sh

# Interactive shell inside the build container
./build-nethsec.sh bash

# Run single package compilation
# (Inside container shell:)
make package/feeds/nethsecurity/ns-<name>/{download,compile} V=sc

# Interactive menuconfig
./build-nethsec.sh make menuconfig
```

Output: `bin/` (image + packages) and `build-logs/`.

**Build system is pure OpenWrt `make`** — no npm, pip, go build, or other language-specific tooling. All derivation runs inside the container.

---

## Repository Structure

| Directory | Content |
|---|---|
| `packages/` | Custom OpenWrt feed; 37 `ns-*` packages |
| `config/` | Diffconfig fragments per feature; `config/targets/<arch>.conf` for arch-specific config |
| `files/` | Filesystem overlay copied verbatim into image |
| `patches/` | Patches applied to upstream OpenWrt feeds |
| `.github/workflows/` | CI/CD (build-image, release-stable, cleanup, docs, etc.) |

---

## Package Conventions

- **All custom packages use `ns-` prefix** (e.g., `ns-firewall`, `ns-api`).
- Set `CATEGORY:=NethSecurity` and `SECTION:=base` in Makefile.
- Use `PKGARCH:=all` for architecture-independent packages (pure Python, shell scripts, etc.).
- **Do not set `PKG_SOURCE_URL`** when package code lives in this repo. Set it only when fetching from external GitHub releases.
- To add a package to the image, create a corresponding `config/<feature>.conf` fragment that enables it at build time.
- Renovate manages external package versions via magic comments in Makefiles: `# renovate: datasource=github-tags depName=Org/Repo`

---

## ns-api (Python3 RPCD Scripts)

APIs are Python 3 scripts placed at `/usr/libexec/rpcd/ns.<name>` on the device.

**Protocol:**
- Called with `list` argument → print JSON listing all methods and parameter schemas.
- Called with `call <method>` → read JSON from stdin, write JSON to stdout.
- **APIs must not commit UCI changes** — callers invoke `ns.commit` separately.

**Error format:**
```json
{ "error": "snake_case_error_code" }
```

**Validation error format:**
```json
{ "validation": { "errors": [{ "parameter": "field", "message": "code", "value": "..." }] } }
```

**Hooks:**
- Pre-commit hooks: `/usr/libexec/ns-api/pre-commit/`
- Post-commit hooks: `/usr/libexec/ns-api/post-commit/`
- Hooks run as part of `ns.commit commit` but do not abort on failure; errors returned in response JSON.

**UCI conventions:**
- Zones: `ns_<zonename>` (e.g., `ns_lan`, `ns_guest`).
- Firewall rule IDs: prefix `ns_` (e.g., `ns_206325d3`); system rules flagged `system_rule: true`.

---

## Testing

**No automated test suite.** Testing is manual on a live device:

```bash
# Via api-cli (default creds: root / Nethesis,1234):
api-cli ns.dashboard system-info
api-cli ns.firewall list-forward-rules

# Via ubus:
ubus call ns.firewall list-zones
```

For UI development against a live device, enable CORS by changing `/etc/init.d/ns-api-server`:
```
GIN_MODE=debug  # (instead of release)
# Then restart: /etc/init.d/ns-api-server restart
```

---

## Release & CI

| Trigger | Channel | Version |
|---|---|---|
| Push to `main` | `dev` | `<base>-dev+<hash>.<timestamp>` |
| Tag push | `stable` | tag value |
| PR branch | branch-named | `<base>-<branch>+<hash>` |

**Packages-only stable release:**
1. Bump `PKG_VERSION` or `PKG_RELEASE` in `packages/<name>/Makefile`.
2. Merge to `main`.
3. Trigger [Release stable packages](https://github.com/NethServer/nethsecurity/actions/workflows/release-stable.yml) workflow manually to sync `dev` → `stable`.

**Build volumes** (persistent, deleted weekly): `nethsecurity_builder_${OWRT_VERSION}_{build,staging,cache,downloads,dl}`.

---

## License Header

Every Nethesis-authored source file must include:

```
#
# Copyright (C) <YEAR> Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#
```

This applies to all source files: Python scripts, shell scripts, Makefiles, Go code, and any other authored source.

---

## Code Quality

**Python linting and formatting:** New Python files must pass `ruff check` and `ruff format --check`. See `ruff.toml` for configuration.

```bash
ruff check packages/ns-api/files/my_script.py
ruff format --check packages/ns-api/files/my_script.py
```

Existing Python files (listed in `ruff.toml` under `extend-exclude`) are grandfathered in and exempt from checking. Fix them incrementally as desired.

---

## API Documentation

**After any API change, update `packages/ns-api/README.md`** to reflect new or modified methods and schemas. The README is the canonical API reference for all `ns.*` methods.

---

## Key External Repositories

| Repo | Purpose |
|---|---|
| [NethServer/nethsecurity-api](https://github.com/NethServer/nethsecurity-api) | Go API server (ns-api-server); handles JWT auth, 2FA, proxies to ubus/rpcd |
| [NethServer/python3-nethsec](https://github.com/NethServer/python3-nethsec) | Python utility library for APIs; used by all Python API scripts |
| [NethServer/nethsecurity-ui](https://github.com/NethServer/nethsecurity-ui) | Vue 3 + Tailwind CSS management UI (standalone + controller modes); built as `ns-ui` package |
| [NethServer/nethsecurity-monitoring](https://github.com/NethServer/nethsecurity-monitoring) | Go monitoring tools (ns-flows); reads netifyd flows, exposes REST API on localhost:8080 |
| [openwrt/openwrt](https://github.com/openwrt/openwrt) | OpenWrt base (pinned to `v24.10.5`) |
