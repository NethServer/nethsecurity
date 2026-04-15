#!/bin/bash

# This is a helper script to extract all Netify APK packages
# into netifyd-apks/tmp/{arch} directories for analysis and integration.
#
# Usage: ./netifyd-packages.sh
#
# Input:  netifyd-apks/{arch}/*.apk
# Output: netifyd-apks/tmp/{arch}/netifyd/   — merged contents of all APKs for that arch
#         netifyd-apks/tmp/{arch}/{pkg}/     — per-package extraction (intermediate)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APKS_DIR="${SCRIPT_DIR}/netifyd-apks"
TMP_DIR="${APKS_DIR}/tmp"

if [ ! -d "${APKS_DIR}" ]; then
    echo "ERROR: APKs directory not found: ${APKS_DIR}" >&2
    exit 1
fi

# Iterate over each arch subdirectory
for arch_dir in "${APKS_DIR}"/*/; do
    [ -d "${arch_dir}" ] || continue
    
    # Skip the tmp directory
    [ "$(basename "${arch_dir}")" = "tmp" ] && continue
    
    arch="$(basename "${arch_dir}")"

    echo "==> Processing arch: ${arch}"

    output_dir="${TMP_DIR}/${arch}/netifyd"
    rm -rf "${TMP_DIR:?}/${arch}"
    mkdir -p "${output_dir}"

    # Extract each APK into its own per-package subdirectory, then merge
    for apk_file in "${arch_dir}"*.apk; do
        [ -f "${apk_file}" ] || continue

        # Derive package name: strip version and arch suffix
        # e.g. netify-plm_2026-01-01-v1.2.1-r8_x86_64.apk -> netify-plm
        filename="$(basename "${apk_file}" .apk)"
        pkg_name="${filename%%_*}"

        # Extract to a temporary directory first to avoid conflicts
        pkg_extract_dir="${TMP_DIR}/${arch}/.extract-${pkg_name}-$$"
        mkdir -p "${pkg_extract_dir}"

        echo "    Extracting ${filename} -> ${pkg_name}/"
        apk extract --allow-untrusted --destination "${pkg_extract_dir}" "${apk_file}"

        # Merge extracted files into the single netifyd output directory
        cp -a "${pkg_extract_dir}/." "${output_dir}/"
    done

    echo "    Merged output: tmp/${arch}/netifyd/"
done

echo "Done."
