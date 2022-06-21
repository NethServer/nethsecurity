#
# Copyright (C) 2022 Nethesis
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-threat_shield
PKG_VERSION:=0.0.1
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-threat_shield-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-threat_shield
	SECTION:=base
	CATEGORY:=NextSecurity
	TITLE:=Threat shield block list
	URL:=https://github.com/NethServer/nextsecurity/
	DEPENDS:=+git-http
	PKGARCH:=all
endef
 
define Package/ns-threat_shield/description
	Download and apply block lists
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-threat_shield/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/threat_shield.init $(1)/etc/init.d/threat_shield
	$(INSTALL_BIN) ./files/ts $(1)/usr/sbin/ts
	$(INSTALL_BIN) ./files/ts-download $(1)/usr/sbin/ts-download
	$(INSTALL_BIN) ./files/ts-nft $(1)/usr/sbin/ts-nft
	$(INSTALL_CONF) ./files/20_threat_shield $(1)/etc/uci-defaults
endef

define Package/ns-threat_shield/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  crontab -l | grep -q '/usr/sbin/ts' || echo '*/20 * * * * sleep $$(( RANDOM % 90 )); /usr/sbin/ts' >> /etc/crontabs/root
  /etc/init.d/cron restart
  /etc/init.d/threat_shield enable
fi
exit 0
endef

define Package/ns-threat_shield/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
    uci set threat_shield.config.status=0
	uci commit
	/usr/sbin/ts
	crontab -l | grep -v "/usr/sbin/ts" | sort | uniq | crontab -
fi
exit 0
endef

define Package/ns-threat_shield/postrm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
    rm -rf /var/ns-threat_shield/
fi
exit 0
endef

$(eval $(call BuildPackage,ns-threat_shield))
