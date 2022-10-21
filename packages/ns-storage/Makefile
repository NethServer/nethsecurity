#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-storage
PKG_VERSION:=0.0.1
PKG_RELEASE:=$(AUTORELEASE)
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-storage-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-storage
	SECTION:=base
	CATEGORY:=NextSecurity
	TITLE:=NextSecurity storage manager
	URL:=https://github.com/NethServer/nextsecurity/
	DEPENDS:=+parted +block-mount +logrotate
	PKGARCH:=all
endef
 
define Package/ns-storage/description
	Manage extra storage
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-storage/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  crontab -l | grep -q '/usr/sbin/logrotate' || echo '5 1 * * * /usr/sbin/logrotate' >> /etc/crontabs/root
  /etc/init.d/cron restart
fi
exit 0
endef

define Package/ns-storage/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	crontab -l | grep -v "/usr/sbin/logrotate" | sort | uniq | crontab -
fi
exit 0
endef


define Package/ns-storage/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_DIR) $(1)/etc/logrotate.d
	$(INSTALL_BIN) ./files/add-persistent-storage $(1)/usr/sbin
	$(INSTALL_BIN) ./files/rotate-messages $(1)/usr/sbin
	$(INSTALL_CONF) ./files/30_ns-storage $(1)/etc/uci-defaults
	$(INSTALL_CONF) ./files/extra.conf $(1)/etc/logrotate.d
endef
 
$(eval $(call BuildPackage,ns-storage))
