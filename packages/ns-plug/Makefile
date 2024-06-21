#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-plug
PKG_VERSION:=0.0.10
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-plug-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-plug
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity controller client
	URL:=https://github.com/NethServer/nethsecurity-controller/
	DEPENDS:=+openvpn +lscpu +python3-nethsec +python3-yaml
	PKGARCH:=all
endef
 
define Package/ns-plug/description
	Register and connect the firewall to a NethSecurity controller instance
endef

define Package/ns-plug/conffiles
/etc/config/ns-plug
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-plug/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  (. /etc/uci-defaults/20_ns-plug)
  rm -f /etc/uci-defaults/20_ns-plug
  /etc/init.d/cron restart
fi
exit 0
endef

define Package/ns-plug/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  crontab -l | grep -v "/usr/sbin/send-backup" | sort | uniq | crontab -
  crontab -l | grep -v "/usr/sbin/send-inventory" | sort | uniq | crontab -
  crontab -l | grep -v "/usr/sbin/send-heartbeat" | sort | uniq | crontab -
fi
exit 0
endef

define Package/ns-plug/install
	$(INSTALL_DIR) $(1)/usr/share/ns-plug
	$(INSTALL_DIR) $(1)/usr/share/ns-plug/hooks/register
	$(INSTALL_DIR) $(1)/usr/share/ns-plug/hooks/unregister
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_DIR) $(1)/etc/netdata
	$(INSTALL_DIR) $(1)/lib/upgrade/keep.d
	$(INSTALL_DIR) $(1)/usr/lib/netdata/python.d/
	$(INSTALL_BIN) ./files/ns-plug.init $(1)/etc/init.d/ns-plug
	$(INSTALL_BIN) ./files/ns-plug $(1)/usr/sbin/ns-plug
	$(INSTALL_BIN) ./files/distfeed-setup $(1)/usr/sbin/distfeed-setup
	$(INSTALL_BIN) ./files/remote-backup $(1)/usr/sbin
	$(INSTALL_BIN) ./files/send-backup $(1)/usr/sbin
	$(INSTALL_BIN) ./files/send-heartbeat $(1)/usr/sbin
	$(INSTALL_BIN) ./files/send-inventory $(1)/usr/sbin
	$(INSTALL_BIN) ./files/register $(1)/usr/sbin
	$(INSTALL_BIN) ./files/unregister $(1)/usr/sbin
	$(INSTALL_BIN) ./files/subscription-info $(1)/usr/sbin
	$(INSTALL_BIN) ./files/inventory $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-download $(1)/usr/bin
	$(INSTALL_BIN) ./files/20_ns-plug $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/30_ns-plug_alerts $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/netadata_enable_alerts $(1)/usr/share/ns-plug/hooks/register/70netadata_enable_alerts
	$(INSTALL_BIN) ./files/netadata_disable_alerts $(1)/usr/share/ns-plug/hooks/unregister/70netadata_disable_alerts
	$(INSTALL_BIN) ./files/enable_automatic_updates $(1)/usr/share/ns-plug/hooks/register/60enable_automatic_updates
	$(INSTALL_BIN) ./files/disable_automatic_updates $(1)/usr/share/ns-plug/hooks/unregister/60disable_automatic_updates
	$(INSTALL_CONF) ./files/config $(1)/etc/config/ns-plug
	$(INSTALL_CONF) files/ns-plug.keep $(1)/lib/upgrade/keep.d/ns-plug
	$(INSTALL_CONF) files/health_alarm_notify.conf $(1)/etc/netdata
	$(INSTALL_DATA) files/mwan.chart.py $(1)/usr/lib/netdata/python.d/
endef
 
$(eval $(call BuildPackage,ns-plug))
