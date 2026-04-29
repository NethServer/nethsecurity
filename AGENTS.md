# AGENTS.md

## Project Overview

**NethSecurity** is an OpenWrt-based Linux firewall, built inside a rootless Podman container. Versions: OpenWrt `v24.10.5`, NethSecurity `8.7.2` (from `build.conf.example`).

---

## Build System

**Do not commit `build.conf`** — it is git-ignored. Copy from `build.conf.example` and populate locally.

**For build verification, prefer GitHub Actions** — inspect CI status and logs via the GitHub MCP server (`github-mcp-server-actions_list`, `github-mcp-server-actions_get`, `github-mcp-server-get_job_logs`). Only run a local build if explicitly required.

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

**Docs preview** (only when a local docs build is explicitly needed):
```bash
cd docs
bundle config set --local path 'vendor/bundle'
bundle install
./prepare.sh && bundle exec jekyll serve
```

---

## High-level Architecture

- `build-nethsec.sh` builds a Podman-based builder image from `builder/Containerfile`, clones OpenWrt, injects the local `packages/` tree as the `nethsecurity` feed, copies `config/`, `files/`, and `patches/`, then runs the OpenWrt build.
- `builder/configure-build.sh` assembles the final `.config` by concatenating every `config/*.conf` fragment, appending `config/targets/<target>.conf`, writing version metadata, and running `make defconfig`.
- `builder/apply-patches.sh` strips the `patches/` prefix and applies each patch into the matching upstream source directory.
- `files/` is the rootfs overlay for the final image. `files/etc/uci-defaults` holds first-boot defaults.
- Runtime web stack: **nginx** serves `ns-ui` from `/www-ns` and proxies `/api/` → **ns-api-server** on `127.0.0.1:8090`; `ns-api-server` handles auth/JWT and forwards calls to ubus/rpcd handlers.
- Many local packages are thin wrappers around upstream code. When changing behavior in one of those areas, inspect the matching upstream repo first and treat the local package as integration glue.

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

**ACL files:**
- Paired with each handler: `ns.NAME.json` installed to `/usr/share/rpcd/acl.d/`.
- Consistently leave `"write": {}` empty and declare ubus permissions under `"read": { "ubus": ... }`.

**UCI conventions:**
- Zones: `ns_<zonename>` (e.g., `ns_lan`, `ns_guest`).
- Firewall rule IDs: prefix `ns_` (e.g., `ns_206325d3`); system rules flagged `system_rule: true`.

---

## Testing

**No automated test suite.** Testing is manual on a live device:

```bash
# Via api-cli (default creds: root / Nethesis,1234):
api-cli ns.dashboard system-info
api-cli ns.dashboard counter --data '{"service":"hosts"}'
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
| [openwrt/openwrt](https://github.com/openwrt/openwrt) | OpenWrt base |
| [openwrt/packages](https://github.com/openwrt/packages) | OpenWrt package repository |
| [NethServer/nethsecurity-controller](https://github.com/NethServer/nethsecurity-controller) | Firewall registration, VPN/proxy routing, and how the firewall connects to and calls the controller. |
| [NethServer/ns8-nethsecurity-controller](https://github.com/NethServer/ns8-nethsecurity-controller) | NS8 deployment details, extra Loki/Grafana/Prometheus/WebSSH components, and controller packaging. |

**NethServer shared handbook** (follow for all contributions):

| Document | When to consult |
|---|---|
| [Commit messages](https://github.com/NethServer/dev/blob/master/handbook/commit_messages.md) | Before writing commits; follow Conventional Commits and issue-reference guidance. |
| [Pull requests](https://github.com/NethServer/dev/blob/master/handbook/pull_requests.md) | Before opening or updating PRs. |
| [Best practices](https://github.com/NethServer/dev/blob/master/handbook/best_practices.md) | Before larger implementation decisions or security-sensitive changes. |
| [Issues](https://github.com/NethServer/dev/blob/master/handbook/issues.md) | Before opening, classifying, or triaging new work. |

---

## Key Conventions

- Before changing behavior in UI/API/monitoring/controller code, inspect the matching upstream repo; the local package usually just wires that code into the OpenWrt image.
- When changing behavior, update the developer documentation under `docs/` in the same change.
- When changing user-facing behavior or adding a new feature, check whether the frontend needs updates so the UI/API contract stays aligned, and update the administrator manual in `nethsecurity-docs` as part of the change.
- When changing current behavior or configuration, verify the change against both the firewall system and the controller so upgrades stay seamless and regressions are avoided on both sides.
- When implementing new things, check [`system_requirements.rst`](https://github.com/NethServer/nethsecurity-docs/blob/main/system_requirements.rst) to keep the result suitable for older x86 hardware.
- Avoid growing the built image unnecessarily; if size increases are unavoidable, evaluate alternatives before committing to the change.
- Use live repository files as the source of truth when docs disagree with the code.
- Keep `AGENTS.md` updated alongside code changes.
