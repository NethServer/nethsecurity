#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-api
PKG_VERSION:=0.0.25
PKG_RELEASE:=1
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-api-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-api
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity REST API
	URL:=https://github.com/NethServer/nethsecurity-controller/
	DEPENDS:=+python3-nethsec +python3-openssl +python3-urllib +python3-idna
	PKGARCH:=all
endef

define Package/ns-api/conffiles
/etc/config/ns-api
/etc/config/templates
endef
 
define Package/ns-api/description
	Configure NethSecurity using REST APIs
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
	$(INSTALL_DIR) $(1)/usr/sbin/
	$(INSTALL_DIR) $(1)/usr/libexec/ns-api/
	$(INSTALL_BIN) ./files/api-cli $(1)/usr/bin/
	$(INSTALL_BIN) ./files/ns.talkers $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.talkers.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.ovpntunnel $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.ovpntunnel.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.ovpnrw $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.ovpnrw.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.smtp $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.smtp.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.firewall $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.firewall.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.flashstart $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.log.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.log $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.flashstart.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.dpireport $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.dpireport.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.dedalo $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.dedalo.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.power $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.power.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.qos $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.qos.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.routes $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.routes.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.dashboard $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.dashboard.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.subscription $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.subscription.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.don $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.don.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.dhcp $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.dhcp.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.dns $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.dns.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.redirects $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.redirects.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.mwan $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.mwan.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.dpi $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.dpi.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.netdata $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.netdata.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.storage $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.storage.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.account $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.account.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.backup $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.backup.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.migration $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.migration.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.ipsectunnel $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.ipsectunnel.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.factoryreset $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.factoryreset.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.update $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.update.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.ssh $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.ssh.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_DATA) ./files/schedule-system-update $(1)/usr/libexec/ns-api/
	$(INSTALL_BIN) ./files/ns.reverseproxy $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.reverseproxy.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.devices $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.devices.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.users $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.users.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_DIR) $(1)/lib/upgrade/keep.d
	$(INSTALL_CONF) files/msmtp.keep $(1)/lib/upgrade/keep.d/msmtp
	$(LN) /usr/bin/msmtp $(1)/usr/sbin/sendmail
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) ./files/config $(1)/etc/config/ns-api
	$(INSTALL_CONF) ./files/templates $(1)/etc/config/
endef
 
$(eval $(call BuildPackage,ns-api))
