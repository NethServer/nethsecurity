#
# Copyright (C) 2024 eGloo, Incorporated
#

include $(TOPDIR)/rules.mk

PKG_NAME:=netify-sink-log
PKG_VERSION:=2025-07-01-v1.0.62
PKG_RELEASE:=6
PKG_MAINTAINER:=Darryl Sokoloski <darryl@egloo.ca>
PKG_LICENSE:=UNLICENSED

PKG_BUILD_PARALLEL:=1
PKG_FIXUP:=autoreconf
PKG_INSTALL:=1

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://gitlab.com/netify.ai/public/netify-plugins/netify-sink-log.git
PKG_SOURCE_VERSION:=v1.0.62-6
#PKG_SOURCE_VERSION:=be9eaf655d6e13ea7e78ad36dd27a5d6c30ded0e
PKG_SOURCE_SUBDIR:=$(PKG_NAME)-$(PKG_VERSION)-$(PKG_RELEASE)
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)
PKG_MIRROR_HASH:=whatever

include $(INCLUDE_DIR)/package.mk

define Package/netify-sink-log
  SECTION:=libs
  CATEGORY:=Libraries
  TITLE:=Netify Log Sink Plugin
  URL:=http://www.netify.ai/
  DEPENDS:=+netifyd @!USE_UCLIBC
  # Explicitly depend on libstdcpp rather than $(CXX_DEPENDS).  At the moment
  # std::unordered_map is only available via libstdcpp which is required for
  # performance reasons.
  DEPENDS+=+libstdcpp
  EXTRA_DEPENDS:=netifyd (=2025-07-01-v5.1.12-r1)
endef

define Package/netify-sink-log/description
This sink plugin saves payloads to configurable log files from one or more processor plugins.
endef

define Package/netify-sink-log/conffiles
/etc/netifyd/netify-sink-log.json
/etc/netifyd/plugins.d/10-netify-sink-log.conf
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
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetify-sink-log.{a,so*} $(1)/usr/lib/
endef

define Package/netify-sink-log/install
	$(INSTALL_DIR) $(1)/usr/lib
	$(INSTALL_DIR) $(1)/etc/netifyd/plugins.d
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetify-sink-log.so.* $(1)/usr/lib/
	$(INSTALL_CONF) $(PKG_INSTALL_DIR)/etc/netifyd/netify-sink-log.json $(1)/etc/netifyd/
	$(INSTALL_CONF) $(PKG_INSTALL_DIR)/etc/netifyd/plugins.d/10-netify-sink-log.conf $(1)/etc/netifyd/plugins.d/
endef

$(eval $(call BuildPackage,netify-sink-log))
