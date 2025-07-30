#
# Copyright (C) 2024 eGloo, Incorporated
#

include $(TOPDIR)/rules.mk

PKG_NAME:=netify-sink-http
PKG_VERSION:=2025-07-01-v1.0.64
PKG_RELEASE:=6
PKG_MAINTAINER:=Darryl Sokoloski <darryl@egloo.ca>
PKG_LICENSE:=UNLICENSED

PKG_BUILD_PARALLEL:=1
PKG_FIXUP:=autoreconf
PKG_INSTALL:=1

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://gitlab.com/netify.ai/public/netify-plugins/netify-sink-http.git
PKG_SOURCE_VERSION:=v1.0.64-6
#PKG_SOURCE_VERSION:=afee9d5ecd9ca88d2d951be92ba067b854bbe5ce
PKG_SOURCE_SUBDIR:=$(PKG_NAME)-$(PKG_VERSION)-$(PKG_RELEASE)
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)
PKG_MIRROR_HASH:=whatever

include $(INCLUDE_DIR)/package.mk

define Package/netify-sink-http
  SECTION:=libs
  CATEGORY:=Libraries
  TITLE:=Netify HTTP Sink Plugin
  URL:=http://www.netify.ai/
  DEPENDS:=+netifyd @!USE_UCLIBC
  # Explicitly depend on libstdcpp rather than $(CXX_DEPENDS).  At the moment
  # std::unordered_map is only available via libstdcpp which is required for
  # performance reasons.
  DEPENDS+=+libstdcpp +libcurl
  EXTRA_DEPENDS:=netifyd (=2025-07-01-v5.1.12-r1)
endef

define Package/netify-sink-http/description
This plugin uploads processor plugin payloads to one or more HTTP servers.
endef

define Package/netify-sink-http/conffiles
/etc/netifyd/netify-sink-http.json
/etc/netifyd/plugins.d/10-netify-sink-http.conf
endef

TARGET_CFLAGS+=-ffunction-sections -fdata-sections -Wno-psabi
TARGET_CXXFLAGS+=-ffunction-sections -fdata-sections -Wno-psabi
TARGET_LDFLAGS+=-Wl,--gc-sections

define Build/Configure
	(cd $(PKG_BUILD_DIR); ./autogen.sh)
	$(call Build/Configure/Default,$(CONFIGURE_ARGS))
endef

define Build/InstallDev
	$(INSTALL_DIR) $(1)/usr/lib
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetify-sink-http.{a,so*} $(1)/usr/lib/
endef

define Package/netify-sink-http/install
	$(INSTALL_DIR) $(1)/usr/lib
	$(INSTALL_DIR) $(1)/etc/netifyd/plugins.d
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetify-sink-http.so.* $(1)/usr/lib/
	$(INSTALL_CONF) $(PKG_INSTALL_DIR)/etc/netifyd/netify-sink-http.json $(1)/etc/netifyd/
	$(INSTALL_CONF) $(PKG_INSTALL_DIR)/etc/netifyd/plugins.d/10-netify-sink-http.conf $(1)/etc/netifyd/plugins.d/
endef

$(eval $(call BuildPackage,netify-sink-http))
