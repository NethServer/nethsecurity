#
# Copyright (C) 2023 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-api-server
PKG_VERSION:=0.0.1
PKG_RELEASE:=1
 
PKG_SOURCE:=$(PKG_NAME)-$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/nethserver/ns-api-server/tar.gz/$(PKG_VERSION)?
PKG_HASH:=skip

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

PKG_BUILD_DEPENDS:=golang/host
PKG_BUILD_PARALLEL:=1
PKG_BUILD_FLAGS:=no-mips16

GO_PKG:=github.com/NethServer/ns-api-server

include $(INCLUDE_DIR)/package.mk
include $(TOPDIR)/feeds/packages/lang/golang/golang-package.mk
 
define Package/ns-api-server
	SECTION:=base
	CATEGORY:=NextSecurity
	TITLE:=NextSecurity REST API server
	URL:=https://github.com/NethServer/ns-api-server
	DEPENDS:=$(GO_ARCH_DEPENDS)
endef
 
define Package/ns-api-server/description
	NextSecurity REST API server
endef


define Package/ns-api-server/install
	$(call GoPackage/Package/Install/Bin,$(1))
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/ns-api-server.initd $(1)/etc/init.d/ns-api-server
	$(INSTALL_DIR) $(1)/usr/sbin/
	$(INSTALL_BIN) $(GO_PKG_BUILD_DIR)/bin/ns-api-server $(1)/usr/sbin/
endef

$(eval $(call GoBinPackage,ns-api-server))
$(eval $(call BuildPackage,ns-api-server))
