#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-api
PKG_VERSION:=0.0.1
PKG_RELEASE:=$(AUTORELEASE)
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-api-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-api
	SECTION:=base
	CATEGORY:=NextSecurity
	TITLE:=NextSecurity REST API
	URL:=https://github.com/NethServer/nextsecurity-controller/
	DEPENDS:=+python3-nextsec +python3-openssl +python3-urllib +python3-idna
	PKGARCH:=all
endef
 
define Package/ns-api/description
	Configure NextSecurity using REST APIs
endef

define Package/ns-api/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  /etc/init.d/rpcd restart
fi
exit 0
endef

define Package/ns-api/postrm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  /etc/init.d/rpcd restart
fi
exit 0
endef


# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-api/install
	$(INSTALL_DIR) $(1)/usr/libexec/rpcd/
	$(INSTALL_DIR) $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_DIR) $(1)/usr/bin/
	$(INSTALL_BIN) ./files/api-cli $(1)/usr/bin/
	$(INSTALL_BIN) ./files/ns.talkers $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.talkers.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.ovpntunnel $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.ovpntunnel.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.smtp $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.smtp.json $(1)/usr/share/rpcd/acl.d/
endef
 
$(eval $(call BuildPackage,ns-api))
