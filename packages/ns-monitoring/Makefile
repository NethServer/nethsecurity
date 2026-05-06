#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-monitoring
# renovate: datasource=github-tags depName=nethserver/nethsecurity-monitoring
PKG_VERSION:=1.1.2
PKG_RELEASE:=1

PKG_SOURCE:=nethsecurity-monitoring-v$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/nethserver/nethsecurity-monitoring/tar.gz/v$(PKG_VERSION)?
PKG_SOURCE_SUBDIR:=nethsecurity-monitoring-$(PKG_VERSION)
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)

PKG_HASH:=skip
PKG_MAINTAINER:=Tommaso Bailetti <tommaso.bailetti@nethesis.it>
PKG_LICENSE:=MIT

PKG_BUILD_DEPENDS:=golang/host
PKG_BUILD_PARALLEL:=1
PKG_BUILD_FLAGS:=no-mips16

GO_PKG:=github.com/nethserver/nethsecurity-monitoring
GO_PKG_BUILD_PKG:= \
	$(GO_PKG)/cmd/ns-flows \
	$(GO_PKG)/cmd/ns-stats
GO_PKG_INSTALL_BIN_PATH:=/usr/sbin

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
/etc/config/ns-flows
/etc/config/ns-stats
endef

define Package/ns-monitoring/install
	$(call GoPackage/Package/Install/Bin,$(1))
	# configuration files
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) ./files/ns-flows.conf $(1)/etc/config/ns-flows
	$(INSTALL_CONF) ./files/ns-stats.conf $(1)/etc/config/ns-stats
	# init scripts
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/ns-flows.init $(1)/etc/init.d/ns-flows
	$(INSTALL_BIN) ./files/ns-stats.init $(1)/etc/init.d/ns-stats
	# startup and crons
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/99-ns-stats $(1)/etc/uci-defaults/99-ns-stats
	# netifyd configuration
	$(INSTALL_DIR) $(1)/etc/netifyd
	$(INSTALL_DIR) $(1)/etc/netifyd/plugins.d
	## ns-flows
	$(INSTALL_CONF) ./files/netifyd/plugins.d/10-ns-flows.conf $(1)/etc/netifyd/plugins.d/10-ns-flows.conf
	$(INSTALL_CONF) ./files/netifyd/netify-sink-socket-flows.json $(1)/etc/netifyd/netify-sink-socket-flows.json
	$(INSTALL_CONF) ./files/netifyd/netify-proc-core-flows.json $(1)/etc/netifyd/netify-proc-core-flows.json
	## ns-stats
	$(INSTALL_CONF) ./files/netifyd/plugins.d/10-ns-stats.conf $(1)/etc/netifyd/plugins.d/10-ns-stats.conf
	$(INSTALL_CONF) ./files/netifyd/netify-ns-stats-proc.json $(1)/etc/netifyd/netify-ns-stats-proc.json
	$(INSTALL_CONF) ./files/netifyd/netify-ns-stats-sink.json $(1)/etc/netifyd/netify-ns-stats-sink.json
	# additional binaries
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) ./files/ns-stats-cleanup $(1)/usr/bin/ns-stats-cleanup
endef

define Package/ns-monitoring/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	/etc/init.d/netifyd restart
fi
exit 0
endef

define Package/ns-monitoring/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	crontab -l | grep -v "/usr/bin/ns-stats-cleanup" | sort | uniq | crontab -
fi
exit 0
endef

$(eval $(call GoBinPackage,ns-monitoring))
$(eval $(call BuildPackage,ns-monitoring))
