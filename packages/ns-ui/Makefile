#
# Copyright (C) 2022 Nethesis
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-ui
PKG_VERSION:=0.0.1
PKG_RELEASE:=$(AUTORELEASE)

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://github.com/NethServer/nextsecurity-controller
PKG_SOURCE_VERSION=d59474ebc5a81ad9eb5b8a0451dc8940d40755c0

#PKG_BUILD_DIR:=$(BUILD_DIR)/ns-ui-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk

HOST_BUILD_PARALLEL:=1
PKG_BUILD_DEPENDS:=node/host

define Package/ns-ui
	SECTION:=base
	CATEGORY:=NextSecurity
	TITLE:=NextSecurity UI
	URL:=https://github.com/NethServer/nextsecurity-controller/
	DEPENDS:=+nginx
	PKGARCH:=all
endef
 
define Package/ns-ui/description
NextSecurity web user interface
endef

define Package/ns-ui/conffiles
endef

# this is required, otherwise compile will fail
define Build/Compile
	(export NODE_OPTIONS='--max-old-space-size=1024'; \
		cd $(PKG_BUILD_DIR)/ui/; \
		npm install && npm run build; \
		sed -i 's/"controller"/"stand-alone"/' ./dist/config/config.production.js; \
	)
endef

define Package/ns-ui/install
	$(INSTALL_DIR) $(1)/www-ns
	$(INSTALL_DIR) $(1)/etc/nginx/conf.d
	$(INSTALL_CONF) ./files/00ns.locations $(1)/etc/nginx/conf.d/
	$(CP) $(PKG_BUILD_DIR)/ui/dist/* $(1)/www-ns
endef
 
$(eval $(call BuildPackage,ns-ui))
