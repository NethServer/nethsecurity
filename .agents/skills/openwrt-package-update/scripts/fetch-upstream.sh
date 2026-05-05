#!/bin/bash
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#
# Fetch upstream OpenWrt package and compare with local fork.
#
# Usage: ./fetch-upstream.sh <openwrt-tag|HEAD> <package-name> <local-package-dir>
#
# Arguments:
#   openwrt-tag   - OpenWrt release tag (e.g., v24.10.5) or literal 'HEAD' for latest
#   package-name  - Name of the package (e.g., 'adblock', 'mwan3')
#   local-package-dir - Path to the local forked package (relative or absolute)
#
# Examples:
#   ./fetch-upstream.sh v24.10.5 adblock ../../../packages/adblock
#   ./fetch-upstream.sh HEAD mwan3 /absolute/path/to/packages/mwan3

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ASSETS_DIR="$SCRIPT_DIR/assets/packages"

OPENWRT_TAG="$1"
PACKAGE_NAME="$2"
LOCAL_PKG_DIR="$3"

# Validate arguments
if [[ -z "$OPENWRT_TAG" || -z "$PACKAGE_NAME" || -z "$LOCAL_PKG_DIR" ]]; then
    echo "ERROR: Missing arguments"
    echo "Usage: $0 <openwrt-tag|HEAD> <package-name> <local-package-dir>"
    exit 1
fi

# Resolve local package directory to absolute path
if [[ ! "$LOCAL_PKG_DIR" = /* ]]; then
    LOCAL_PKG_DIR="$(cd "$LOCAL_PKG_DIR" 2>/dev/null && pwd)" || {
        echo "ERROR: Local package directory does not exist: $LOCAL_PKG_DIR"
        exit 1
    }
else
    if [[ ! -d "$LOCAL_PKG_DIR" ]]; then
        echo "ERROR: Local package directory does not exist: $LOCAL_PKG_DIR"
        exit 1
    fi
fi

FEEDS_URL="https://raw.githubusercontent.com/openwrt/openwrt"
PACKAGES_REPO="https://github.com/openwrt/packages.git"
TARGET_HASH=""

# Step 1: Determine the packages feed hash
echo "=== Step 1: Fetching feeds.conf.default from OpenWrt $OPENWRT_TAG ==="

if [[ "$OPENWRT_TAG" == "HEAD" ]]; then
    echo "Using HEAD of packages feed (no pinned commit hash)"
    TARGET_HASH="HEAD"
else
    FEEDS_CONF_URL="$FEEDS_URL/$OPENWRT_TAG/feeds.conf.default"
    echo "Fetching: $FEEDS_CONF_URL"
    
    FEEDS_CONF=$(curl -sS "$FEEDS_CONF_URL" 2>&1) || {
        echo "ERROR: Failed to fetch feeds.conf.default from $FEEDS_CONF_URL"
        echo "$FEEDS_CONF"
        exit 1
    }
    
    # Extract the packages feed line and parse the hash after '^'
    PACKAGES_LINE=$(echo "$FEEDS_CONF" | grep "^src-git packages")
    if [[ -z "$PACKAGES_LINE" ]]; then
        echo "ERROR: Could not find 'src-git packages' line in feeds.conf.default"
        exit 1
    fi
    
    # Hash is after the '^' character if present
    TARGET_HASH=$(echo "$PACKAGES_LINE" | sed -n 's/.*\^\([a-f0-9]*\).*/\1/p')
    
    if [[ -z "$TARGET_HASH" ]]; then
        echo "WARNING: No pinned commit hash found in feeds.conf.default"
        echo "  Line: $PACKAGES_LINE"
        echo "  Using HEAD instead"
        TARGET_HASH="HEAD"
    else
        echo "Found packages feed hash: $TARGET_HASH"
    fi
fi

# Step 2: Clone or update the packages feed
echo ""
echo "=== Step 2: Cloning/updating packages feed to $ASSETS_DIR ==="

if [[ -d "$ASSETS_DIR/.git" ]]; then
    echo "Repository already exists, fetching latest..."
    cd "$ASSETS_DIR"
    git fetch origin "$TARGET_HASH" 2>&1 | grep -v "^From https" | grep -v "^ " || true
else
    echo "Cloning packages feed..."
    mkdir -p "$ASSETS_DIR"
    git clone --depth 1 "$PACKAGES_REPO" "$ASSETS_DIR" 2>&1 | grep -E "(Cloning|fatal)" || true
    cd "$ASSETS_DIR"
fi

# Checkout the target hash/branch
echo "Checking out $TARGET_HASH..."
git checkout "$TARGET_HASH" 2>&1 | grep -v "^Already on" || true

# Step 3: Find the package directory in the upstream feed
echo ""
echo "=== Step 3: Locating package '$PACKAGE_NAME' in upstream feed ==="

UPSTREAM_PKG_DIR=$(find "$ASSETS_DIR" -maxdepth 3 -type d -name "$PACKAGE_NAME" 2>/dev/null | head -1)

if [[ -z "$UPSTREAM_PKG_DIR" ]]; then
    echo "ERROR: Package '$PACKAGE_NAME' not found in upstream feed"
    echo "Searched in: $ASSETS_DIR"
    exit 1
fi

echo "Found upstream package at: $UPSTREAM_PKG_DIR"

# Step 4: Compare the directories
echo ""
echo "=== Step 4: Comparing upstream vs local package ==="
echo ""
echo "Upstream: $UPSTREAM_PKG_DIR"
echo "Local:    $LOCAL_PKG_DIR"
echo ""
echo "--- Diff (upstream vs local) ---"
echo ""

diff -ru "$UPSTREAM_PKG_DIR" "$LOCAL_PKG_DIR" || true

echo ""
echo "=== Diff Summary ==="
echo "If no changes are shown above, the local package matches upstream."
echo ""
echo "To update the local package:"
echo "  1. Review the diff above carefully"
echo "  2. Copy relevant files from: $UPSTREAM_PKG_DIR"
echo "  3. Preserve intentional local customizations"
echo "  4. Update PKG_VERSION and PKG_RELEASE in Makefile"
echo "  5. Re-run this script to verify changes"
