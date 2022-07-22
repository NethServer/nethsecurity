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
	DEPENDS:=+wget-ssl +adblock +jq
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
	$(INSTALL_BIN) ./files/ts-ip.init $(1)/etc/init.d/ts-ip
	$(INSTALL_BIN) ./files/ts-dns.init $(1)/etc/init.d/ts-dns
	$(INSTALL_BIN) ./files/ts-ip $(1)/usr/sbin/ts-ip
	$(INSTALL_BIN) ./files/ts-ip-download $(1)/usr/sbin/ts-ip-download
	$(INSTALL_BIN) ./files/ts-ip-nft $(1)/usr/sbin/ts-ip-nft
	$(INSTALL_CONF) ./files/20_threat_shield $(1)/etc/uci-defaults
	$(INSTALL_DIR) $(1)/usr/share/threat_shield
	$(INSTALL_DATA) ./files/nethesis-ip.sources $(1)/usr/share/threat_shield
	$(INSTALL_DATA) ./files/nethesis-dns.sources $(1)/usr/share/threat_shield
	gzip -9n $(1)/usr/share/threat_shield/nethesis-ip.sources
	gzip -9n $(1)/usr/share/threat_shield/nethesis-dns.sources
endef

define Package/ns-threat_shield/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  crontab -l | grep -q '/usr/sbin/ts-ip' || echo '*/50 * * * * sleep $$(( RANDOM % 3500 )); /usr/sbin/ts-ip' >> /etc/crontabs/root
  crontab -l | grep -q '/etc/init.d/ts-dns' || echo '1 */12 * * * sleep $$(( RANDOM % 3600 )); /etc/init.d/ts-dns reload' >> /etc/crontabs/root
  /etc/init.d/cron restart
  /etc/init.d/ts-ip enable
fi
exit 0
endef

define Package/ns-threat_shield/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
    uci set threat_shield.config.status=0
	uci commit
	/usr/sbin/ts-ip
	crontab -l | grep -v "/usr/sbin/ts-ip" | sort | uniq | crontab -
	crontab -l | grep -v "/etc/init.d/ts-dns" | sort | uniq | crontab -
fi
exit 0
endef

define Package/ns-threat_shield/postrm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
    rm -rf /var/ns-ip/ /var/ns-dns/
fi
exit 0
endef

$(eval $(call BuildPackage,ns-threat_shield))
