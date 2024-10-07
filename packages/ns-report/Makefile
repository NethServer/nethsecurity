#
# Copyright (C) 2023 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-report
PKG_VERSION:=0.0.3
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-report-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-report
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity reports
	URL:=https://github.com/NethServer/nethsecurity/
	DEPENDS:=+python3-nethsec +python3-logging
	PKGARCH:=all
endef
 
define Package/ns-report/description
	NethSecurity reports
endef

define Package/ns-report/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	crontab -l | grep -v "/usr/bin/dpireport-cleanup" | sort | uniq | crontab -
fi
exit 0
endef

define Package/ns-report/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  (. /etc/uci-defaults/20_ns-report)
  rm -f /etc/uci-defaults/20_ns-report
  /etc/init.d/cron restart
  /etc/init.d/dpireport restart
fi
exit 0
endef

define Package/ns-report/postrm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  /etc/init.d/dpireport restart
fi
exit 0
endef


# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-report/install
	$(INSTALL_DIR) $(1)/etc/init.d/
	$(INSTALL_DIR) $(1)/usr/bin/
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/dpireport $(1)/usr/bin/
	$(INSTALL_BIN) ./files/dpireport-cleanup $(1)/usr/bin/
	$(INSTALL_BIN) ./files/dpireport.init $(1)/etc/init.d/dpireport
	$(INSTALL_BIN) ./files/20_ns-report $(1)/etc/uci-defaults
endef
 
$(eval $(call BuildPackage,ns-report))
