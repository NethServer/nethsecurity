# Detailed Workflow: Updating Upstream Packages

## 1. Identify the package

Confirm the package exists and is in scope. Read `packages/<package-name>/Makefile` to understand the current version:
- Note PKG_VERSION and PKG_RELEASE
- Check if `packages/<package-name>/patches/` exists (indicates local patches)
- Scan `files/` directory to understand what configuration files and scripts are included

## 2. Setup snapshots

Run the setup script:
```bash
bash scripts/setup-package.sh <package-name>
```

This script will:
- Auto-discover the upstream path in openwrt/packages (e.g., `net/adblock`)
- Use git pickaxe to find the commit that introduced the current PKG_VERSION
- Then find the commit that set the current PKG_RELEASE
- Extract both versions into `assets/<package-name>_old/` and `assets/<package-name>_new/`
- Output summary with commit hashes and paths

## 3. Compare and classify

Examine both snapshots using your file reading tools. Run:
```bash
bash scripts/diff-package.sh <package-name>
```

Classify each change:
- **Makefile**: version bumps, new dependencies, build flags
- **files/*.sh** / **files/*.init**: behavioral changes to shell scripts
- **files/*.conf**: UCI configuration schema changes (new/removed/renamed options)
- **files/*.sources**, **files/*.categories**, data files: content-only updates
- **New files** added / **files removed**

## 4. Apply upstream changes

For each changed file:
- If the local copy is identical to old version or has no NethSecurity-specific changes → take upstream as-is
- If the local copy has customizations → merge carefully:
  - Use the diff tool to understand what changed upstream
  - Manually integrate the upstream changes into the local file
  - Preserve any NethSecurity-specific logic or configuration
  
Always:
- Update PKG_VERSION and PKG_RELEASE in `packages/<package-name>/Makefile`
- If `packages/<package-name>/patches/` exists, re-verify each patch still applies cleanly with the new version
- Test build: `make package/feeds/nethsecurity/<name>/compile V=sc` inside the build container

## 5. Cross-package impact detection

For each changed UCI option name, function name, or config key in the diff:
- Grep the workspace for references:
  ```bash
  grep -r "<changed-key>" packages/ files/ docs/ --include="*.py" --include="*.sh" --include="*.json" --include="*.conf" --include="*.md"
  ```
- Grep `packages/ns-migration/` for migration scripts that reference old option names
- Grep `packages/ns-api/` for API scripts that read/write this package's configuration
- Present findings to user before making changes

## 6. Apply cross-package fixes (after user confirmation)

Update affected files:
- **ns-api scripts**: if UCI schema changed, update handlers in `packages/ns-api/files/ns.<name>` 
- **Migration scripts**: if old config options are removed, add migration logic to `packages/ns-migration/files/`
- **files/ overlay defaults**: if default values changed, update `files/etc/uci-defaults/` or `files/etc/config/`
- **Documentation**: update `docs/` if user-facing behavior changed

## Edge cases

**mwan3**: This is a deep fork with significant local modifications. Apply upstream changes one by one, preferring manual review for any behavioral change. Verify the result against firewall rules and failover behavior.

**snort3, openvpn-easy-rsa**: These packages have local patches (see `packages/<name>/patches/`). After updating upstream files, re-run `quilt refresh` or regenerate patches. If patches no longer apply cleanly, update them to match the new upstream.

**Empty diff**: If upstream and local versions are the same, only update PKG_VERSION/PKG_RELEASE in the Makefile if tracking a newer release. Otherwise, the package is up-to-date.

**Version not found**: If the script cannot find the current PKG_VERSION in upstream history, it means the local version is very old or from a different source. Check git history in the bare repo (`assets/.openwrt-packages-repo/`) to understand the version trajectory.

## Helpful commands

Inside the skill directory:
- `bash scripts/get-target-commit.sh` — print the target packages feed commit hash from feeds.conf.default
- `bash scripts/setup-package.sh <name>` — extract old/new snapshots
- `bash scripts/diff-package.sh <name>` — show recursive diff
- `find assets/<name>_old/ -type f` — list all files in old snapshot
- `cat assets/<name>_old/Makefile | grep PKG_` — check old version details
