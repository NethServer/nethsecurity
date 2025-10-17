#
# Copyright (C) 2016-2024 eGloo Incorporated
#
# This is free software, licensed under the GNU General Public License v2.

include $(TOPDIR)/rules.mk

PKG_NAME:=netifyd
PKG_VERSION:=2025-10-01-v5.1.24
PKG_RELEASE:=2
PKG_MAINTAINER:=Darryl Sokoloski <darryl@egloo.ca>
PKG_LICENSE:=GPL-3.0-or-later

PKG_BUILD_PARALLEL:=1
PKG_FIXUP:=autoreconf
PKG_INSTALL:=1

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://gitlab.com/netify.ai/public/netify-agent.git
PKG_SOURCE_VERSION:=v5.1.24-2
#PKG_SOURCE_VERSION:=df4e3a7032dee9fa0ad619b5e860617c8334bab5
PKG_SOURCE_SUBDIR:=$(PKG_NAME)-$(PKG_VERSION)-$(PKG_RELEASE)
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)
PKG_MIRROR_HASH:=whatever

PKG_CONFIG_DEPENDS:= \
	CONFIG_NETIFYD_BUILD_SHARED_LIBRARY \
	CONFIG_NETIFYD_ENABLE_CONNTRACK_COUNTERS \
	CONFIG_NETIFYD_ENABLE_CONNTRACK_MDATA \
	CONFIG_NETIFYD_ENABLE_EXTENDED_STATS \
	CONFIG_NETIFYD_ENABLE_LEAN_AND_MEAN \
	CONFIG_NETIFYD_ENABLE_LINUX_CAPABILITIES \
	CONFIG_NETIFYD_ENABLE_NFQUEUE \
	CONFIG_NETIFYD_ENABLE_OPENWRT \
	CONFIG_NETIFYD_ENABLE_TPACKETV3 \
	CONFIG_NETIFYD_WITH_LOCAL_LIBGCRYPT \
	CONFIG_NETIFYD_WITH_STDCPP17

include $(INCLUDE_DIR)/package.mk

define Package/netifyd
  SECTION:=net
  CATEGORY:=Network
  TITLE:=Netify Agent
  URL:=http://www.netify.ai/
  DEPENDS:=+ca-bundle +libatomic +libcurl +libmnl +libnetfilter-conntrack \
	+libpcap +libpthread +zlib @!USE_UCLIBC
  # Explicitly depend on libstdcpp rather than $(CXX_DEPENDS).  At the moment
  # std::unordered_map is only available via libstdcpp which is required for
  # performance reasons.
  DEPENDS+=+libstdcpp
  DEPENDS+=+NETIFYD_WITH_LOCAL_LIBGCRYPT:libgcrypt
  DEPENDS+=+NETIFYD_WITH_LOCAL_LIBGCRYPT:libgpg-error
  DEPENDS+=+NETIFYD_ENABLE_LINUX_CAPABILITIES:libcap
  DEPENDS+=+NETIFYD_ENABLE_NFQUEUE:libnetfilter-queue
  DEPENDS+=+NETIFYD_ENABLE_OPENWRT:libubox
  DEPENDS+=+NETIFYD_ENABLE_OPENWRT:libblobmsg-json
  DEPENDS+=+NETIFYD_ENABLE_OPENWRT:libjson-c
  DEPENDS+=+NETIFYD_ENABLE_OPENWRT:libubus
  DEPENDS+=+NETIFYD_ENABLE_OPENWRT:libuci
endef

define Package/netifyd/description
The Netify Agent is a deep-packet inspection server which detects network
protocols and applications.  These detections can be saved locally, served over
a UNIX or TCP socket, and/or "pushed" (via HTTP POSTs) to a remote third-party
server.  Flow metadata, network statistics, and detection classifications are
JSON encoded for easy consumption by third-party applications.
endef

define Package/netifyd/config
	source "$(SOURCE)/Config.in"
endef

define Package/netifyd/conffiles
/etc/config/netifyd
/etc/netifyd/agent.uuid
/etc/netifyd/netify-apps.conf
/etc/netifyd/netify-categories.json
/etc/netifyd/serial.uuid
/etc/netifyd/site.uuid
/etc/netifyd.conf
endef

TARGET_CFLAGS+=-ffunction-sections -fdata-sections -Wno-psabi
TARGET_CXXFLAGS+=-ffunction-sections -fdata-sections -Wno-psabi
TARGET_LDFLAGS+=-Wl,--gc-sections

CONFIGURE_ARGS+= \
	$(if $(CONFIG_NETIFYD_BUILD_SHARED_LIBRARY),--enable-shared,--disable-shared) \
	$(if $(CONFIG_NETIFYD_ENABLE_CONNTRACK_COUNTERS),--enable-conntrack-counters,--disable-conntrack-counters) \
	$(if $(CONFIG_NETIFYD_ENABLE_CONNTRACK_MDATA),--enable-conntrack-mdata,--disable-conntrack-mdata) \
	$(if $(CONFIG_NETIFYD_ENABLE_EXTENDED_STATS),--enable-extended-stats,--disable-extended-stats) \
	$(if $(CONFIG_NETIFYD_ENABLE_LEAN_AND_MEAN),--enable-lean-and-mean,--disable-lean-and-mean) \
	$(if $(CONFIG_NETIFYD_ENABLE_LINUX_CAPABILITIES),--enable-capabilities,--disable-capabilities) \
	$(if $(CONFIG_NETIFYD_ENABLE_NFQUEUE),--enable-nfqueue,--disable-nfqueue) \
	$(if $(CONFIG_NETIFYD_ENABLE_OPENWRT),--enable-ubus,--disable-ubus) \
	$(if $(CONFIG_NETIFYD_ENABLE_OPENWRT),--enable-uci,--disable-uci) \
	$(if $(CONFIG_NETIFYD_ENABLE_TPACKETV3),--enable-tpacketv3,--disable-tpacketv3) \
	$(if $(CONFIG_NETIFYD_WITH_LOCAL_LIBGCRYPT),--with-local-libgcrypt,--without-local-libgcrypt) \
	$(if $(CONFIG_NETIFYD_WITH_STDCPP17),--with-stdcpp=17,--with-stdcpp=11) \
	--sharedstatedir=/var/run \
	--disable-libtcmalloc \
	--without-systemdsystemunitdir \
	--without-tmpfilesdir

ifneq ($(CONFIG_LIBCURL_ZLIB),y)
CONFIGURE_ARGS+= \
	--without-libcurl-zlib
endif

define Build/InstallDev
	$(INSTALL_DIR) $(STAGING_DIR)/usr/include/netifyd
	$(CP) $(PKG_INSTALL_DIR)/usr/include/netifyd/*.h $(STAGING_DIR)/usr/include/netifyd
	$(CP) $(PKG_INSTALL_DIR)/usr/include/netifyd/*.hpp $(STAGING_DIR)/usr/include/netifyd
	$(INSTALL_DIR) $(STAGING_DIR)/usr/include/netifyd/pcap-compat
	$(CP) $(PKG_INSTALL_DIR)/usr/include/netifyd/pcap-compat/*.h $(STAGING_DIR)/usr/include/netifyd/pcap-compat
	$(INSTALL_DIR) $(STAGING_DIR)/usr/include/netifyd/nlohmann
	$(CP) $(PKG_INSTALL_DIR)/usr/include/netifyd/nlohmann/*.hpp $(STAGING_DIR)/usr/include/netifyd/nlohmann
	$(INSTALL_DIR) $(STAGING_DIR)/usr/include/netifyd/radix
	$(CP) $(PKG_INSTALL_DIR)/usr/include/netifyd/radix/*.hpp $(STAGING_DIR)/usr/include/netifyd/radix
	$(INSTALL_DIR) $(STAGING_DIR)/usr/include/ndpi
	$(CP) $(PKG_INSTALL_DIR)/usr/include/ndpi/*.h $(STAGING_DIR)/usr/include/ndpi
	$(INSTALL_DIR) $(STAGING_DIR)/usr/lib
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetifyd.a $(STAGING_DIR)/usr/lib
	$(if $(CONFIG_NETIFYD_BUILD_SHARED_LIBRARY),$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetifyd.so.* $(STAGING_DIR)/usr/lib,)
	$(INSTALL_DIR) $(STAGING_DIR)/usr/lib/pkgconfig
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/pkgconfig/libnetifyd.pc $(STAGING_DIR)/usr/lib/pkgconfig
endef

define Package/netifyd/install
	$(INSTALL_DIR) $(1)/etc
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/deploy/netifyd.conf $(1)/etc
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_CONF) ./files/netifyd.config $(1)/etc/config/netifyd
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/netifyd.init $(1)/etc/init.d/netifyd
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_BIN) $(PKG_INSTALL_DIR)/usr/sbin/netifyd $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/usr/lib
	$(if $(CONFIG_NETIFYD_BUILD_SHARED_LIBRARY),$(CP) $(PKG_INSTALL_DIR)/usr/lib/libnetifyd.so* $(1)/usr/lib,)
	$(INSTALL_DIR) $(1)/etc/netifyd
	$(INSTALL_DIR) $(1)/etc/netifyd/categories.d
	$(INSTALL_DIR) $(1)/etc/netifyd/profiles.d
	$(CP) $(PKG_INSTALL_DIR)/etc/netifyd/profiles.d/* $(1)/etc/netifyd/profiles.d
	$(INSTALL_DIR) $(1)/etc/netifyd/interfaces.d
	$(CP) $(PKG_INSTALL_DIR)/etc/netifyd/interfaces.d/* $(1)/etc/netifyd/interfaces.d
	$(INSTALL_DIR) $(1)/etc/netifyd/plugins.d
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/deploy/netify-apps.conf $(1)/etc/netifyd
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/deploy/netify-categories.json $(1)/etc/netifyd
	$(INSTALL_DIR) $(1)/usr/share/netifyd/plugins.d
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/deploy/functions.sh $(1)/usr/share/netifyd
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/deploy/netify-apps.conf $(1)/usr/share/netifyd
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/deploy/*.json $(1)/usr/share/netifyd
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/deploy/plugins.d/*.conf $(1)/usr/share/netifyd/plugins.d
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/99-netify-v4-migrate.uci-default $(1)/etc/uci-defaults/99-netify-v4-migrate
endef

$(eval $(call BuildPackage,netifyd))
