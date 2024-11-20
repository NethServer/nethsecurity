#
# Copyright (C) 2024 Nethesis
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-binding
PKG_VERSION:=0.0.1
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-binding-$(PKG_VERSION)

PKG_MAINTAINER:=Tommaso Bailetti <tommaso.bailetti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk

define Package/ns-binding
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=MAC/IP binding
	URL:=https://github.com/NethServer/nethsecurity
	DEPENDS:=+python3-nethsec +dnsmasq-full
	PKGARCH:=all
endef
 
define Package/ns-binding/description
	Tool to force bind MAC addresses to IP addresses
endef

define Build/Compile
endef

define Package/ns-binding/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  /etc/init.d/ns-binding restart
fi
exit 0
endef

define Package/ns-binding/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-binding.py $(1)/usr/sbin/ns-binding
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/ns-binding.init $(1)/etc/init.d/ns-binding
endef
 
$(eval $(call BuildPackage,ns-binding))
