#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-reverse-proxy
PKG_VERSION:=0.0.2
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-reverse-proxy-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-reverse-proxy
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity reverse-proxy manager
	URL:=https://github.com/NethServer/nethsecurity/
	DEPENDS:=+nginx
	PKGARCH:=all
endef
 
define Package/ns-reverse-proxy/description
	Manage reverse-proxy
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-reverse-proxy/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) ./files/nginx-proxy $(1)/usr/sbin
endef
 
$(eval $(call BuildPackage,ns-reverse-proxy))
