#
# Copyright (C) 2022 Nethesis
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-rsyslog
PKG_VERSION:=0.0.1
PKG_RELEASE:=$(AUTORELEASE)
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-rsyslog-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-rsyslog
	SECTION:=base
	CATEGORY:=NextSecurity
	TITLE:=NextSecurity UCI configuration for rsyslog
	URL:=https://github.com/NethServer/nextsecurity-controller/
	DEPENDS:=+rsyslog
	PKGARCH:=all
endef
 
define Package/ns-rsyslog/description
	UCI configuration support for rsyslog
endef

define Package/ns-rsyslog/conffiles
	/etc/config/rsyslog
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-rsyslog/install
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_BIN) ./files/ns-rsyslog.init $(1)/etc/init.d/ns-rsyslog
	$(INSTALL_CONF) ./files/config $(1)/etc/config/rsyslog
endef
 
$(eval $(call BuildPackage,ns-rsyslog))
