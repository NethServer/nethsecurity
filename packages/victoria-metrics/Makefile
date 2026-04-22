#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=victoria-metrics
# renovate: datasource=github-tags depName=VictoriaMetrics/VictoriaMetrics
PKG_VERSION:=1.139.0
PKG_RELEASE:=1
 
PKG_SOURCE:=$(PKG_NAME)-$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/VictoriaMetrics/VictoriaMetrics/tar.gz/v$(PKG_VERSION)?
PKG_SOURCE_SUBDIR:=VictoriaMetrics-$(PKG_VERSION)
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)

PKG_HASH:=skip
PKG_MAINTAINER:=Tommaso Bailetti <tommaso.bailetti@nethesis.it>
PKG_LICENSE:=Apache-2.0

PKG_BUILD_DEPENDS:=golang/host
PKG_BUILD_PARALLEL:=1
PKG_BUILD_FLAGS:=no-mips16

GO_PKG:=github.com/VictoriaMetrics/VictoriaMetrics
GO_PKG_BUILD_PKG:=github.com/VictoriaMetrics/VictoriaMetrics/app/victoria-metrics \
	github.com/VictoriaMetrics/VictoriaMetrics/app/vmalert
GO_PKG_LDFLAGS:= \
	-extldflags \
	-static
GO_PKG_LDFLAGS_X:=github.com/VictoriaMetrics/VictoriaMetrics/lib/buildinfo.Version=$(PKG_NAME)-v$(PKG_VERSION)
GO_PKG_TAGS:= \
	netgo \
	osusergo \
	musl

include $(INCLUDE_DIR)/package.mk
include $(TOPDIR)/feeds/packages/lang/golang/golang-package.mk
 
define Package/victoria-metrics
	SECTION:=base
	CATEGORY:=NethServer
	TITLE:=Victoria Metrics
	URL:=https://github.com/VictoriaMetrics/VictoriaMetrics
	DEPENDS:=$(GO_ARCH_DEPENDS)
endef
 
define Package/victoria-metrics/description
	VictoriaMetrics time series database / single-node server.
endef

define Package/victoria-metrics/conffiles
/etc/config/victoria-metrics
/etc/config/vmalert
endef

define Package/victoria-metrics/install
	$(call GoPackage/Package/Install/Bin,$(1))
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/victoria-metrics.initd $(1)/etc/init.d/victoria-metrics
	$(INSTALL_BIN) ./files/vmalert.initd $(1)/etc/init.d/vmalert
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DATA) ./files/victoria-metrics.conf $(1)/etc/config/victoria-metrics
	$(INSTALL_DATA) ./files/vmalert.conf $(1)/etc/config/vmalert
	$(INSTALL_DIR) $(1)/etc/vmalert/rules
	$(INSTALL_DATA) ./files/vmalert-rules/*.yaml $(1)/etc/vmalert/rules/
endef

define Package/victoria-metrics/postinst
#!/bin/sh
[ -z "$${IPKG_INSTROOT}" ] && /etc/init.d/victoria-metrics restart
[ -z "$${IPKG_INSTROOT}" ] && /etc/init.d/vmalert restart
exit 0
endef

$(eval $(call GoBinPackage,victoria-metrics))
$(eval $(call BuildPackage,victoria-metrics))