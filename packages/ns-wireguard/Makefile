#
# Copyright (C) 2025 Nethesis
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-wireguard
PKG_VERSION:=1.0.0
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-wireguard-$(PKG_VERSION)

PKG_MAINTAINER:=Tommaso Bailetti <tommaso.bailetti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk

define Package/ns-wireguard
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Wireguard Tools for NethSecurity
	URL:=https://github.com/NethServer/nethsecurity
	DEPENDS:=+netifd +python3-uci +wireguard-tools +luci-app-wireguard +luci-proto-wireguard
	PKGARCH:=all
endef
 
define Package/ns-wireguard/description
	Wireguard Tools for NethSecurity, allowing config to be managed easily.
endef

define Build/Compile
endef

define Package/ns-wireguard/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  /etc/init.d/ns-wireguard restart
fi
exit 0
endef

define Package/ns-wireguard/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-wireguard.py $(1)/usr/sbin/ns-wireguard
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/ns-wireguard.init $(1)/etc/init.d/ns-wireguard
endef
 
$(eval $(call BuildPackage,ns-wireguard))
