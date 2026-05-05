---
name: openwrt-package-update
description: Update a forked OpenWrt upstream package to a newer upstream version while preserving local customizations. Use when updating packages like adblock, mwan3, or other non-ns- prefixed upstream packages to newer releases, and when comparing local forks against the canonical OpenWrt packages feed to identify and merge upstream improvements.
license: GPL-2.0-only
compatibility: Requires git, curl, and bash. Works with OpenWrt release tags (v24.10.x, v24.11.x, etc.) and HEAD of the packages feed.
metadata:
  domain: nethsecurity-packages
  type: upstream-package-update
---

## What I do

I help you update forked OpenWrt upstream packages (non-`ns-*` packages) to newer upstream versions while carefully preserving intentional local customizations. I:

1. Fetch the canonical OpenWrt `feeds.conf.default` for a given release tag or the latest HEAD
2. Extract the pinned commit hash for the packages feed
3. Clone or update a local copy of the `openwrt/packages` GitHub mirror
4. Locate the package in the upstream feed
5. Generate a detailed diff showing all differences between upstream and your local fork
6. Guide you through analyzing the diff to identify:
   - Pure upstream improvements to apply
   - Your intentional customizations to preserve
   - Conflicting changes requiring manual adaptation

## When to use me

Use this skill when you are:
- **Updating an existing forked package** to a newer upstream release (e.g., adblock 4.1.5 → 4.5.5)
- **Merging upstream improvements** while keeping local patches and configuration
- **Comparing against multiple OpenWrt releases** to understand what changed between versions
- **Evaluating the scope of local customization** before deciding whether to continue forking or contribute upstream
- **Refreshing patches and adapting them** to newer upstream versions

Do **not** use this skill for:
- Creating entirely new `ns-*` packages (use `openwrt-package` skill instead)
- Patches that should be contributed upstream (this skill is for local forks only)
- Non-OpenWrt packages or custom software

## Workflow

### Step 1: Identify the target package and version

Ask the user:
- **Which package are you updating?** (e.g., `adblock`, `mwan3`, `keepalived`)
- **Which OpenWrt version?** Suggest either:
  - A specific release tag (e.g., `v24.10.5`) — extracts the pinned hash from that release's `feeds.conf.default`
  - `HEAD` — uses the latest upstream version

### Step 2: Run the diff script

From the skill root directory, invoke:

```bash
scripts/fetch-upstream.sh <openwrt-tag|HEAD> <package-name> <path-to-local-package>
```

Examples:
```bash
scripts/fetch-upstream.sh v24.10.5 adblock ../../../packages/adblock
scripts/fetch-upstream.sh HEAD mwan3 /absolute/path/to/packages/mwan3
```

The script will:
- Fetch the feeds.conf.default for the target tag
- Clone the packages feed to `assets/packages/` (gitignored)
- Output a detailed `diff -ru` comparing upstream vs local

### Step 3: Analyze the diff

Review the diff output and classify each change:

#### Category A: Pure Upstream Changes (Safe to apply)
These are bug fixes or features from upstream with no local modification:
- Upstream script improvements, new functions, or bugfixes
- Version bumps in dependencies
- Documentation updates

**Action:** Copy the upstream version directly into the local package.

#### Category B: Intentional Local Customizations (Always preserve)
These are deliberate modifications specific to NethSecurity:
- UCI configuration defaults hardcoded for NethSecurity
- Removal of upstream features not needed in NethSecurity
- Integration with ns-api or other NethSecurity components
- Build system tweaks (PKG_RELEASE bumps for local patches)

**Action:** Keep these changes as-is. They should remain in the diff even after updating.

#### Category C: Upstream Changes That Conflict With Local Customizations (Needs manual work)
These require careful adaptation:
- Upstream modified the same function that you customized
- New upstream feature overlaps with your local workaround
- Upstream changed configuration options you've modified

**Action:** 
- Read both versions carefully
- Decide whether upstream's approach is better (merge it)
- Or adapt upstream's changes to work with your customization
- Test thoroughly after merging

### Step 4: Update the Makefile

Update version information in the package Makefile:

- **`PKG_VERSION`**: Set to the upstream version (e.g., `4.1.5` → `4.5.5`)
- **`PKG_RELEASE`**: Reset to `1` if the upstream version changed, or increment if only applying new local patches

Example transitions:
```makefile
# Before: 4.1.5 with 9 local releases
PKG_VERSION:=4.1.5
PKG_RELEASE:=9

# After updating to 4.5.5:
PKG_VERSION:=4.5.5
PKG_RELEASE:=1

# Or if staying at 4.1.5 but adding a new local patch:
PKG_VERSION:=4.1.5
PKG_RELEASE:=10
```

### Step 5: Apply the changes

For each file in the diff:

1. **If it's Category A (safe upstream change)**: Copy the upstream version directly
2. **If it's Category B (local customization)**: Leave unchanged
3. **If it's Category C (conflict)**: Manually edit to merge both approaches

Common files to check:
- `Makefile` — version and release
- `files/*.sh` — main scripts (often have conflicts)
- `files/*.conf` — configuration templates
- `files/*.init` — OpenWrt init scripts
- `files/README.md` — documentation

### Step 6: Re-run the diff for verification

After making changes, re-run:

```bash
scripts/fetch-upstream.sh <same-openwrt-tag-or-HEAD> <package-name> <path-to-local-package>
```

The diff should now only show your **intentional** customizations. Review it one more time:
- Do all remaining differences make sense?
- Are there any accidental changes that slipped in?
- Should any new upstream code be adopted?

### Step 7: Update documentation (if significant changes)

If the package's behavior changes, update the package's `README.md` or comments to document:
- The version it's based on (e.g., "Based on upstream adblock 4.5.5")
- A summary of local customizations (e.g., "Adds automatic DNS reload on UCI changes")
- Any compatibility notes with the controller or UI

## Common Scenarios

### Scenario: Small upstream bugfix, large local customization

**Situation:** adblock 4.1.5→4.1.6 (just a bugfix), but you've heavily customized the script for NethSecurity.

**Steps:**
1. Run diff with `v24.10.5` tag
2. See the bugfix hunk in `files/adblock.sh`
3. Merge the bugfix into your customized version
4. Update Makefile: `PKG_VERSION:=4.1.6 PKG_RELEASE:=1`
5. Re-run diff — should show only your customizations remain

### Scenario: Multiple version jumps (e.g., 4.1.5 → 4.5.5)

**Situation:** You skipped several releases and want to jump to the latest.

**Steps:**
1. Run diff with `HEAD` (latest packages feed)
2. Review all changes — likely many new features and bugfixes
3. Categorize each: adopt, preserve, or merge
4. Update Makefile: `PKG_VERSION:=4.5.5 PKG_RELEASE:=1`
5. Test extensively — more changes = higher risk
6. Consider running against intermediate versions to ease the transition

### Scenario: Package has local patches in `patches/feeds/packages/`

**Situation:** You have patches for the upstream package (in `patches/feeds/packages/`), and the upstream has evolved.

**Steps:**
1. Run diff to see what's different
2. Review whether your patches are still needed (upstream might have fixed the issue)
3. If needed, regenerate the patches from the upstream source:
   ```bash
   cd assets/packages/<package-name>
   git diff HEAD^ HEAD > /tmp/new-patch.diff
   ```
4. Compare with your current patch; update if necessary
5. Test the patched version in a build

## Edge Cases

- **Package renamed upstream**: The script won't find it. Manually verify it still exists in the feed under a new name.
- **Package removed from upstream**: You're now the sole maintainer. Update documentation and consider contributing upstream.
- **Multiple packages with same name**: The script finds the first one. Use `find` manually to disambiguate.
- **Large binary files**: The diff may be very large. Use `diff -r --exclude="*.bin" ...` if needed.

## Reference Files

See [REFERENCE.md](references/REFERENCE.md) for:
- Shell script explanation of `fetch-upstream.sh`
- OpenWrt feeds.conf.default format
- Git workflow for managing local patches
- Diff interpretation guide
