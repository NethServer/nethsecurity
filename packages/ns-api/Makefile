#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-api
PKG_VERSION:=3.3.0
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
	DEPENDS:=+python3-nethsec +python3-openssl +python3-urllib +python3-idna +python3-requests +python3-paramiko
	PKGARCH:=all
endef

define Package/ns-api/conffiles
/etc/config/ns-api
/etc/config/ns-wizard
endef
 
define Package/ns-api/description
	Configure NethSecurity using REST APIs
endef

define Package/ns-api/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  /etc/init.d/rpcd restart
fi
/usr/share/ns-api/remove-pppoe-keepalive
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
	$(INSTALL_DIR) $(1)/usr/share/ns-api/
	$(INSTALL_DIR) $(1)/usr/bin/
	$(INSTALL_DIR) $(1)/usr/sbin/
	$(INSTALL_DIR) $(1)/usr/libexec/ns-api/
	$(INSTALL_DIR) $(1)/usr/libexec/ns-api/pre-commit
	$(INSTALL_DIR) $(1)/usr/libexec/ns-api/post-commit
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
	$(INSTALL_BIN) ./files/ns.report $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.report.json $(1)/usr/share/rpcd/acl.d/
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
	$(INSTALL_BIN) ./files/schedule-system-update $(1)/usr/libexec/ns-api/
	$(INSTALL_BIN) ./files/schedule-automatic-updates $(1)/usr/libexec/ns-api/
	$(INSTALL_BIN) ./files/ns.reverseproxy $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.reverseproxy.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.devices $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.devices.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.users $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.users.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.commit $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.commit.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.netmap $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.netmap.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.threatshield $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.threatshield.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.nat $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.nat.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.plug $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.plug.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.netifyd $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.netifyd.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.controller $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.controller.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.conntrack $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.conntrack.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.scan $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.scan.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.wireguard $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.wireguard.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.objects $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.objects.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.snort $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.snort.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.nathelpers $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.nathelpers.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.wizard $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.wizard.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_BIN) ./files/ns.ha $(1)/usr/libexec/rpcd/
	$(INSTALL_DATA) ./files/ns.ha.json $(1)/usr/share/rpcd/acl.d/
	$(INSTALL_DIR) $(1)/lib/upgrade/keep.d
	$(INSTALL_CONF) files/msmtp.keep $(1)/lib/upgrade/keep.d/msmtp
	$(INSTALL_CONF) files/nat-helpers.keep $(1)/lib/upgrade/keep.d/nat-helpers
	$(LN) /usr/bin/msmtp $(1)/usr/sbin/sendmail
	$(INSTALL_BIN) ./files/load-kernel-modules $(1)/usr/sbin/load-kernel-modules
	$(INSTALL_BIN) ./files/firewall-apply-default-logging $(1)/usr/sbin/firewall-apply-default-logging
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) ./files/config/ns-api $(1)/etc/config/ns-api
	$(INSTALL_CONF) ./files/config/ns-wizard $(1)/etc/config/ns-wizard
	$(INSTALL_CONF) ./files/templates $(1)/etc/config/
	$(INSTALL_BIN) ./files/post-commit/restart-netdata.py $(1)/usr/libexec/ns-api/post-commit/
	$(INSTALL_BIN) ./files/pre-commit/fix-redirect-reflections.py $(1)/usr/libexec/ns-api/pre-commit
	$(INSTALL_BIN) ./files/pre-commit/update-objects.py $(1)/usr/libexec/ns-api/pre-commit
	$(INSTALL_BIN) ./files/post-commit/configure-netifyd.py $(1)/usr/libexec/ns-api/post-commit
	$(INSTALL_BIN) ./files/post-commit/reload-ipsets.py $(1)/usr/libexec/ns-api/post-commit
	$(INSTALL_BIN) ./files/post-commit/restart-cron.py $(1)/usr/libexec/ns-api/post-commit
	$(INSTALL_BIN) ./files/pre-commit/clean-network.py $(1)/usr/libexec/ns-api/pre-commit
	$(INSTALL_BIN) ./files/remove-pppoe-keepalive $(1)/usr/share/ns-api
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/uci-defaults/99-ns-api.ipsec $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/uci-defaults/99-ns-api.dropbear $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/uci-defaults/19-ns-api.wizard $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/uci-defaults/99-ns-api.synflood $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/uci-defaults/99-ns-api.dnsmasq $(1)/etc/uci-defaults
endef
 
$(eval $(call BuildPackage,ns-api))
