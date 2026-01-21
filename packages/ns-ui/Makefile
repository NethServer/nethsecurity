#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-ui
# renovate: datasource=github-releases depName=NethServer/nethsecurity-ui
PKG_VERSION:=flows
PKG_RELEASE:=1

PKG_SOURCE:=nethsecurity-ui-$(PKG_VERSION).tar.gz
PKG_BUILD_DIR=$(BUILD_DIR)/nethsecurity-ui-$(PKG_VERSION)
PKG_SOURCE_URL:=https://codeload.github.com/nethserver/nethsecurity-ui/tar.gz/$(PKG_VERSION)?
PKG_HASH:=skip

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

PKG_BUILD_DEPENDS:=node/host
PKG_BUILD_PARALLEL:=1

include $(INCLUDE_DIR)/package.mk

define Package/ns-ui
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity UI
	URL:=https://github.com/NethServer/nethsecurity-ui/
	DEPENDS:=+nginx-ssl
	PKGARCH:=all
endef

define Package/ns-ui/description
NethSecurity web user interface
endef

define Build/Configure
endef

define Package/ns-ui/conffiles
/etc/config/ns-ui
/www-ns/branding.js
endef

define Build/Compile
	(cd $(PKG_BUILD_DIR) && npm ci && npm run build)
endef

define Package/ns-ui/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  /etc/init.d/ns-ui restart
fi
exit 0
endef

define Package/ns-ui/install
	$(INSTALL_DIR) $(1)/www-ns
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/etc/nginx/conf.d
	$(INSTALL_CONF) ./files/00ns.locations $(1)/etc/nginx/conf.d/
	$(INSTALL_CONF) ./files/config $(1)/etc/config/ns-ui
	$(INSTALL_BIN) ./files/ns-ui $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/ns-ui.init $(1)/etc/init.d/ns-ui
	$(CP) $(PKG_BUILD_DIR)/dist/* $(1)/www-ns
endef
 
$(eval $(call BuildPackage,ns-ui))
