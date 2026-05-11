#!/bin/bash
#
# Diff old and new package snapshots
#
# Usage: diff-package.sh <package-name>
#
# Outputs a recursive diff between assets/<name>_old/ and assets/<name>_new/
#

set -euo pipefail

PACKAGE_NAME="${1:-}"

if [[ -z "$PACKAGE_NAME" ]]; then
    echo "Usage: diff-package.sh <package-name>" >&2
    exit 1
fi

# Find skill root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ASSETS_DIR="$SKILL_ROOT/assets"

OLD_DIR="$ASSETS_DIR/${PACKAGE_NAME}_old"
NEW_DIR="$ASSETS_DIR/${PACKAGE_NAME}_new"

if [[ ! -d "$OLD_DIR" ]]; then
    echo "Error: $OLD_DIR not found. Run setup-package.sh first." >&2
    exit 1
fi

if [[ ! -d "$NEW_DIR" ]]; then
    echo "Error: $NEW_DIR not found. Run setup-package.sh first." >&2
    exit 1
fi

# Run recursive diff, showing added/removed/modified files
diff -rN "$OLD_DIR" "$NEW_DIR" || true
