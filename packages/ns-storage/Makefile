#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-storage
PKG_VERSION:=0.0.7
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-storage-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-storage
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity storage manager
	URL:=https://github.com/NethServer/nethsecurity/
	DEPENDS:=+parted +block-mount +logrotate +rsync
	PKGARCH:=all
endef
 
define Package/ns-storage/description
	Manage data storage
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-storage/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  crontab -l | grep -q '/usr/sbin/logrotate /etc/logrotate.conf' || echo '5 1 * * * /usr/sbin/logrotate /etc/logrotate.conf' >> /etc/crontabs/root
  /etc/init.d/cron restart
fi
exit 0
endef

define Package/ns-storage/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	crontab -l | grep -v "/usr/sbin/logrotate /etc/logrotate.conf" | sort | uniq | crontab -
fi
exit 0
endef


define Package/ns-storage/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_DIR) $(1)/etc/logrotate.d
	$(INSTALL_DIR) $(1)/usr/libexec
	$(INSTALL_DIR) $(1)/usr/libexec/sync-data
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/add-storage $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-storage-setup-partition $(1)/usr/libexec
	$(INSTALL_BIN) ./files/ns-storage-setup-disk $(1)/usr/libexec
	$(INSTALL_BIN) ./files/ns-storage-has-free-space $(1)/usr/libexec
	$(INSTALL_BIN) ./files/remove-storage $(1)/usr/sbin
	$(INSTALL_BIN) ./files/rotate-messages $(1)/usr/sbin
	$(INSTALL_BIN) ./files/sync-data $(1)/usr/sbin
	$(INSTALL_BIN) ./files/openvpn $(1)/usr/libexec/sync-data
	$(INSTALL_CONF) ./files/30_ns-storage $(1)/etc/uci-defaults
	$(INSTALL_CONF) ./files/data.conf $(1)/etc/logrotate.d
	$(INSTALL_BIN) ./files/storage-status $(1)/usr/sbin
	$(INSTALL_BIN) ./files/storage-alarm $(1)/usr/libexec
	$(INSTALL_BIN) ./files/ns-storage-check.init $(1)/etc/init.d/ns-storage-check
endef
 
$(eval $(call BuildPackage,ns-storage))
