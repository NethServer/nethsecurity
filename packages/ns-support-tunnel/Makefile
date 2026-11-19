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
	DEPENDS:=@x86_64 +jq
endef

define Package/ns-support-tunnel/description
	WebSocket-based remote support client using tunnel-client.
	Coexists with the existing OpenVPN-based don support system.
endef

# No compilation needed: the binary is pre-built, verify its checksum
define Build/Compile
	cd $(CURDIR)/files && sha256sum -c tunnel-client-linux-amd64.sha256
endef

define Package/ns-support-tunnel/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/usr/libexec/rpcd
	$(INSTALL_DIR) $(1)/usr/share/rpcd/acl.d
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_DIR) $(1)/lib/upgrade/keep.d
	$(INSTALL_DIR) $(1)/usr/share/my/users.d
	$(INSTALL_DIR) $(1)/usr/share/my/diagnostics.d
	$(INSTALL_BIN) ./files/support-tunnel $(1)/usr/sbin
	$(INSTALL_BIN) ./files/tunnel-client-linux-amd64 $(1)/usr/sbin/tunnel-client
	$(INSTALL_BIN) ./files/support-tunnel.init $(1)/etc/init.d/support-tunnel-cleanup
	$(INSTALL_DATA) ./files/support-tunnel.keep $(1)/lib/upgrade/keep.d/ns-support-tunnel
	$(INSTALL_BIN) ./files/ns.support-tunnel $(1)/usr/libexec/rpcd
	$(INSTALL_DATA) ./files/ns.support-tunnel.json $(1)/usr/share/rpcd/acl.d
	$(INSTALL_BIN) ./files/health $(1)/usr/share/my/diagnostics.d
	$(INSTALL_CONF) ./files/20_ns_support_tunnel $(1)/etc/uci-defaults
endef

$(eval $(call BuildPackage,ns-support-tunnel))
