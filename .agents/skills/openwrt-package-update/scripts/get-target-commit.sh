#!/bin/bash
#
# Get the target OpenWrt packages feed commit hash from feeds.conf.default
# at the version specified in build.conf.defaults
#
# Outputs the commit hash to stdout, or exits with error if fetch/parse fails.
#

set -euo pipefail

# Find workspace root
WORKSPACE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && git rev-parse --show-toplevel 2>/dev/null || echo ".")

# Read OWRT_VERSION from build.conf.defaults
if [[ ! -f "$WORKSPACE_ROOT/build.conf.defaults" ]]; then
    echo "Error: build.conf.defaults not found at $WORKSPACE_ROOT" >&2
    exit 1
fi

OWRT_VERSION=$(grep '^OWRT_VERSION=' "$WORKSPACE_ROOT/build.conf.defaults" | cut -d'=' -f2 | tr -d ' ')

if [[ -z "$OWRT_VERSION" ]]; then
    echo "Error: OWRT_VERSION not found or empty in build.conf.defaults" >&2
    exit 1
fi

# Fetch feeds.conf.default from OpenWrt at the specified tag
FEEDS_URL="https://raw.githubusercontent.com/openwrt/openwrt/$OWRT_VERSION/feeds.conf.default"

FEEDS_CONTENT=$(curl -fsSL "$FEEDS_URL" 2>/dev/null || {
    echo "Error: Failed to fetch $FEEDS_URL" >&2
    exit 1
})

# Parse the packages line to extract the commit hash (after the ^)
# Expected format: src-git packages https://git.openwrt.org/feed/packages.git^<hash>
PACKAGES_COMMIT=$(echo "$FEEDS_CONTENT" | grep '^src-git packages' | sed 's/.*\^//g' | head -1)

if [[ -z "$PACKAGES_COMMIT" ]]; then
    echo "Error: Could not parse packages commit hash from feeds.conf.default" >&2
    exit 1
fi

echo "$PACKAGES_COMMIT"
