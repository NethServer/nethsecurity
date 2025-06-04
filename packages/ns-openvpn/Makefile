#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-openvpn
PKG_VERSION:=1.0.0
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-openvpn-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-openvpn
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity OpenVPN extensions
	URL:=https://github.com/NethServer/nethsecurity/
	DEPENDS:=+openvpn +openvpn-easy-rsa +python3-sqlite3 +python3-nethsec +openldap-utils +qrencode +python3-pyotp
	PKGARCH:=all
endef
 
define Package/ns-openvpn/description
	NethSecurity OpenVPN extensions
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-openvpn/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_DIR) $(1)/usr/libexec/ns-openvpn/connect-scripts
	$(INSTALL_DIR) $(1)/usr/libexec/ns-openvpn/disconnect-scripts
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/ns-openvpnrw-add $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-openvpnrw-init-pki $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-openvpnrw-extend-crl $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns-openvpntunnel-add-client $(1)/usr/sbin
	$(INSTALL_BIN) ./files/openvpn-connect $(1)/usr/libexec/ns-openvpn/
	$(INSTALL_BIN) ./files/openvpn-disconnect $(1)/usr/libexec/ns-openvpn/
	$(INSTALL_BIN) ./files/init-connections-db $(1)/usr/libexec/ns-openvpn/
	$(INSTALL_BIN) ./files/openvpn-local-auth $(1)/usr/libexec/ns-openvpn/
	$(INSTALL_BIN) ./files/openvpn-remote-auth $(1)/usr/libexec/ns-openvpn/
	$(INSTALL_BIN) ./files/openvpn-otp-auth $(1)/usr/libexec/ns-openvpn/
	$(INSTALL_BIN) ./files/01-check-status $(1)/usr/libexec/ns-openvpn/connect-scripts
	$(INSTALL_BIN) ./files/10-static-lease $(1)/usr/libexec/ns-openvpn/connect-scripts
	$(INSTALL_BIN) ./files/10-tunnel-iroute $(1)/usr/libexec/ns-openvpn/connect-scripts
	$(INSTALL_BIN) ./files/80-save-connection $(1)/usr/libexec/ns-openvpn/connect-scripts
	$(INSTALL_BIN) ./files/80-save-disconnection $(1)/usr/libexec/ns-openvpn/disconnect-scripts
	$(INSTALL_BIN) ./files/99_ns-openvpn $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/99_ns-openvpn-renew-crl $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/openvpn-status $(1)/usr/bin
	$(INSTALL_BIN) ./files/openvpn-kill $(1)/usr/bin
endef

define Package/ns-openvpn/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
    sed -i '/\/usr\/libexec\/ns-openvpn\/init-connections-db/d' /etc/openvpn.user
fi
exit 0
endef

define Package/ns-openvpn/postinst
#!/bin/sh
/usr/sbin/ns-openvpnrw-extend-crl
exit 0
endef

$(eval $(call BuildPackage,ns-openvpn))
