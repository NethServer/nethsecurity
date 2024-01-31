#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-migration
PKG_VERSION:=0.0.3
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-migration-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-migration
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NS7 2 NethSecurity migration
	URL:=https://github.com/NethServer/nethsecurity/tree/master/packages/ns-migration
	DEPENDS:=+python3-nethsec
	PKGARCH:=all
endef
 
define Package/ns-migration/description
	Import NS7 firewall configuration
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-migration/install
	$(INSTALL_DIR) $(1)/usr/share/ns-migration
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) ./files/ns-import $(1)/usr/sbin/ns-import
	$(INSTALL_BIN) ./files/zonename2timezone $(1)/usr/bin/zonename2timezone
	$(INSTALL_BIN) ./files/scripts/passwd $(1)/usr/share/ns-migration/10passwd
	$(INSTALL_BIN) ./files/scripts/time $(1)/usr/share/ns-migration/10time
	$(INSTALL_BIN) ./files/scripts/network $(1)/usr/share/ns-migration/20network
	$(INSTALL_BIN) ./files/scripts/routes $(1)/usr/share/ns-migration/20routes
	$(INSTALL_BIN) ./files/scripts/wan $(1)/usr/share/ns-migration/20wan
	$(INSTALL_BIN) ./files/scripts/dhcp $(1)/usr/share/ns-migration/30dhcp
	$(INSTALL_BIN) ./files/scripts/dns $(1)/usr/share/ns-migration/30dns
	$(INSTALL_BIN) ./files/scripts/ssh $(1)/usr/share/ns-migration/30ssh
	$(INSTALL_BIN) ./files/scripts/subscription $(1)/usr/share/ns-migration/30subscription
	$(INSTALL_BIN) ./files/scripts/openvpn $(1)/usr/share/ns-migration/40openvpn
	$(INSTALL_BIN) ./files/scripts/openvpn_tunnels $(1)/usr/share/ns-migration/40openvpn_tunnels
	$(INSTALL_BIN) ./files/scripts/ipsec $(1)/usr/share/ns-migration/40ipsec
	$(INSTALL_BIN) ./files/scripts/hotspot $(1)/usr/share/ns-migration/40hotspot
	$(INSTALL_BIN) ./files/scripts/rules $(1)/usr/share/ns-migration/50rules
	$(INSTALL_BIN) ./files/scripts/redirects $(1)/usr/share/ns-migration/50redirects
	$(INSTALL_BIN) ./files/scripts/reverse_proxy $(1)/usr/share/ns-migration/60reverse_proxy
	$(INSTALL_BIN) ./files/scripts/threat_shield $(1)/usr/share/ns-migration/70threat_shield
	$(INSTALL_BIN) ./files/scripts/flashstart $(1)/usr/share/ns-migration/70flashstart
	$(INSTALL_BIN) ./files/scripts/acme $(1)/usr/share/ns-migration/80acme
	$(INSTALL_DATA) ./files/scripts/nsmigration.py $(1)/usr/share/ns-migration/
endef
 
$(eval $(call BuildPackage,ns-migration))
