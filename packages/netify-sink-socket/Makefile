#
# Copyright (C) 2024 eGloo, Incorporated
#

include $(TOPDIR)/rules.mk

PKG_NAME:=netify-sink-socket
PKG_VERSION:=2025-10-01-v1.0.76
PKG_RELEASE:=3
PKG_MAINTAINER:=Darryl Sokoloski <darryl@egloo.ca>
PKG_LICENSE:=UNLICENSED

PKG_BUILD_PARALLEL:=1
PKG_FIXUP:=autoreconf
PKG_INSTALL:=1

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://gitlab.com/netify.ai/public/netify-plugins/netify-sink-socket.git
PKG_SOURCE_VERSION:=v1.0.76-3
#PKG_SOURCE_VERSION:=293b247ea12a17f65558ed9769a5f2b22dfc6d93
PKG_SOURCE_SUBDIR:=$(PKG_NAME)-$(PKG_VERSION)-$(PKG_RELEASE)
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)
PKG_MIRROR_HASH:=whatever

PKG_CONFIG_DEPENDS:= \
	CONFIG_NETIFY_SINK_SOCKET_WITH_STDCPP17

include $(INCLUDE_DIR)/package.mk

define Package/netify-sink-socket
  SECTION:=libs
  CATEGORY:=Libraries
  TITLE:=Netify Socket Sink Plugin
  URL:=http://www.netify.ai/
  DEPENDS:=+netifyd @!USE_UCLIBC
  # Explicitly depend on libstdcpp rather than $(CXX_DEPENDS).  At the moment
  # std::unordered_map is only available via libstdcpp which is required for
  # performance reasons.
  DEPENDS+=+libstdcpp
  EXTRA_DEPENDS:=netifyd (=2025-10-01-v5.1.24-r1)
endef

define Package/netify-sink-socket/description
This sink plugin accepts payloads from processor plugins and writes them to one or more configurable sockets.
endef

define Package/netify-sink-socket/conffiles
/etc/netifyd/netify-sink-socket.json
/etc/netifyd/plugins.d/10-netify-sink-socket.conf
endef

TARGET_CFLAGS+=-ffunction-sections -fdata-sections -Wno-psabi
TARGET_CXXFLAGS+=-ffunction-sections -fdata-sections -Wno-psabi
TARGET_LDFLAGS+=-Wl,--gc-sections

CONFIGURE_ARGS+= \
	$(if $(CONFIG_NETIFY_SINK_SOCKET_WITH_STDCPP17),--with-stdcpp=17,--with-stdcpp=11)

define Build/Configure
	(cd $(PKG_BUILD_DIR); ./autogen.sh)
	$(call Build/Configure/Default,$(CONFIGURE_ARGS))
endef

define Build/InstallDev
	$(INSTALL_DIR) $(1)/usr/lib
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetify-sink-socket.{a,so*} $(1)/usr/lib/
endef

define Package/netify-sink-socket/install
	$(INSTALL_DIR) $(1)/usr/lib
	$(INSTALL_DIR) $(1)/etc/netifyd/plugins.d
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetify-sink-socket.so.* $(1)/usr/lib/
	$(INSTALL_CONF) ./files/netify-sink-socket.json $(1)/etc/netifyd/
	$(INSTALL_CONF) ./files/plugins.d/10-netify-sink-socket.conf $(1)/etc/netifyd/plugins.d/
endef

$(eval $(call BuildPackage,netify-sink-socket))
