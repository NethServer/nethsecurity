#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-3.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=ns-clm
PKG_VERSION:=0.0.1
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/ns-clm-$(PKG_VERSION)

PKG_MAINTAINER:=Nethesis <nethesis@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk

define Package/ns-clm
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Cloud Log Manager forwarder
	URL:=https://github.com/NethServer/nethsecurity/
	DEPENDS:=+python3-urllib
	PKGARCH:=all
endef

define Package/ns-clm/description
	Forward syslog messages to the Nethesis Cloud Log Manager service
endef

define Package/ns-clm/conffiles
/etc/config/ns-clm
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-clm/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  /etc/init.d/ns-clm stop 2>/dev/null
  /etc/init.d/ns-clm disable 2>/dev/null
fi
exit 0
endef

define Package/ns-clm/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/ns-clm-forwarder $(1)/usr/sbin/
	$(INSTALL_BIN) ./files/ns-clm.init $(1)/etc/init.d/ns-clm
	$(INSTALL_CONF) ./files/config $(1)/etc/config/ns-clm
endef

$(eval $(call BuildPackage,ns-clm))
