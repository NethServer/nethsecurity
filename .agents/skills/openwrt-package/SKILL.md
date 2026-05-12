---
name: openwrt-package
description: Create or modify an OpenWrt ns-* package including Makefile, config fragments, and upstream patches. Use when building new packages for NethSecurity, managing package dependencies, patching upstream feeds, or modifying build configurations. Covers naming conventions, required Makefile fields, architecture selection, external version management, and patch workflows.
compatibility: Works with OpenCode and other Agent Skills-compatible tools. Requires familiarity with OpenWrt build system and Makefile syntax.
metadata:
  domain: nethsecurity-packages
  type: package-development
---

## What I do

- Help create or modify `ns-*` packages in the `packages/` directory
- Write correct Makefile with required fields and conventions
- Create config diffconfig fragments to enable packages in the image
- Generate and apply patches for upstream OpenWrt packages
- Manage external package versions via Renovate

## When to use me

Use this skill when you are:
- Creating a new `ns-*` package from scratch
- Modifying an existing package's Makefile
- Adding a package to the image via a config fragment
- Patching an upstream OpenWrt feed package
- Updating external package versions

## Naming Convention

**All packages must use the `ns-` prefix.** Examples:
- `ns-firewall`
- `ns-api`
- `ns-ui`
- `ns-monitoring`
- `ns-openvpn`

Do not create packages without this prefix.

## Package Structure

```
packages/ns-myapp/
├── Makefile              # Package build definition
├── README.md             # Optional: package documentation
└── files/                # Optional: files to install on device
    ├── usr/bin/myapp
    ├── etc/config/myapp
    └── ...
```

## Makefile Template

Minimal `packages/ns-myapp/Makefile`:

```makefile
#
# Copyright (C) <YEAR> Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=ns-myapp
PKG_VERSION:=1.0.0
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)

CATEGORY:=NethSecurity
SECTION:=base
PKGARCH:=all
DEPENDS:=+python3

define Package/ns-myapp
  TITLE:=My Application
  DESCRIPTION:=Short description of what ns-myapp does
endef

define Package/ns-myapp/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) ./files/myapp $(1)/usr/bin/
endef

$(eval $(call BuildPackage,ns-myapp))
```

## Required Makefile Fields

| Field | Value | Notes |
|---|---|---|
| `CATEGORY` | `NethSecurity` | Always this value |
| `SECTION` | `base` | Standard for all ns-* packages |
| `PKGARCH` | `all` | Use for pure Python/shell scripts (no binaries) |
| `PKGARCH` | `x86_64` (or target) | Use for compiled binaries or architecture-specific code |

## PKG_SOURCE_URL Convention

**Do NOT set `PKG_SOURCE_URL`** for packages whose code lives in this repo.

**DO set it** only when fetching from an external GitHub release:

```makefile
PKG_SOURCE_URL:=https://github.com/NethServer/ns-myapp/releases/download/v$(PKG_VERSION)/
PKG_SOURCE:=ns-myapp-$(PKG_VERSION).tar.gz
PKG_HASH:=<sha256>
```

## Renovate Version Management

For external packages, use Renovate magic comments to auto-update versions:

```makefile
# renovate: datasource=github-tags depName=NethServer/ns-myapp
PKG_VERSION:=1.0.0
```

Renovate will periodically create PRs when new releases are available.

## Config Fragment

To add the package to the built image, create `config/<feature>.conf`:

```
CONFIG_PACKAGE_ns-myapp=y
CONFIG_PACKAGE_ns-myapp-extra-features=y
```

Build system reads all `config/*.conf` files and merges them to build `.config`.

## Patching Upstream Packages

When modifying upstream OpenWrt feed packages (not packages living in this repo):

1. **Enter the build container**:
   ```bash
   ./build-nethsec.sh bash
   ```

2. **Navigate to the feed package**:
   ```bash
   cd /home/buildbot/openwrt/feeds/packages/net/adblock
   git diff > /tmp/patch.diff
   ```

3. **Create the patch in the repo**:
   ```bash
   mkdir -p patches/feeds/packages
   mv /tmp/patch.diff patches/feeds/packages/100-adblock-changes.patch
   ```

Patches are applied automatically during build via `patches/feeds.conf.default`.

**Naming convention**: `<number>-<package>-<description>.patch` (e.g., `100-adblock-bypass.patch`)

## Single Package Build

Build and test a single package without building the full image:

```bash
# Inside the container
./build-nethsec.sh bash

# Then run
make package/feeds/nethsecurity/ns-myapp/{download,compile} V=sc
```

Output `.ipk` appears at: `bin/packages/x86_64/nethsecurity/ns-myapp_<version>_all.ipk`

## SPDX Header

Every file must include:

```
#
# Copyright (C) <YEAR> Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#
```

This includes shell scripts, Python, Makefiles, and any other source files.

## Code Style

Python files in packages must pass ruff checks:

```bash
ruff check packages/ns-myapp/files/script.py
ruff format --check packages/ns-myapp/files/script.py
```

Existing files are grandfathered; see `ruff.toml` in the repo root for details.

## Testing the Package

After building the `.ipk`:

1. Copy to a live NethSecurity device
2. Install: `apk add ns-myapp_<version>_all.ipk`
3. Test functionality manually
4. Check logs: `logread | grep ns-myapp`

## Example Packages

See real examples in `packages/`:
- `packages/ns-api/` — Python RPCD API scripts
- `packages/ns-firewall/` — Firewall API
- `packages/ns-migration/` — Migration tools
