#!/bin/bash

# This is a helper script to extract all Netify IPK packages
# into tmp/{arch} directories for analysis and integration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NETIFYD_IPKS_DIR="${SCRIPT_DIR}/netifyd-ipks"
TMP_DIR="${NETIFYD_IPKS_DIR}/tmp"

# Clean up previous extraction
echo "Cleaning up previous extractions..."
rm -rf "${TMP_DIR}"

# Function to extract IPK package
extract_ipk() {
    local ipk_file="$1"
    local arch="$2"
    local pkg_name=$(basename "${ipk_file}" .ipk)
    local temp_extract_dir="${TMP_DIR}/.extract_temp"

    echo "Extracting ${pkg_name} (${arch})..."

    # Create temporary extraction directory
    rm -rf "${temp_extract_dir}"
    mkdir -p "${temp_extract_dir}"

    # Extract IPK package (ar archive) and extract data.tar.gz directly
    tar -xf "${ipk_file}" ./data.tar.gz -O | tar -xzf - -C "${temp_extract_dir}"

    # Process extracted files
    if [ -d "${temp_extract_dir}" ]; then
        # Move binaries (usr/lib and usr/sbin) to tmp/bin/{arch}
        if [ -d "${temp_extract_dir}/usr/lib" ]; then
            mkdir -p "${TMP_DIR}/bin/${arch}/lib"
            cp -r "${temp_extract_dir}/usr/lib"/* "${TMP_DIR}/bin/${arch}/lib/"
        fi

        if [ -d "${temp_extract_dir}/usr/sbin" ]; then
            mkdir -p "${TMP_DIR}/bin/${arch}/sbin"
            cp -r "${temp_extract_dir}/usr/sbin"/* "${TMP_DIR}/bin/${arch}/sbin/"
        fi

        # Move all other files to tmp/config
        for item in "${temp_extract_dir}"/*; do
            if [ -e "${item}" ]; then
                item_name=$(basename "${item}")
                # Skip usr directory as we already processed binaries
                if [ "${item_name}" != "usr" ]; then
                    mkdir -p "${TMP_DIR}/config"
                    cp -r "${item}" "${TMP_DIR}/config/"
                fi
            fi
        done

        # Handle remaining usr content (like usr/share)
        if [ -d "${temp_extract_dir}/usr" ]; then
            for subitem in "${temp_extract_dir}/usr"/*; do
                if [ -e "${subitem}" ]; then
                    subitem_name=$(basename "${subitem}")
                    # Skip lib and sbin as already processed
                    if [ "${subitem_name}" != "lib" ] && [ "${subitem_name}" != "sbin" ]; then
                        mkdir -p "${TMP_DIR}/config/usr"
                        cp -r "${subitem}" "${TMP_DIR}/config/usr/"
                    fi
                fi
            done
        fi
    fi

    # Clean up temporary directory
    rm -rf "${temp_extract_dir}"
}

# Process all architecture directories
for arch_dir in "${NETIFYD_IPKS_DIR}"/*; do
    if [ -d "${arch_dir}" ]; then
        arch=$(basename "${arch_dir}")

        # Skip tmp directory
        if [ "${arch}" = "tmp" ]; then
            continue
        fi

        echo "Processing ${arch} packages..."
        for ipk in "${arch_dir}"/*.ipk; do
            if [ -f "${ipk}" ]; then
                extract_ipk "${ipk}" "${arch}"
            fi
        done
    fi
done

echo ""
echo "Extraction complete!"
echo "Files extracted to: ${TMP_DIR}"
echo ""
echo "Directory structure:"
tree -L 2 "${TMP_DIR}" 2>/dev/null || find "${TMP_DIR}" -maxdepth 2 -type d
