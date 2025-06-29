#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-ha
PKG_VERSION:=0.0.1
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-ha-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-ha
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity HA configuration
	URL:=https://github.com/NethServer/nethsecurity/
	DEPENDS:=+keepalived +conntrackd
	PKGARCH:=all
endef
 
define Package/ns-ha/description
	Support High Availability configuration for NethSecurity
endef

# this is required, otherwise compile will fail
define Build/Compile
endef


define Package/ns-ha/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DIR) $(1)/lib/functions/keepalived
	$(INSTALL_DIR) $(1)/usr/libexec
	$(INSTALL_DIR) $(1)/etc/keepalived/scripts/
	$(INSTALL_DIR) $(1)/etc/profile.d/
	$(INSTALL_BIN) ./files/ns-ha-disable $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-ha-enable $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-ha-export $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-ha-import $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-ha-config $(1)/usr/sbin
	$(INSTALL_DATA) ./files/400-network $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/500-nathelpers $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/500-netmap $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/560-mac-binding $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/600-backup $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/600-openvpn $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/600-mwan3 $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/600-users-objects $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/600-qosify $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/600-snort $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/600-ipsec $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/600-acme $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/700-nginx $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/800-adblock $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/800-banip $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/800-netifyd $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/800-flashstart $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/800-ui $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/800-dedalo $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/900-ns-plug $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/900-phonehome $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/900-msmtp $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/900-snmpd $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/900-ddns $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/100-conntrackd $(1)/etc/hotplug.d/keepalived
	$(INSTALL_DATA) ./files/ns.sh $(1)/lib/functions/keepalived
	$(INSTALL_DATA) ./files/99-ns-ha.sh $(1)/etc/profile.d
	$(INSTALL_BIN) ./files/conntrackd.sh $(1)/usr/libexec/
	$(INSTALL_BIN) ./files/ns-rsync.sh $(1)/usr/libexec/
endef
 
$(eval $(call BuildPackage,ns-ha))
