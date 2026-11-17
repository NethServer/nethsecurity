#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=ns-watchdog
PKG_VERSION:=0.0.3
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)

PKG_MAINTAINER:=Filippo Carletti <filippo.carletti@nethesis.it>
PKG_LICENSE:=GPL-2.0-only

include $(INCLUDE_DIR)/package.mk

define Package/ns-watchdog
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Hardware watchdog driver selection
	URL:=https://github.com/NethServer/nethsecurity
	DEPENDS:=@TARGET_x86 \
		+kmod-i6300esb-wdt \
		+kmod-itco-wdt \
		+kmod-sp5100-tco \
		+kmod-softdog
	PKGARCH:=all
endef

define Package/ns-watchdog/description
	Ship x86 watchdog drivers and pick the one matching the hardware
	at boot, so procd pings a watchdog that can actually reset the system.
endef

define Build/Compile
endef

# Blacklist the watchdog modules for kmodloader, so only the preinit hook
# loads them. /etc/modules.conf belongs to ubox: edit a marked block.
# The module list is read from the hook, which is the single source.
# This writes the copy in the read-only image, read before preinit;
# the hook rewrites the block in the overlay copy when it differs.
define Package/ns-watchdog/postinst
#!/bin/sh
conf="$${IPKG_INSTROOT}/etc/modules.conf"
hook="$${IPKG_INSTROOT}/lib/preinit/83_ns_watchdog"
sed -i '/^# BEGIN ns-watchdog$$/,/^# END ns-watchdog$$/d' "$$conf" 2>/dev/null
{
	echo "# BEGIN ns-watchdog"
	for mod in $$(sed -n 's/^NS_WDT_ALL="\(.*\)"$$/\1/p' "$$hook"); do
		echo "blacklist $$mod"
	done
	echo "# END ns-watchdog"
} >> "$$conf"
exit 0
endef

define Package/ns-watchdog/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	sed -i '/^# BEGIN ns-watchdog$$/,/^# END ns-watchdog$$/d' /etc/modules.conf
fi
exit 0
endef

define Package/ns-watchdog/install
	$(INSTALL_DIR) $(1)/lib/preinit
	$(INSTALL_DATA) ./files/83_ns_watchdog $(1)/lib/preinit/83_ns_watchdog
endef

$(eval $(call BuildPackage,ns-watchdog))
