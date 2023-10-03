#
# Copyright (C) 2022 eGloo, Incorporated
#

include $(TOPDIR)/rules.mk

PKG_NAME:=netify-flow-actions
PKG_RELEASE:=1
PKG_MAINTAINER:=Darryl Sokoloski <darryl@egloo.ca>
PKG_LICENSE:=UNLICENSED

PKG_BUILD_PARALLEL:=1
PKG_FIXUP:=autoreconf
PKG_INSTALL:=1

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=file:///home/build/openwrt/netify-flow-actions
PKG_SOURCE_DATE:=2023-25-09
PKG_SOURCE_VERSION:=9daa0174804ae72de78cb21373b4e13ed2ba7dd6
PKG_MIRROR_HASH:=whatever

PKG_CONFIG_DEPENDS:= \
	CONFIG_NETIFY_FLOW_ACTIONS_TARGET_LOG \
	CONFIG_NETIFY_FLOW_ACTIONS_TARGET_CTLABEL \
	CONFIG_NETIFY_FLOW_ACTIONS_TARGET_IPSET \
	CONFIG_NETIFY_FLOW_ACTIONS_TARGET_NFTSET

include $(INCLUDE_DIR)/package.mk

define Package/netify-flow-actions
  SECTION:=libs
  CATEGORY:=Libraries
  TITLE:=Netify Agent Flow Actions Plugin
  URL:=http://www.netify.ai/
  DEPENDS:=+netifyd @!USE_UCLIBC
  # Explicitly depend on libstdcpp rather than $(CXX_DEPENDS).  At the moment
  # std::unordered_map is only available via libstdcpp which is required for
  # performance reasons.
  DEPENDS+=+libstdcpp
  # Target dependencies.
  DEPENDS+=+NETIFY_FLOW_ACTIONS_TARGET_CTLABEL:libnetfilter-conntrack
  DEPENDS+=+NETIFY_FLOW_ACTIONS_TARGET_IPSET:libipset
  DEPENDS+=+NETIFY_FLOW_ACTIONS_TARGET_NFTSET:nftables
  EXTRA_DEPENDS:=netifyd (>=4.4.1-1)
endef

define Package/netify-flow-actions/description
The Flow Actions Plugin for the Netify Agent applies user-defined criteria to
new flow detections in real-time.  Matching flows are passed to one or more
Action Targets for further processing.
endef

define Package/netify-flow-actions/config
	source "$(SOURCE)/Config.in"
endef

define Package/netify-flow-actions/conffiles
/etc/netify.d/netify-flow-actions.json
endef

TARGET_CFLAGS+=-ffunction-sections -fdata-sections -Wno-psabi
TARGET_CXXFLAGS+=-ffunction-sections -fdata-sections -Wno-psabi
TARGET_LDFLAGS+=-Wl,--gc-sections

CONFIGURE_ARGS += \
	$(if $(CONFIG_NETIFY_FLOW_ACTIONS_TARGET_CTLABEL),,--disable-target-ctlabel) \
	$(if $(CONFIG_NETIFY_FLOW_ACTIONS_TARGET_IPSET),,--disable-target-ipset) \
	$(if $(CONFIG_NETIFY_FLOW_ACTIONS_TARGET_NFTSET),,--disable-target-nftset)

define Build/Configure
	(cd $(PKG_BUILD_DIR); ./autogen.sh)
	$(call Build/Configure/Default,$(CONFIGURE_ARGS))
endef

define Build/InstallDev
	$(INSTALL_DIR) $(1)/usr/lib
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetify-flow-actions.{a,so*} $(1)/usr/lib/
endef

define Package/netify-flow-actions/install
	$(INSTALL_DIR) $(1)/usr/lib
	$(INSTALL_DIR) $(1)/etc/netify.d
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetify-flow-actions.so.* $(1)/usr/lib/
	$(INSTALL_DATA) $(PKG_INSTALL_DIR)/etc/netify.d/netify-flow-actions.json $(1)/etc/netify.d/
endef

$(eval $(call BuildPackage,netify-flow-actions))
