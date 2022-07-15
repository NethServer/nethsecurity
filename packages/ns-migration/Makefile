#
# Copyright (C) 2022 Nethesis
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-migration
PKG_VERSION:=0.0.1
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-migration-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-migration
	SECTION:=base
	CATEGORY:=NextSecurity
	TITLE:=NS7 2 NextSecurity migration
	URL:=https://github.com/NethServer/nextsecurity/tree/master/packages/ns-migration
	PKGARCH:=all
endef
 
define Package/ns-migration/description
	Import NS7 firewall configuration
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-migration/install
	$(INSTALL_DIR) $(1)/usr/share/ns-migration
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-import $(1)/usr/sbin/ns-import
	$(INSTALL_BIN) ./files/scripts/network $(1)/usr/share/ns-migration/network
	$(INSTALL_BIN) ./files/scripts/dhcp $(1)/usr/share/ns-migration/dhcp
endef
 
$(eval $(call BuildPackage,ns-migration))
