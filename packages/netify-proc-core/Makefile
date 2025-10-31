#
# Copyright (C) 2024 eGloo, Incorporated
#

include $(TOPDIR)/rules.mk

PKG_NAME:=netify-proc-core
PKG_VERSION:=2025-10-01-v1.0.94
PKG_RELEASE:=25
PKG_MAINTAINER:=Darryl Sokoloski <darryl@egloo.ca>
PKG_LICENSE:=UNLICENSED

PKG_BUILD_PARALLEL:=1
PKG_FIXUP:=autoreconf
PKG_INSTALL:=1

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://gitlab.com/netify.ai/public/netify-plugins/netify-proc-core.git
PKG_SOURCE_VERSION:=v1.0.94-25
#PKG_SOURCE_VERSION:=28721dc550b1a534ba3e5b7abf7cd9e7daa011bb
PKG_SOURCE_SUBDIR:=$(PKG_NAME)-$(PKG_VERSION)-$(PKG_RELEASE)
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)
PKG_MIRROR_HASH:=whatever

PKG_CONFIG_DEPENDS:= \
	CONFIG_NETIFY_PROC_CORE_WITH_STDCPP17

include $(INCLUDE_DIR)/package.mk

define Package/netify-proc-core
  SECTION:=libs
  CATEGORY:=Libraries
  TITLE:=Netify Core Processor Plugin
  URL:=http://www.netify.ai/
  DEPENDS:=+netifyd @!USE_UCLIBC
  # Explicitly depend on libstdcpp rather than $(CXX_DEPENDS).  At the moment
  # std::unordered_map is only available via libstdcpp which is required for
  # performance reasons.
  DEPENDS+=+libstdcpp
  EXTRA_DEPENDS:=netifyd (=2025-10-01-v5.1.24-r2)
endef

define Package/netify-proc-core/description
The core processor plugin encodes flow events and Agent status updates into various output formats such as JSON or MSGPACK with optional compression support.  The encoded results can then be dispatched to one or more sink plugins for transport or storage.
endef

define Package/netify-proc-core/conffiles
/etc/netifyd/netify-proc-core.json
/etc/netifyd/plugins.d/10-netify-proc-core.conf
endef

TARGET_CFLAGS+=-ffunction-sections -fdata-sections -Wno-psabi
TARGET_CXXFLAGS+=-ffunction-sections -fdata-sections -Wno-psabi
TARGET_LDFLAGS+=-Wl,--gc-sections

CONFIGURE_ARGS+= \
	$(if $(CONFIG_NETIFY_PROC_CORE_WITH_STDCPP17),--with-stdcpp=17,--with-stdcpp=11)

define Build/Configure
	(cd $(PKG_BUILD_DIR); ./autogen.sh)
	$(call Build/Configure/Default,$(CONFIGURE_ARGS))
endef

define Build/InstallDev
	$(INSTALL_DIR) $(1)/usr/lib
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetify-proc-core.{a,so*} $(1)/usr/lib/
endef

define Package/netify-proc-core/install
	$(INSTALL_DIR) $(1)/usr/lib
	$(INSTALL_DIR) $(1)/etc/netifyd/plugins.d
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetify-proc-core.so.* $(1)/usr/lib/
	$(INSTALL_CONF) ./files/netify-proc-core.json $(1)/etc/netifyd/
	$(INSTALL_CONF) ./files/plugins.d/10-netify-proc-core.conf $(1)/etc/netifyd/plugins.d/
endef

$(eval $(call BuildPackage,netify-proc-core))
