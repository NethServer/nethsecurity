#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-objects
PKG_VERSION:=0.0.1
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-objects-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-objects
	SECTION:=base
	CATEGORY:=NextSecurity
	TITLE:=NextSecurity controller client
	URL:=https://github.com/NethServer/nextsecurity-controller/
	DEPENDS:=+python3-nextsec
	PKGARCH:=all
endef
 
define Package/ns-objects/description
	Manage firewall objects and users
endef

define Package/ns-objects/conffiles
	/etc/config/objects
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-objects/install
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_CONF) ./files/config $(1)/etc/config/objects
endef
 
$(eval $(call BuildPackage,ns-objects))
