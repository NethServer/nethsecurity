#!/bin/bash
#
# Setup old and new package snapshots for comparison
#
# Usage: setup-package.sh <package-name>
#
# Outputs:
#   - Creates assets/<name>_old/ with the current pinned upstream version
#   - Creates assets/<name>_new/ with the target upstream version (from feeds.conf.default)
#   - Prints to stdout: package name, CURRENT_COMMIT, TARGET_COMMIT, upstream path
#

set -euo pipefail

PACKAGE_NAME="${1:-}"

if [[ -z "$PACKAGE_NAME" ]]; then
    echo "Usage: setup-package.sh <package-name>" >&2
    exit 1
fi

# Find workspace root (convert to absolute path)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT=$(cd "$SCRIPT_DIR/../../../.." && git rev-parse --show-toplevel 2>/dev/null || pwd)
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ASSETS_DIR="$SKILL_ROOT/assets"

# Ensure assets dir exists
mkdir -p "$ASSETS_DIR"

# Read current package version from local Makefile
LOCAL_MAKEFILE="$WORKSPACE_ROOT/packages/$PACKAGE_NAME/Makefile"
if [[ ! -f "$LOCAL_MAKEFILE" ]]; then
    echo "Error: $LOCAL_MAKEFILE not found" >&2
    exit 1
fi

PKG_VERSION=$(grep '^PKG_VERSION:=' "$LOCAL_MAKEFILE" | cut -d'=' -f2 | tr -d ' ')
PKG_RELEASE=$(grep '^PKG_RELEASE:=' "$LOCAL_MAKEFILE" | cut -d'=' -f2 | tr -d ' ')

if [[ -z "$PKG_VERSION" ]]; then
    echo "Error: PKG_VERSION not found in $LOCAL_MAKEFILE" >&2
    exit 1
fi

echo "Package: $PACKAGE_NAME (version $PKG_VERSION-$PKG_RELEASE)" >&2

# Get target commit from feeds.conf.default
TARGET_COMMIT=$("$SKILL_ROOT/scripts/get-target-commit.sh")
echo "Target commit: $TARGET_COMMIT" >&2

# Clone/fetch openwrt/packages bare repo
BARE_REPO="$ASSETS_DIR/.openwrt-packages-repo"

if [[ ! -d "$BARE_REPO" ]]; then
    echo "Cloning openwrt/packages (bare repo)..." >&2
    git clone --bare --filter=blob:none https://github.com/openwrt/packages.git "$BARE_REPO" 2>/dev/null || {
        echo "Error: Failed to clone openwrt/packages" >&2
        exit 1
    }
else
    echo "Fetching openwrt/packages..." >&2
    cd "$BARE_REPO"
    git fetch origin 2>/dev/null || {
        echo "Error: Failed to fetch openwrt/packages" >&2
        exit 1
    }
    cd - > /dev/null
fi

# Auto-discover the upstream path by searching for <package-name>/Makefile
# Look in the target commit first to find the exact path
echo "Discovering upstream package path..." >&2
UPSTREAM_PATH=$(cd "$BARE_REPO" && git ls-tree -r --name-only "$TARGET_COMMIT" | grep -E "^[^/]+/$PACKAGE_NAME/Makefile$" | sed 's|/Makefile$||' | head -1)

if [[ -z "$UPSTREAM_PATH" ]]; then
    echo "Error: Could not find $PACKAGE_NAME in upstream openwrt/packages at $TARGET_COMMIT" >&2
    exit 1
fi

echo "Upstream path: $UPSTREAM_PATH" >&2

# Find the commit that introduced the current version
# Step 1: Find when PKG_VERSION was introduced using pickaxe
# Step 2: Find when PKG_RELEASE was set using pickaxe
echo "Finding commit that matches local version ($PKG_VERSION-$PKG_RELEASE)..." >&2

CURRENT_COMMIT=""

# Step 1: Find commits that introduced PKG_VERSION
echo "  Step 1: Finding commits with PKG_VERSION:=$PKG_VERSION..." >&2
version_commits=$(cd "$BARE_REPO" && git log -S "PKG_VERSION:=$PKG_VERSION" --all --format="%H" -- "$UPSTREAM_PATH/Makefile" 2>/dev/null)

if [[ -z "$version_commits" ]]; then
    echo "Error: Could not find PKG_VERSION:=$PKG_VERSION in git history" >&2
    exit 1
fi

# Get the oldest commit where PKG_VERSION was introduced (last in the list when searching backwards)
version_commit=$(echo "$version_commits" | tail -1)
echo "  PKG_VERSION introduced at: $version_commit" >&2

# Step 2: From that commit forward, find when PKG_RELEASE was set
# We search commits from version_commit onwards for PKG_RELEASE change
echo "  Step 2: Finding commits with PKG_RELEASE:=$PKG_RELEASE after version introduction..." >&2
release_commits=$(cd "$BARE_REPO" && git log -S "PKG_RELEASE:=$PKG_RELEASE" --all --format="%H" -- "$UPSTREAM_PATH/Makefile" 2>/dev/null)

if [[ -n "$release_commits" ]]; then
    # Find the first commit in release_commits that is an ancestor of or after version_commit
    # Also verify both PKG_VERSION and PKG_RELEASE are present
    while IFS= read -r commit; do
        makefile_content=$(cd "$BARE_REPO" && git show "$commit:$UPSTREAM_PATH/Makefile" 2>/dev/null || echo "")
        
        if echo "$makefile_content" | grep -q "^PKG_VERSION:=$PKG_VERSION" && \
           echo "$makefile_content" | grep -q "^PKG_RELEASE:=$PKG_RELEASE"; then
            CURRENT_COMMIT="$commit"
            break
        fi
    done <<< "$release_commits"
fi

if [[ -z "$CURRENT_COMMIT" ]]; then
    echo "Error: Could not find a commit matching $PKG_VERSION-$PKG_RELEASE in upstream history" >&2
    echo "Available version range (last 20 commits):" >&2
    cd "$BARE_REPO" && git log --all --oneline -20 -- "$UPSTREAM_PATH/Makefile" >&2
    exit 1
fi

echo "Current commit: $CURRENT_COMMIT" >&2

# Extract the old version (current commit)
OLD_DIR="$ASSETS_DIR/${PACKAGE_NAME}_old"
rm -rf "$OLD_DIR"
mkdir -p "$OLD_DIR"

echo "Extracting old version to $OLD_DIR..." >&2
strip_level=$(echo "$UPSTREAM_PATH" | awk -F/ '{print NF}')
cd "$BARE_REPO" && git archive "$CURRENT_COMMIT" "$UPSTREAM_PATH/" | tar -x --strip-components=$strip_level -C "$OLD_DIR" 2>/dev/null || {
    echo "Error: Failed to extract old version" >&2
    exit 1
}

# Extract the new version (target commit)
NEW_DIR="$ASSETS_DIR/${PACKAGE_NAME}_new"
rm -rf "$NEW_DIR"
mkdir -p "$NEW_DIR"

echo "Extracting new version to $NEW_DIR..." >&2
cd "$BARE_REPO" && git archive "$TARGET_COMMIT" "$UPSTREAM_PATH/" | tar -x --strip-components=$strip_level -C "$NEW_DIR" 2>/dev/null || {
    echo "Error: Failed to extract new version" >&2
    exit 1
}

# Output summary to stdout
echo ""
echo "===== SETUP COMPLETE ====="
echo "Package: $PACKAGE_NAME"
echo "Current upstream commit: $CURRENT_COMMIT"
echo "Target upstream commit: $TARGET_COMMIT"
echo "Upstream path: $UPSTREAM_PATH"
echo "Old version snapshot: $OLD_DIR"
echo "New version snapshot: $NEW_DIR"
