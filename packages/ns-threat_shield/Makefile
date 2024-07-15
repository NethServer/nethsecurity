#
# Copyright (C) 2022 Nethesis
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-threat_shield
PKG_VERSION:=0.0.6
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-threat_shield-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-threat_shield
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Threat shield block list
	URL:=https://github.com/NethServer/nethsecurity/
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
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_DIR) $(1)/etc/banip
	$(INSTALL_DIR) $(1)/usr/share/ns-plug/hooks/register
	$(INSTALL_DIR) $(1)/usr/share/ns-plug/hooks/unregister
	$(INSTALL_DIR) $(1)/usr/libexec/ns-api/post-commit
	$(INSTALL_DIR) $(1)/usr/libexec/ns-api/pre-commit
	$(INSTALL_BIN) ./files/ts-dns $(1)/usr/sbin/ts-dns
	$(INSTALL_BIN) ./files/ts-ip $(1)/usr/sbin/ts-ip
	$(INSTALL_BIN) ./files/20_threat_shield $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/ts-dns.hook $(1)/usr/share/ns-plug/hooks/register/90ts-dns
	$(INSTALL_BIN) ./files/ts-dns.hook $(1)/usr/share/ns-plug/hooks/unregister/90ts-dns
	$(LN) /usr/sbin/ts-ip $(1)/usr/share/ns-plug/hooks/register/80ts-ip
	$(LN) /usr/sbin/ts-ip $(1)/usr/share/ns-plug/hooks/unregister/80ts-ip
	$(INSTALL_DIR) $(1)/usr/share/threat_shield
	$(INSTALL_DATA) ./files/nethesis-dns.sources $(1)/usr/share/threat_shield
	$(INSTALL_DATA) ./files/banip.nethesis.feeds $(1)/etc/banip
	$(INSTALL_BIN) ./files/adjust-banip.py $(1)/usr/libexec/ns-api/post-commit/
	$(INSTALL_BIN) ./files/configure-banip-wans.py $(1)/usr/libexec/ns-api/pre-commit/
	gzip -9n $(1)/usr/share/threat_shield/nethesis-dns.sources
endef

define Package/ns-threat_shield/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  (. /etc/uci-defaults/20_threat_shield)
  rm -f /etc/uci-defaults/20_threat_shield
  /etc/init.d/cron restart
fi
exit 0
endef

define Package/ns-threat_shield/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	crontab -l | grep -v "/etc/init.d/banip reload" | sort | uniq | crontab -
	crontab -l | grep -v "/etc/init.d/adblock" | sort | uniq | crontab -
fi
exit 0
endef

define Package/ns-threat_shield/postrm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
    rm -rf /var/ns-dns/
fi
exit 0
endef

$(eval $(call BuildPackage,ns-threat_shield))
