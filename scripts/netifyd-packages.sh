#!/bin/bash

# This is a helper script to extract all Netify IPK packages
# kindly provided by them, that allows the extraction of the packages
# into a single meta-package for OpenWrt.

set -eou pipefail

BASE="$(realpath "packages")"
IPKS="$(realpath "scripts/netifyd-ipks")"
PACKAGES="$(find "$IPKS" -name 'netify*.ipk' | grep -v integration)"
FEED="${BASE}/netify-integration-meta"

if [ -z "$PACKAGES" ]; then
    echo "No packages found."
    exit 1
fi

if [ -d "${FEED}/files" ]; then
    sudo rm -rf "${FEED}/files"
fi

mkdir -vp "${FEED}/files"
pushd "${FEED}/files"

DEPENDS=
for PACKAGE in $PACKAGES; do
    tar -xf "${PACKAGE}" ./data.tar.gz -O | sudo tar -xzf - -C "${FEED}/files/"
done

sudo rm -rf lib
sudo chown -R ${USER}:${USER} .
sudo find . -type f -print0 | xargs -0 -n 1 chmod a+r
sudo find . -type d -print0 | xargs -0 -n 1 chmod a+x

DIRS=$(find . -type d | sed -e 's/^\.//' | sort)
FILES=$(find . -type f | sed -e 's/^\.//' | sort)
LINKS=$(find . -type l | sed -e 's/^\.//' | sort)

echo -e "\ndefine Package/netify-integration-meta/install"

for DIR in $DIRS; do
    echo -e "\t\$(INSTALL_DIR) \$(1)$DIR"
done

for FILE in $FILES; do
    INSTALL="INSTALL_DATA"
    if [ -x "./$FILE" ]; then
        INSTALL="INSTALL_BIN"
#    elif [[ $FILE =~ \.conf$ ]]; then
#        INSTALL="INSTALL_CONF"
#    elif [[ $FILE =~ \.json$ ]]; then
#        INSTALL="INSTALL_CONF"
#    elif [[ $FILE =~ etc/config ]]; then
#        INSTALL="INSTALL_CONF"
    fi

    echo -e "\t\$($INSTALL) ./files${FILE} \$(1)$FILE"
done

for LINK in $LINKS; do
    DIR="$(dirname $LINK)"
    LINK_SRC="$(readlink ./$LINK)"

    if [ "$(dirname $LINK_SRC)" == "." ]; then
        echo -e "\t\$(LN) $DIR/$LINK_SRC \$(1)$LINK"
    else
        echo -e "\t\$(LN) $LINK_SRC \$(1)$LINK"
    fi
done
echo -e "endef\n"

popd

echo "Edit ${BASE}/netify-integration-meta/Makefile"
echo "and update the 'install' file list."

exit 0
