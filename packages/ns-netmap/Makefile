#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-netmap
PKG_VERSION:=0.0.1
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-netmap-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-netmap
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Netmap firewall rules
	URL:=https://github.com/NethServer/nethsecurity/
	DEPENDS:=+python3-nethsec
	PKGARCH:=all
endef
 
define Package/ns-netmap/description
	Implement netmap firewall rules
endef

define Package/ns-netmap/conffiles
/etc/config/netmap
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-netmap/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_BIN) ./files/ns-netmap $(1)/usr/sbin/ns-netmap
	$(INSTALL_CONF) ./files/config $(1)/etc/config/netmap
endef
 
$(eval $(call BuildPackage,ns-netmap))
