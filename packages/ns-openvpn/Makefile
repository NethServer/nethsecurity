#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-openvpn
PKG_VERSION:=0.0.1
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-openvpn-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-openvpn
	SECTION:=base
	CATEGORY:=NextSecurity
	TITLE:=Threat shield block list
	URL:=https://github.com/NethServer/nextsecurity/
	DEPENDS:=+openvpn +openvpn-easy-rsa +python3-sqlite3 +python3-nextsec
	PKGARCH:=all
endef
 
define Package/ns-openvpn/description
	Nextsecurity OpenVPN extensions
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-openvpn/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/usr/libexec/ns-openvpn/connect-scripts
	$(INSTALL_DIR) $(1)/usr/libexec/ns-openvpn/disconnect-scripts

	$(INSTALL_BIN) ./files/ns-openvpnrw-setup $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-openvpnrw-add $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-openvpnrw-init-pki $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-openvpnrw-print-client $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-openvpnrw-revoke  $(1)/usr/sbin
	$(INSTALL_BIN) ./files/openvpn-connect $(1)/usr/libexec/ns-openvpn/
	$(INSTALL_BIN) ./files/openvpn-disconnect $(1)/usr/libexec/ns-openvpn/
	$(INSTALL_BIN) ./files/init-connections-db $(1)/usr/libexec/ns-openvpn/
	$(INSTALL_BIN) ./files/openvpn-local-auth $(1)/usr/libexec/ns-openvpn/
	$(INSTALL_BIN) ./files/01-check-status $(1)/usr/libexec/ns-openvpn/connect-scripts
	$(INSTALL_BIN) ./files/10-static-lease $(1)/usr/libexec/ns-openvpn/connect-scripts
	$(INSTALL_BIN) ./files/10-tunnel-iroute $(1)/usr/libexec/ns-openvpn/connect-scripts
	$(INSTALL_BIN) ./files/80-save-connection $(1)/usr/libexec/ns-openvpn/connect-scripts
	$(INSTALL_BIN) ./files/80-save-disconnection $(1)/usr/libexec/ns-openvpn/disconnect-scripts
endef

define Package/ns-openvpn/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  grep '/usr/libexec/ns-openvpn/init-connections-db' /etc/openvpn.user || echo "/usr/libexec/ns-openvpn/init-connections-db" >> /etc/openvpn.user
  /usr/sbin/ns-openvpnrw-setup
fi
exit 0
endef

define Package/ns-openvpn/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
    sed -i '/\/usr\/libexec\/ns-openvpn\/init-connections-db/d' /etc/openvpn.user
fi
exit 0
endef

$(eval $(call BuildPackage,ns-openvpn))
