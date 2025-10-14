#
# Copyright (C) 2024 eGloo, Incorporated
#

include $(TOPDIR)/rules.mk

PKG_NAME:=netify-sink-http
PKG_VERSION:=2025-10-01-v1.0.64
PKG_RELEASE:=22
PKG_MAINTAINER:=Darryl Sokoloski <darryl@egloo.ca>
PKG_LICENSE:=UNLICENSED

PKG_BUILD_PARALLEL:=1
PKG_FIXUP:=autoreconf
PKG_INSTALL:=1

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://gitlab.com/netify.ai/public/netify-plugins/netify-sink-http.git
PKG_SOURCE_VERSION:=v1.0.64-22
#PKG_SOURCE_VERSION:=dbf248cd9f5832b3301fd431eefd78f2ece8fd97
PKG_SOURCE_SUBDIR:=$(PKG_NAME)-$(PKG_VERSION)-$(PKG_RELEASE)
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)
PKG_MIRROR_HASH:=whatever

PKG_CONFIG_DEPENDS:= \
	CONFIG_NETIFY_SINK_HTTP_WITH_STDCPP17

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
  EXTRA_DEPENDS:=netifyd (=2025-10-01-v5.1.24-r1)
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

CONFIGURE_ARGS+= \
	$(if $(CONFIG_NETIFY_SINK_HTTP_WITH_STDCPP17),--with-stdcpp=17,--with-stdcpp=11)

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
