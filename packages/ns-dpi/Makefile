#
# Copyright (C) 2022 Nethesis
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk

PKG_NAME:=ns-dpi
PKG_VERSION:=0.0.1
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/ns-dpi-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk

define Package/ns-dpi
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=DPI rules
	URL:=https://github.com/NethServer/nethsecurity/
	DEPENDS:=+netify-flow-actions +kmod-ipt-conntrack-label
	PKGARCH:=all
endef

define Package/ns-dpi/description
	Traffic rules for network flows
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-dpi/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_DIR) $(1)/etc/xtables
	$(INSTALL_CONF) ./files/connlabel.conf $(1)/etc/xtables
	$(INSTALL_BIN) ./files/dpi.init $(1)/etc/init.d/dpi
	$(INSTALL_BIN) ./files/dpi-start $(1)/usr/sbin/
	$(INSTALL_BIN) ./files/dpi-nft $(1)/usr/sbin/
	$(INSTALL_BIN) ./files/dpi-config $(1)/usr/sbin/
	$(INSTALL_CONF) ./files/20_dpi $(1)/etc/uci-defaults
endef

$(eval $(call BuildPackage,ns-dpi))
