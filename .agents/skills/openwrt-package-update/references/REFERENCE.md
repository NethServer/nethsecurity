# Reference: openwrt-package-update Skill

## fetch-upstream.sh Script Details

### Purpose
The `fetch-upstream.sh` script automates fetching upstream package code and generating a diff for manual review.

### Workflow

1. **Argument parsing**: Takes `<openwrt-tag|HEAD>`, `<package-name>`, `<local-package-dir>`
2. **Fetch feeds.conf.default**: If a tag is provided, curl the feeds.conf.default from that OpenWrt release
3. **Extract hash**: Parse the `src-git packages` line to find the pinned commit hash after `^`
4. **Clone/update feed**: Clone the GitHub mirror of openwrt/packages or update an existing clone
5. **Checkout hash**: `git checkout` the extracted hash (or HEAD if no hash provided)
6. **Locate package**: `find` the package directory (up to 3 levels deep)
7. **Generate diff**: Run `diff -ru` between upstream and local

### Output Format

```
=== Step 1: Fetching feeds.conf.default from OpenWrt <tag> ===
...
=== Step 2: Cloning/updating packages feed to <path> ===
...
=== Step 3: Locating package '<name>' in upstream feed ===
...
=== Step 4: Comparing upstream vs local package ===
...
--- Diff (upstream vs local) ---
[diff output]
...
=== Diff Summary ===
...
```

### Exit Codes
- `0`: Success
- `1`: Missing arguments, network error, or package not found

### Asset Management

The script clones the packages feed into `.agents/skills/openwrt-package-update/assets/packages/` which is added to `.gitignore`. This folder:
- Grows over time as more packages are cloned
- Can be manually deleted to save space (script will re-clone on next run)
- Is not committed to git
- Is safe to delete between sessions

### Network Requirements

The script needs:
- `curl` to fetch feeds.conf.default from GitHub
- `git` to clone and checkout the packages repository
- Network access to github.com (both GitHub CDN and Git protocol)

Firewall/corporate proxy rules should allow:
- `https://raw.githubusercontent.com/openwrt/openwrt/...`
- `https://github.com/openwrt/packages.git` (or git:// protocol)

## OpenWrt feeds.conf.default Format

The feeds.conf.default file lists the official feeds:

```
src-git packages https://git.openwrt.org/feed/packages.git^<commit-hash>
src-git luci https://git.openwrt.org/project/luci.git^<commit-hash>
...
```

Each line format:
- `src-git` — source control type (Git)
- `<name>` — feed name (e.g., `packages`, `luci`)
- `<url>` — Git repository URL
- `^<hash>` — (optional) pinned commit hash

The hash ensures reproducible builds by locking to a specific point in time.

## Diff Interpretation Guide

When reviewing the script's diff output:

### Common diff symbols:
- `---` — upstream file
- `+++` — local file
- `@@` — hunk header showing line numbers
- `-` (red) — line removed in local (upstream has it, you removed it)
- `+` (green) — line added in local (you added this, upstream doesn't have it)

### Example: Local customization

```diff
--- a/files/adblock.sh
+++ b/files/adblock.sh
@@ -10,6 +10,8 @@
 UPSTREAM_VERSION="4.1.5"
 
 # Initialize DNS backend
+# NethSecurity: Force dnsmasq backend
+DNS_BACKEND="dnsmasq"
 init_dns_backend() {
```

Here:
- Upstream has no hardcoded `DNS_BACKEND`
- Local (your fork) forces `dnsmasq`
- This is a **local customization** to preserve

### Example: Pure upstream change

```diff
--- a/files/adblock.sh
+++ b/files/adblock.sh
@@ -234,6 +234,8 @@
     log "Error: Invalid source URL"
     return 1
   fi
+  # Upstream fix: sanitize URL before processing
+  sanitize_url "$source_url"
   process_source "$source_url"
```

Here:
- Upstream added a sanitization step
- Neither the old nor new version is in your local file
- This is a **pure upstream improvement** to adopt

## Git Workflow for Patches

If your package has patches in `patches/feeds/packages/`:

### Understand the current patch
```bash
cd assets/packages/<package-name>
git log --oneline -5  # See recent changes
git show HEAD  # See the latest change
cat /path/to/your/patches/feeds/packages/*-<pkg>.patch  # Your patch
```

### Check if patch still applies
```bash
cd assets/packages/<package-name>
git apply --check /path/to/your/patch.patch
```

### Regenerate patch if needed
```bash
cd assets/packages/<package-name>
# Make your changes to files
git diff > /tmp/regenerated.patch
# Copy to repo
cp /tmp/regenerated.patch /path/to/patches/feeds/packages/
```

## Decision Tree for Categorizing Diffs

```
For each hunk in the diff:

1. Is this hunk in a file you modified locally?
   NO → Category A (pure upstream, safe to apply)
   YES → go to 2

2. Does this hunk match a specific customization documented in README.md or comments?
   YES → Category B (intentional customization, preserve)
   NO → go to 3

3. Does this hunk conflict with your customization (same lines touched)?
   YES → Category C (conflict, needs manual merge)
   NO → Category B (you customized different parts, keep both)
```

## Example: Updating adblock 4.1.5 → 4.5.5

**Preparation:**
```bash
scripts/fetch-upstream.sh HEAD adblock ../../../packages/adblock
```

**Review output:**
- Makefile version bumped from 4.1.5 to 4.5.5 (upstream)
- New categories in `adblock.categories` (upstream)
- New sources in `adblock.sources` (upstream)
- Custom DNS backend forcing in `adblock.sh` (local)
- Custom email notification logic in `adblock.sh` (local)

**Categorization:**
- Makefile version: Category A (pure upstream) → adopt
- New categories: Category A → adopt
- New sources: Category A → adopt
- Custom DNS backend: Category B → preserve
- Custom email: Category B → preserve

**Actions:**
1. Copy upstream Makefile, update locally to preserve DNS backend forcing
2. Copy upstream categories file
3. Copy upstream sources file
4. Merge adblock.sh: take upstream as base, reapply the two local customizations
5. Update Makefile PKG_VERSION=4.5.5, PKG_RELEASE=1
6. Re-run script to verify remaining diffs are just your customizations

## Troubleshooting

### Script fails to clone the feed
**Cause:** Network connectivity or git configuration issue
**Solution:** Verify git works: `git clone https://github.com/openwrt/packages.git /tmp/test`

### Script can't find the package
**Cause:** Package name doesn't match directory name, or doesn't exist in that release
**Solution:** Manually browse the assets folder: `ls assets/packages/net/ | grep <name>`

### Diff is huge (thousands of lines)
**Cause:** You're comparing very different versions
**Solution:** 
- Try an intermediate version first
- Use `diff -r --exclude-from=.diffignore` to skip binary files
- Split review into categories (Makefile, scripts, configs)

### Cloned repo is getting too large
**Cause:** Multiple runs accumulate git history
**Solution:** Delete the assets folder: `rm -rf assets/packages/`, script will re-clone on next run
