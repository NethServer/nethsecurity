#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=telegraf
# renovate: datasource=github-tags depName=influxdata/telegraf
PKG_VERSION:=1.33.2
PKG_RELEASE:=1
 
PKG_SOURCE:=$(PKG_NAME)-$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/influxdata/telegraf/tar.gz/v$(PKG_VERSION)?
PKG_SOURCE_SUBDIR:=telegraf-$(PKG_VERSION)
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)

PKG_HASH:=skip
PKG_MAINTAINER:=Tommaso Bailetti <tommaso.bailetti@nethesis.it>
PKG_LICENSE:=MIT

PKG_BUILD_DEPENDS:=golang/host
PKG_BUILD_PARALLEL:=1
PKG_BUILD_FLAGS:=no-mips16

GO_PKG:=github.com/influxdata/telegraf/cmd/$(PKG_NAME)
GO_BUILD_PKG:=github.com/influxdata/telegraf/cmd/$(PKG_NAME)
GO_PKG_LDFLAGS_X:=github.com/influxdata/telegraf/internal.Version=$(PKG_VERSION)
GO_PKG_TAGS:= \
	custom \
	inputs.bond \
	inputs.cpu \
	inputs.disk \
	inputs.diskio \
	inputs.ethtool \
	inputs.file \
	inputs.iptables \
	inputs.kernel \
	inputs.kernel_vmstat \
	inputs.linux_cpu \
	inputs.linux_sysctl_fs \
	inputs.mem \
	inputs.net \
	inputs.netstat \
	inputs.nftables \
	inputs.nstat \
	inputs.processes \
	inputs.sensors \
	inputs.system \
	outputs.influxdb \
	parsers.json_v2

include $(INCLUDE_DIR)/package.mk
include $(TOPDIR)/feeds/packages/lang/golang/golang-package.mk
 
define Package/telegraf
	SECTION:=base
	CATEGORY:=NethServer
	TITLE:=Telegraf
	URL:=https://github.com/influxdata/telegraf
	DEPENDS:=$(GO_ARCH_DEPENDS)
endef
 
define Package/telegraf/description
	Telegraf is an agent for collecting, processing, aggregating, and writing metrics.
endef

define Package/telegraf/conffiles
/etc/telegraf/telegraf.d/
endef


define Package/telegraf/install
	$(call GoPackage/Package/Install/Bin,$(1))
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/telegraf.initd $(1)/etc/init.d/telegraf
	$(INSTALL_DIR) $(1)/etc/telegraf
	$(INSTALL_DATA) ./files/telegraf.conf $(1)/etc/telegraf/telegraf.conf
endef

define Package/telegraf/postinst
#!/bin/sh
[ -z "$${IPKG_INSTROOT}" ] && /etc/init.d/telegraf restart
exit 0
endef

$(eval $(call GoBinPackage,telegraf))
$(eval $(call BuildPackage,telegraf))