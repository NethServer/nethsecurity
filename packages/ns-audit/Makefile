#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=ns-audit
PKG_VERSION:=0.0.1
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/ns-audit-$(PKG_VERSION)

PKG_MAINTAINER:=Tommaso Bailetti <tommaso.bailetti@nethesis.it>
PKG_LICENSE:=GPL-2.0-only

include $(INCLUDE_DIR)/package.mk

define Package/ns-audit
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Netfilter audit logging
	URL:=https://github.com/NethServer/nethsecurity/
	DEPENDS:=+ulogd +ulogd-mod-nflog +ulogd-mod-extra +ulogd-mod-syslog \
		+rsyslog +victoria-logs
	PKGARCH:=all
endef

define Package/ns-audit/description
	Collect nftables NFLOG records with ulogd and forward them to syslog,
	keeping firewall logging off the kernel ring buffer and the console.
endef

define Package/ns-audit/conffiles
/etc/ns-audit/ulogd.conf
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-audit/install
	$(INSTALL_DIR) $(1)/etc/ns-audit
	$(INSTALL_CONF) ./files/ulogd.conf $(1)/etc/ns-audit/ulogd.conf
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/ns-audit.init $(1)/etc/init.d/ns-audit
endef

$(eval $(call BuildPackage,ns-audit))
