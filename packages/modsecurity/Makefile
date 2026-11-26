#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=modsecurity
# renovate: datasource=github-releases depName=owasp-modsecurity/ModSecurity
PKG_VERSION:=3.0.17
PKG_RELEASE:=1

PKG_SOURCE:=modsecurity-v$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://github.com/owasp-modsecurity/ModSecurity/releases/download/v$(PKG_VERSION)/
PKG_HASH:=f283b33d5c21130fd3a15c84a93a1abe12bd1949edaf44288b12af571b671a50
PKG_BUILD_DIR:=$(BUILD_DIR)/modsecurity-v$(PKG_VERSION)

PKG_LICENSE:=Apache-2.0
PKG_LICENSE_FILES:=LICENSE

PKG_BUILD_PARALLEL:=1
PKG_INSTALL:=1

include $(INCLUDE_DIR)/package.mk

define Package/libmodsecurity
  SECTION:=libs
  CATEGORY:=Libraries
  TITLE:=ModSecurity v3 web application firewall library
  URL:=https://github.com/owasp-modsecurity/ModSecurity
  DEPENDS:=+libstdcpp +libpcre2 +yajl +libxml2 +lmdb +libcurl +curl +jsonfilter
endef

define Package/libmodsecurity/description
  libModSecurity is the engine of the ModSecurity v3 web application firewall.
endef

CONFIGURE_ARGS += \
	--disable-static \
	--disable-examples \
	--with-pcre2=$(STAGING_DIR)/usr \
	--with-yajl=$(STAGING_DIR)/usr \
	--with-libxml=$(STAGING_DIR)/usr \
	--with-lmdb=$(STAGING_DIR)/usr \
	--with-curl=$(STAGING_DIR)/usr \
	--without-lua \
	--without-maxmind \
	--without-geoip \
	--without-ssdeep

define Build/InstallDev
	$(INSTALL_DIR) $(1)/usr/include $(1)/usr/lib
	$(CP) $(PKG_INSTALL_DIR)/usr/include/modsecurity $(1)/usr/include/
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libmodsecurity.so* $(1)/usr/lib/
endef

define Package/libmodsecurity/conffiles
/etc/modsecurity/modsecurity.conf
/etc/nginx/conf.d/modsecurity.conf
endef

define Package/libmodsecurity/install
	$(INSTALL_DIR) $(1)/usr/lib $(1)/usr/sbin $(1)/etc/modsecurity $(1)/etc/nginx/conf.d $(1)/etc/rsyslog.d/rules.d
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libmodsecurity.so.* $(1)/usr/lib/
	$(INSTALL_BIN) ./files/modsecurity-crs-update $(1)/usr/sbin/
	$(INSTALL_CONF) ./files/modsecurity.conf $(1)/etc/modsecurity/modsecurity.conf
	$(INSTALL_CONF) ./files/crs.conf $(1)/etc/modsecurity/crs.conf
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/unicode.mapping $(1)/etc/modsecurity/
	$(INSTALL_CONF) ./files/nginx-modsecurity.conf $(1)/etc/nginx/conf.d/modsecurity.conf
	$(INSTALL_DATA) ./files/rsyslog-rules.conf $(1)/etc/rsyslog.d/rules.d/modsecurity.conf
endef

$(eval $(call BuildPackage,libmodsecurity))
