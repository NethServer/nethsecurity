#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-ui
PKG_VERSION:=0.0.1
UI_COMMIT=a2235242a567acf48ff15aa86e676971b64c492a
PKG_RELEASE:=$(UI_COMMIT)

PKG_SOURCE:=ui-$(UI_COMMIT).tar.gz
PKG_SOURCE_URL:=https://nethsecurity.ams3.digitaloceanspaces.com/ui-dist/
PKG_HASH:=skip

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk

HOST_BUILD_PARALLEL:=1

define Package/ns-ui
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity UI
	URL:=https://github.com/NethServer/nethsecurity-controller/
	DEPENDS:=+nginx
	PKGARCH:=all
endef
 
define Package/ns-ui/description
NethSecurity web user interface
endef

define Package/ns-ui/conffiles
endef

define Build/Configure
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-ui/install
	$(INSTALL_DIR) $(1)/www-ns
	$(INSTALL_DIR) $(1)/etc/nginx/conf.d
	$(INSTALL_CONF) ./files/00ns.locations $(1)/etc/nginx/conf.d/
	$(CP) $(PKG_BUILD_DIR)/../dist/* $(1)/www-ns
endef
 
$(eval $(call BuildPackage,ns-ui))
