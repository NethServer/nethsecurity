#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=ns-audit
PKG_VERSION:=0.1.0
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-2.0-only

include $(INCLUDE_DIR)/package.mk

define Package/ns-audit
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity on-device audit collector
	URL:=https://github.com/NethServer/nethsecurity
	DEPENDS:=+python3 +python3-nethsec +python3-jinja2
	PKGARCH:=all
endef

define Package/ns-audit/description
	Read-only local audit evidence collector for NethSecurity.
endef

define Package/ns-audit/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ] && [ -x /etc/init.d/rpcd ]; then
	/etc/init.d/rpcd restart
fi
exit 0
endef

define Package/ns-audit/postrm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ] && [ -x /etc/init.d/rpcd ]; then
	/etc/init.d/rpcd restart
fi
exit 0
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-audit/install
	$(INSTALL_DIR) $(1)/usr/libexec/rpcd
	$(INSTALL_BIN) ./files/ns.audit $(1)/usr/libexec/rpcd/ns.audit
	$(INSTALL_DIR) $(1)/usr/share/rpcd/acl.d
	$(INSTALL_DATA) ./files/ns.audit.json $(1)/usr/share/rpcd/acl.d/ns.audit.json
	$(INSTALL_DIR) $(1)/usr/share/ns-audit
	$(CP) ./files/ns_audit $(1)/usr/share/ns-audit/
endef

$(eval $(call BuildPackage,ns-audit))
