#
# Copyright (C) 2022 Nethesis
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-dedalo
PKG_VERSION:=0.0.4
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-dedalo-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://github.com/nethesis/icaro.git
PKG_SOURCE_VERSION:=v85

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-dedalo
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Dedalo Network Access Controller, runs on the firewall and intercepts all guest connections
	URL:=https://github.com/nethesis/icaro
	DEPENDS:=+curl +grep +ca-bundle +haserl +uuidgen +coova-chilli +ethtool
	PKGARCH:=all
endef
 
define Package/ns-dedalo/description
	Dedalo is the Network Access Controller, runs on the firewall and intercepts all guest connections.
	It's a configuration helper for Coova-Chilli
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-dedalo/conffiles
/etc/config/dedalo
endef

define Package/ns-dedalo/firewall_config

set firewall.ns_hs_include=include
set firewall.ns_hs_include.type='script'
set firewall.ns_hs_include.path='/opt/icaro/dedalo/dedalo.user'
set firewall.ns_hs_include.fw4_compatible='1'

commit

endef

define Package/ns-dedalo/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
uci batch <<EOF
$(Package/ns-dedalo/firewall_config)
EOF
else
echo uci batch "<<EOF" "$(Package/ns-dedalo/firewall_config)""EOF" >> $${IPKG_INSTROOT}/etc/uci-defaults/dedalo
echo "exit 0" >> $${IPKG_INSTROOT}/etc/uci-defaults/dedalo
fi
exit 0
endef

define Package/ns-dedalo/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/dedalo/dedalo $(1)/usr/bin/
	$(INSTALL_BIN) files/unregister_dedalo $(1)/usr/bin/

	$(INSTALL_DIR) $(1)/usr/sbin

	$(INSTALL_DIR) $(1)/opt/icaro/dedalo
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/dedalo/config $(1)/opt/icaro/dedalo/config
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/dedalo/dedalo_users_auth.sh $(1)/opt/icaro/dedalo/
	$(INSTALL_BIN) files/dedalo.user $(1)/opt/icaro/dedalo/

	$(INSTALL_DIR) $(1)/opt/icaro/dedalo/template
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/dedalo/template/engine $(1)/opt/icaro/dedalo/template/engine
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/dedalo/template/chilli.conf.tpl $(1)/opt/icaro/dedalo/template/chilli.conf.tpl

	$(INSTALL_DIR) $(1)/opt/icaro/dedalo/walled_gardens/integrations
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/dedalo/walled_gardens/facebook.conf $(1)/opt/icaro/dedalo/walled_gardens/facebook.conf
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/dedalo/walled_gardens/linkedin.conf $(1)/opt/icaro/dedalo/walled_gardens/linkedin.conf
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/dedalo/walled_gardens/instagram.conf $(1)/opt/icaro/dedalo/walled_gardens/instagram.conf
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/dedalo/walled_gardens/wifi4eu.conf $(1)/opt/icaro/dedalo/walled_gardens/wifi4eu.conf

	$(INSTALL_DIR) $(1)/opt/icaro/dedalo/www
	$(INSTALL_BIN) files/redirect.chi $(1)/opt/icaro/dedalo/www/redirect.chi

	touch $(1)/opt/icaro/dedalo/local.conf
	touch $(1)/opt/icaro/dedalo/walled_gardens/local.conf

	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) files/dedalo.init $(1)/etc/init.d/dedalo
	$(INSTALL_BIN) files/dedalo_users_auth.init $(1)/etc/init.d/dedalo_users_auth
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DATA) files/dedalo.config $(1)/etc/config/dedalo

	$(INSTALL_DIR) $(1)/lib/upgrade/keep.d
	$(INSTALL_CONF) files/dedalo.keep $(1)/lib/upgrade/keep.d/dedalo
endef
 
$(eval $(call BuildPackage,ns-dedalo))
