#!/bin/bash

# This is a helper script to extract all Netify IPK packages
# into netifyd-ipks/tmp/{arch} directories for analysis and integration.
#
# Usage: ./netifyd-packages.sh
#
# Input:  netifyd-ipks/{arch}/*.ipk
# Output: netifyd-ipks/tmp/{arch}/netifyd/   — merged contents of all IPKs for that arch
#         netifyd-ipks/tmp/{arch}/{pkg}/     — per-package extraction (intermediate)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IPKS_DIR="${SCRIPT_DIR}/netifyd-ipks"
TMP_DIR="${IPKS_DIR}/tmp"

if [ ! -d "${IPKS_DIR}" ]; then
    echo "ERROR: IPKs directory not found: ${IPKS_DIR}" >&2
    exit 1
fi

# Iterate over each arch subdirectory
for arch_dir in "${IPKS_DIR}"/*/; do
    [ -d "${arch_dir}" ] || continue
    arch="$(basename "${arch_dir}")"

    echo "==> Processing arch: ${arch}"

    output_dir="${TMP_DIR}/${arch}/netifyd"
    rm -rf "${TMP_DIR:?}/${arch}"
    mkdir -p "${output_dir}"

    # Extract each IPK into its own per-package subdirectory, then merge
    for ipk_file in "${arch_dir}"*.ipk; do
        [ -f "${ipk_file}" ] || continue

        # Derive package name: strip version and arch suffix
        # e.g. netify-plm_2026-01-01-v1.2.1-r8_x86_64.ipk -> netify-plm
        filename="$(basename "${ipk_file}" .ipk)"
        pkg_name="${filename%%_*}"

        # Extract to a temporary directory first to avoid conflicts
        pkg_extract_dir="${TMP_DIR}/${arch}/.extract-${pkg_name}-$$"
        mkdir -p "${pkg_extract_dir}"

        echo "    Extracting ${filename} -> ${pkg_name}/"
        tar -xf "${ipk_file}" ./data.tar.gz -O | tar -xzf - -C "${pkg_extract_dir}"

        # Merge extracted files into the single netifyd output directory
        cp -a "${pkg_extract_dir}/." "${output_dir}/"
    done

    echo "    Merged output: tmp/${arch}/netifyd/"
done

echo "Done."
