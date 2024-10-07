#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-objects
PKG_VERSION:=0.0.8
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-objects-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-objects
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity controller client
	URL:=https://github.com/NethServer/nethsecurity-controller/
	DEPENDS:=+python3-nethsec
	PKGARCH:=all
endef
 
define Package/ns-objects/description
	Manage firewall objects and users
endef

define Package/ns-objects/conffiles
/etc/config/objects
/etc/config/users
endef

define Package/ns-objects/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  (. /etc/uci-defaults/20_ns_objects)
  rm -f /etc/uci-defaults/20_ns_objects
  /etc/init.d/cron restart
fi
exit 0
endef

define Package/ns-objects/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
    crontab -l | grep -v "/usr/sbin/ns-objects-reload-dns" | sort | uniq | crontab -
fi
exit 0
endef


# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-objects/install
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/20_ns_objects $(1)/etc/uci-defaults
	$(INSTALL_CONF) ./files/objects $(1)/etc/config/
	$(INSTALL_CONF) ./files/users $(1)/etc/config/
	$(INSTALL_BIN) ./files/ns-objects-reload-dns $(1)/usr/bin/
endef
 
$(eval $(call BuildPackage,ns-objects))
