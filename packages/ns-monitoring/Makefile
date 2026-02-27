#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-monitoring
# renovate: datasource=github-tags depName=nethserver/nethsecurity-monitoring
PKG_VERSION:=0.0.1
PKG_RELEASE:=1

PKG_SOURCE:=$(PKG_NAME)-$(PKG_VERSION).tar.gz
PKG_SOURCE_VERSION:=badb4039bf3fd5f216154777d8e72413185e8f86
PKG_SOURCE_URL:=https://codeload.github.com/nethserver/nethsecurity-monitoring/tar.gz/$(PKG_SOURCE_VERSION)?
PKG_SOURCE_SUBDIR:=nethsecurity-monitoring-$(PKG_SOURCE_VERSION)
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

define Package/ns-monitoring/conffiles
/etc/config/monitoring
endef

define Package/ns-monitoring/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) $(GO_PKG_BUILD_BIN_DIR)/nethsecurity-monitoring $(1)/usr/sbin/ns-flows
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) ./files/ns-flows.conf $(1)/etc/config/ns-flows
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/monitoring.uci-defaults $(1)/etc/uci-defaults/99-monitoring
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/ns-flows.init $(1)/etc/init.d/ns-flows
	$(INSTALL_DIR) $(1)/etc/netifyd
	$(INSTALL_DIR) $(1)/etc/netifyd/plugins.d
	$(INSTALL_CONF) ./files/netifyd/plugins.d/10-netify-flows.conf $(1)/etc/netifyd/plugins.d/10-netify-flows.conf
	$(INSTALL_CONF) ./files/netifyd/netify-sink-socket-flows.json $(1)/etc/netifyd/netify-sink-socket-flows.json
	$(INSTALL_CONF) ./files/netifyd/netify-proc-core-flows.json $(1)/etc/netifyd/netify-proc-core-flows.json
endef

define Package/ns-monitoring/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	/etc/init.d/ns-flows restart
	/etc/init.d/netifyd reload
	if /etc/init.d/ns-flows enabled; then
		/etc/init.d/ns-flows enable
	fi
fi
exit 0
endef

$(eval $(call GoBinPackage,ns-monitoring))
$(eval $(call BuildPackage,ns-monitoring))
