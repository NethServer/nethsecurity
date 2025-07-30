#
# Copyright (C) 2022 Nethesis
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk

PKG_NAME:=ns-dpi
PKG_VERSION:=0.1.0
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/ns-dpi-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk

# TODO: fix this with proper dependencies when specs for V5 arrive
define Package/ns-dpi
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=DPI rules
	URL:=https://github.com/NethServer/nethsecurity/
	DEPENDS:=+kmod-ipt-conntrack-label
	PKGARCH:=all
endef

define Package/ns-dpi/description
	Traffic rules for network flows
endef

define Package/ns-dpi/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
  (. /etc/uci-defaults/20_dpi)
  rm -f /etc/uci-defaults/20_dpi
  /etc/init.d/cron restart
fi
exit 0
endef

define Package/ns-dpi/prerm
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	crontab -l | grep -v "/usr/sbin/dpi-update" | sort | uniq | crontab -
fi
exit 0
endef

define Package/ns-plug/conffiles
/etc/config/dpi
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-dpi/install
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_DIR) $(1)/etc/xtables
	$(INSTALL_DIR) $(1)/usr/share/ns-plug/hooks/unregister
	$(INSTALL_CONF) ./files/connlabel.conf $(1)/etc/xtables
	$(INSTALL_BIN) ./files/dpi.init $(1)/etc/init.d/dpi
	$(INSTALL_BIN) ./files/dpi $(1)/usr/sbin/
	$(INSTALL_BIN) ./files/dpi-nft $(1)/usr/sbin/
	$(INSTALL_BIN) ./files/dpi-config $(1)/usr/sbin/
	$(INSTALL_BIN) ./files/dpi-update $(1)/usr/sbin/
	$(INSTALL_CONF) ./files/20_dpi $(1)/etc/uci-defaults
	$(INSTALL_DIR) $(1)/usr/share/ns-plug/hooks/register
	$(INSTALL_BIN) ./files/70dpi $(1)/usr/share/ns-plug/hooks/unregister/
	$(LN) /usr/sbin/dpi-update $(1)/usr/share/ns-plug/hooks/register/80dpi-update
endef

$(eval $(call BuildPackage,ns-dpi))
