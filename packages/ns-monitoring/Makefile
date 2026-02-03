#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-monitoring
# renovate: datasource=github-tags depName=nethserver/nethsecurity-monitoring
PKG_VERSION:=a9978744f63568e2ea10e225bae901cb7271c7e5
PKG_RELEASE:=1

PKG_SOURCE:=$(PKG_NAME)-$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/nethserver/nethsecurity-monitoring/tar.gz/$(PKG_VERSION)?
PKG_SOURCE_SUBDIR:=nethsecurity-monitoring-$(PKG_VERSION)
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)

PKG_HASH:=skip
PKG_MAINTAINER:=Tommaso Bailetti <tommaso.bailetti@nethesis.it>
PKG_LICENSE:=MIT

PKG_BUILD_DEPENDS:=golang/host
PKG_BUILD_PARALLEL:=1
PKG_BUILD_FLAGS:=no-mips16

GO_PKG:=github.com/nethserver/nethsecurity-monitoring

include $(INCLUDE_DIR)/package.mk
include $(TOPDIR)/feeds/packages/lang/golang/golang-package.mk

define Package/ns-monitoring
	SECTION:=base
	CATEGORY:=NethServer
	TITLE:=Nethsecurity Monitoring
	URL:=https://github.com/nethserver/nethsecurity-monitoring
	DEPENDS:=$(GO_ARCH_DEPENDS)
endef

define Package/ns-monitoring/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) $(GO_PKG_BUILD_BIN_DIR)/nethsecurity-monitoring $(1)/usr/sbin/ns-flows
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/ns-flows.init $(1)/etc/init.d/ns-flows
endef

define Package/ns-monitoring/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	/etc/init.d/ns-flows restart
	if /etc/init.d/ns-flows enabled; then
		/etc/init.d/ns-flows enable
	fi
fi
exit 0
endef

$(eval $(call GoBinPackage,ns-monitoring))
$(eval $(call BuildPackage,ns-monitoring))
