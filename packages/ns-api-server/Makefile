#
# Copyright (C) 2023 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-api-server
# renovate: datasource=github-tags depName=NethServer/nethsecurity-api
PKG_VERSION:=1.4.1
PKG_RELEASE:=2
 
PKG_SOURCE:=ns-api-server-$(PKG_VERSION).tar.gz
PKG_BUILD_DIR=$(BUILD_DIR)/nethsecurity-api-$(PKG_VERSION)
PKG_SOURCE_URL:=https://codeload.github.com/nethserver/nethsecurity-api/tar.gz/$(PKG_VERSION)?
PKG_HASH:=skip

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

PKG_BUILD_DEPENDS:=golang/host
PKG_BUILD_PARALLEL:=1
PKG_BUILD_FLAGS:=no-mips16

GO_PKG:=github.com/NethServer/nethsecurity-api

include $(INCLUDE_DIR)/package.mk
include $(TOPDIR)/feeds/packages/lang/golang/golang-package.mk
 
define Package/ns-api-server
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity REST API server
	URL:=https://github.com/NethServer/nethsecurity-api
	DEPENDS:=$(GO_ARCH_DEPENDS)
endef
 
define Package/ns-api-server/description
	NethSecurity REST API server
endef


define Package/ns-api-server/install
	$(call GoPackage/Package/Install/Bin,$(1))
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/ns-api-server.initd $(1)/etc/init.d/ns-api-server
	$(INSTALL_DIR) $(1)/lib/upgrade/keep.d
	$(INSTALL_CONF) files/ns-api-server.keep $(1)/lib/upgrade/keep.d/ns-api-server
endef

define Package/ns-api-server/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  /etc/init.d/ns-api-server restart
fi
exit 0
endef


$(eval $(call GoBinPackage,ns-api-server))
$(eval $(call BuildPackage,ns-api-server))
