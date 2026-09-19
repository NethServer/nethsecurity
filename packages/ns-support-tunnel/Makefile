#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=ns-support-tunnel
PKG_VERSION:=0.0.1
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/ns-support-tunnel-$(PKG_VERSION)

PKG_MAINTAINER:=Edoardo Spadoni <edoardo.spadoni@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk

define Package/ns-support-tunnel
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=WebSocket-based remote support tunnel (coexists with don)
	URL:=https://github.com/NethServer/nethsecurity/
	DEPENDS:=+jq
endef

define Package/ns-support-tunnel/description
	WebSocket-based remote support client using tunnel-client.
	Coexists with the existing OpenVPN-based don support system.
endef

# No compilation needed - binary is pre-built
define Build/Compile
endef

define Package/ns-support-tunnel/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/usr/libexec/rpcd
	$(INSTALL_DIR) $(1)/usr/share/rpcd/acl.d
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_DIR) $(1)/usr/share/my/users.d
	$(INSTALL_DIR) $(1)/usr/share/my/diagnostics.d
	$(INSTALL_BIN) ./files/support-tunnel $(1)/usr/sbin
	$(INSTALL_BIN) ./files/tunnel-client $(1)/usr/sbin
	$(INSTALL_BIN) ./files/ns.support-tunnel $(1)/usr/libexec/rpcd
	$(INSTALL_DATA) ./files/ns.support-tunnel.json $(1)/usr/share/rpcd/acl.d
	$(INSTALL_BIN) ./files/health $(1)/usr/share/my/diagnostics.d
	$(INSTALL_CONF) ./files/20_ns_support_tunnel $(1)/etc/uci-defaults
endef

$(eval $(call BuildPackage,ns-support-tunnel))
