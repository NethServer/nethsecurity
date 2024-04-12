#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-phonehome
PKG_VERSION:=0.0.3
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-phonehome-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-phonehome
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity controller client
	URL:=https://github.com/NethServer/nethsecurity-controller/
	DEPENDS:=+lscpu +pciutils +python3-uuid
	PKGARCH:=all
endef
 
define Package/ns-phonehome/description
	Send statistical data to remote server
endef

define Package/ns-phonehome/conffiles
/etc/config/phonehome
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-phonehome/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  (. /etc/uci-defaults/20_ns-phonehome)
  rm -f /etc/uci-defaults/20_ns-phonehome
  /etc/init.d/cron restart
fi
exit 0
endef

define Package/ns-phonehome/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  crontab -l | grep -v "/usr/sbin/send-phonehome" | sort | uniq | crontab -
fi
exit 0
endef

define Package/ns-phonehome/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/phonehome $(1)/usr/sbin/
	$(INSTALL_BIN) ./files/send-phonehome $(1)/usr/sbin
	$(INSTALL_BIN) ./files/20_ns-phonehome $(1)/etc/uci-defaults
	$(INSTALL_CONF) ./files/config $(1)/etc/config/phonehome
endef
 
$(eval $(call BuildPackage,ns-phonehome))
