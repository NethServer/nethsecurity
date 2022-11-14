#
# Copyright (C) 2022 eGloo, Incorporated
#

include $(TOPDIR)/rules.mk

PKG_NAME:=netify-plugin-stats
PKG_RELEASE:=1
PKG_MAINTAINER:=Darryl Sokoloski <darryl@egloo.ca>
PKG_LICENSE:=UNLICENSED

PKG_BUILD_PARALLEL:=1
PKG_FIXUP:=autoreconf
PKG_INSTALL:=1

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=file:///home/build/openwrt/netify-agent-stats-plugin
PKG_SOURCE_DATE:=2022-09-07
#PKG_SOURCE_VERSION:=v1.0.11
PKG_SOURCE_VERSION:=6d3a37d9035ddf01b8c969b3b687fb8b0e3f6ab1
PKG_MIRROR_HASH:=whatever

include $(INCLUDE_DIR)/package.mk

define Package/netify-plugin-stats
  SECTION:=libs
  CATEGORY:=Libraries
  TITLE:=Netify Agent Statistics Plugin
  URL:=http://www.netify.ai/
  DEPENDS:=+netifyd @!USE_UCLIBC
  # Explicitly depend on libstdcpp rather than $(CXX_DEPENDS).  At the moment
  # std::unordered_map is only available via libstdcpp which is required for
  # performance reasons.
  DEPENDS+=+libstdcpp
endef

define Package/netify-plugin-stats/description
Writes agent and flow statistics to JSON log files on a configurable interval.
endef

define Package/netify-plugin-stats/conffiles
/etc/netify.d/netify-plugin-stats.json
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
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetify-plugin-stats.{a,so*} $(1)/usr/lib/
endef

define Package/netify-plugin-stats/install
	$(INSTALL_DIR) $(1)/usr/lib
	$(INSTALL_DIR) $(1)/etc/netify.d
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetify-plugin-stats.so.* $(1)/usr/lib/
	$(INSTALL_DATA) ./files/netify-plugin-stats.json $(1)/etc/netify.d/
endef

$(eval $(call BuildPackage,netify-plugin-stats))
