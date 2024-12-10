#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-flashstart
PKG_VERSION:=0.0.6
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-flashstart-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-flashstart
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Flashstart integration
	URL:=https://github.com/NethServer/nethsecurity-controller/
	DEPENDS:=+dnsdist +python3-nethsec
	PKGARCH:=all
endef
 
define Package/ns-flashstart/description
	Register and enable Flashstart DNS filter
endef

define Package/ns-flashstart/conffiles
/etc/config/flashstart
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-flashstart/install
	$(INSTALL_DIR) $(1)/usr/share/ns-flashstart
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DIR) $(1)/etc/hotplug.d/iface/
	$(INSTALL_BIN) ./files/flashstart-apply $(1)/usr/sbin/flashstart-apply
	$(INSTALL_BIN) ./files/flashstart-auth $(1)/usr/share/ns-flashstart/flashstart-auth
	$(INSTALL_BIN) ./files/flashstart-setup-firewall $(1)/usr/share/ns-flashstart/flashstart-setup-firewall
	$(INSTALL_CONF) ./files/config $(1)/etc/config/flashstart
	$(INSTALL_DATA) ./files/hotplug $(1)/etc/hotplug.d/iface/90-flashstart
endef
 
$(eval $(call BuildPackage,ns-flashstart))
