#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-don
PKG_VERSION:=0.0.1
PKG_RELEASE:=$(AUTORELEASE)
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-don-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-don
	SECTION:=base
	CATEGORY:=NextSecurity
	TITLE:=Windmill Don client
	URL:=https://github.com/NethServer/nextsecurity/
	DEPENDS:=+openvpn +dropbear
	PKGARCH:=all
endef
 
define Package/ns-don/description
	Connect to a remote Windmill installations
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-don/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_DIR) $(1)/etc/don
	$(INSTALL_BIN) ./files/don $(1)/usr/sbin
	$(INSTALL_CONF) ./files/20_ns_don $(1)/etc/uci-defaults
	$(INSTALL_CONF) ./files/nethesis.pub $(1)/etc/don
	$(INSTALL_CONF) ./files/nethesis.pem $(1)/etc/don
endef
 
$(eval $(call BuildPackage,ns-don))
