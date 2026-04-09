#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=checkmk-agent
PKG_VERSION:=2.4.0p24
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/checkmk-agent-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-2.0-only

include $(INCLUDE_DIR)/package.mk

define Package/checkmk-agent
	SECTION:=base
	CATEGORY:=Administration
	TITLE:=Check_MK monitoring agent
	URL:=https://github.com/Checkmk/checkmk
	DEPENDS:=+socat
	PKGARCH:=all
endef

define Package/checkmk-agent/description
	Check_MK monitoring agent
endef


# Download the Check_MK agent binary
define Download/checkmk-agent-binary
  URL:=https://raw.githubusercontent.com/Checkmk/checkmk/v$(PKG_VERSION)/agents
  URL_FILE:=check_mk_agent.openwrt
  FILE:=check_mk_agent.openwrt
  HASH:=skip
endef
$(eval $(call Download,checkmk-agent-binary))

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	$(CP) $(DL_DIR)/check_mk_agent.openwrt $(PKG_BUILD_DIR)/check_mk_agent
endef

define Build/Configure
	true
endef

define Build/Compile
	true
endef

define Package/checkmk-agent/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_mk_agent $(1)/usr/sbin/check_mk_agent
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/check_mk_agent.init $(1)/etc/init.d/check_mk_agent
endef

$(eval $(call BuildPackage,checkmk-agent))
