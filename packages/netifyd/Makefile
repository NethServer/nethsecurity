include $(TOPDIR)/rules.mk

PKG_NAME:=netifyd
NETIFYD_VERSION:=5.2.8
PKG_VERSION:=$(NETIFYD_VERSION)
PKG_RELEASE:=1
PKG_MAINTAINER:=Darryl Sokoloski <darryl@egloo.ca>
PKG_LICENSE:=Unlicensed

# Base URL for downloads
NETIFYD_BASE_URL:=https://updates.nethsecurity.nethserver.org/netifyd-dist/netifyd-$(PKG_VERSION)/25.12.4/$(ARCH)
DL_DIR:=$(DL_DIR)/netifyd-$(PKG_VERSION)-$(ARCH)

# Per-architecture download hashes ($(ARCH) drives both the URL and these hashes)
ifeq ($(ARCH),aarch64)
NETIFYD_HASH_LIBNETIFYD:=117e925f8a3f9361d9b87ed13dd11b74d46bc59e072e98ee3dc6cfd40755537c
NETIFYD_HASH_PLM:=1f6e86a6660bc470b603bc83f7d1d6fc448c1b54eefeeee540c1a4fa03eb4f33
NETIFYD_HASH_PROC_AGGREGATOR:=11392b6684fe971dac6d1ed916285ecb6aa3746ea3726a76a87e81903bac334d
NETIFYD_HASH_PROC_CORE:=c6bacb7a0ffef953e8dc732c4c4b463dd271fc952f936576cf664bd5e450c0de
NETIFYD_HASH_PROC_FLOW_ACTIONS:=a93c5d46383fe9a1a0a7aad9ff7ccef6b9ad048ba91c6ffcfcb27c703a496c0d
NETIFYD_HASH_SINK_HTTP:=609f59738a37b740e43d6c2d35697bc69fefcb02ff531130b779b068dec2ee83
NETIFYD_HASH_SINK_LOG:=754dd2032ea5f4c0f3ff2cfeb9e817e8245535e3c02d9de413d925917ddc0a4f
NETIFYD_HASH_NETIFYD:=e33d4dd26a6e6fe0ccd445a7d149a462c0080f9d931a1ab9c8330b7e12fae504
else
NETIFYD_HASH_LIBNETIFYD:=b974f93c6aa5dd79a1b04b8adbe5f344a4f988883256a684f7b565080c938bba
NETIFYD_HASH_PLM:=7bb5a68672eb694fc1b4ed1c6da50a91a47f24f0b3d5c5beac840f6c6d0ab2d0
NETIFYD_HASH_PROC_AGGREGATOR:=9f062e8389b52ae817147271c68d8df92a5a738bf5635c07808d858c2ca08df2
NETIFYD_HASH_PROC_CORE:=8f742d684031fc6e3800798e6ea14a3d159950fc6a7ac159b5df466db00e88e9
NETIFYD_HASH_PROC_FLOW_ACTIONS:=0b2439d66bc1d90f6c5b47e4738a675e1af2c52f23a02f67bbfa363215ec238e
NETIFYD_HASH_SINK_HTTP:=edb9a2f35135accd8ccd0eb4ef632630c5282c48600bcf051d0b5ef5440cfd63
NETIFYD_HASH_SINK_LOG:=9fd92e440f037c34d53b2adb7d3c867c627d6431b6aee4ba60eeab4f098bad5b
NETIFYD_HASH_NETIFYD:=eb8cb8fded423fdbdb04dd2499a1c3f03b611f2e316af43bce7db22cffe6c238
endif

include $(INCLUDE_DIR)/package.mk

define Package/netifyd
	SECTION:=admin
	CATEGORY:=Administration
	TITLE:=Netify Binary Integration Package
	URL:=https://netify.ai/
	DEPENDS:= \
		+ca-bundle \
		+kmod-ipt-conntrack-label \
		+kmod-ipt-ipset \
		+libatomic \
		+libblobmsg-json \
		+libc \
		+libcap \
		+libcurl \
		+libgcrypt \
		+libgpg-error \
		+libipset \
		+libjson-c \
		+libmnl \
		+libnetfilter-conntrack \
		+libnetfilter-queue \
		+libopenssl \
		+libpcap \
		+libpthread \
		+libsqlite3 \
		+libstdcpp \
		+libubox \
		+libubus \
		+libuci \
		+nftables \
		+zlib \
		+zoneinfo-core
	USERID:=netify:netify
endef

define Package/netifyd/description
Netifyd meta package compiled for NethSecurity 8.
endef

define Package/netifyd/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
	# removed the table-pre script for fw4, reload it to remove the entries
	/etc/init.d/firewall reload >/dev/null 2>&1
	/etc/init.d/netifyd restart
fi
exit 0
endef

define Download/libnetifyd
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetifyd.so.4.0.0
  FILE:=libnetifyd.so.4.0.0
  HASH:=$(NETIFYD_HASH_LIBNETIFYD)
endef
$(eval $(call Download,libnetifyd))

define Download/libnetify-plm
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-plm.so.1.0.0
  FILE:=libnetify-plm.so.1.0.0
  HASH:=$(NETIFYD_HASH_PLM)
endef
$(eval $(call Download,libnetify-plm))

define Download/libnetify-proc-aggregator
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-proc-aggregator.so.0.0.0
  FILE:=libnetify-proc-aggregator.so.0.0.0
  HASH:=$(NETIFYD_HASH_PROC_AGGREGATOR)
endef
$(eval $(call Download,libnetify-proc-aggregator))

define Download/libnetify-proc-core
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-proc-core.so.0.0.0
  FILE:=libnetify-proc-core.so.0.0.0
  HASH:=$(NETIFYD_HASH_PROC_CORE)
endef
$(eval $(call Download,libnetify-proc-core))

define Download/libnetify-proc-flow-actions
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-proc-flow-actions.so.0.0.0
  FILE:=libnetify-proc-flow-actions.so.0.0.0
  HASH:=$(NETIFYD_HASH_PROC_FLOW_ACTIONS)
endef
$(eval $(call Download,libnetify-proc-flow-actions))

define Download/libnetify-sink-http
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-sink-http.so.0.0.0
  FILE:=libnetify-sink-http.so.0.0.0
  HASH:=$(NETIFYD_HASH_SINK_HTTP)
endef
$(eval $(call Download,libnetify-sink-http))

define Download/libnetify-sink-log
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-sink-log.so.0.0.0
  FILE:=libnetify-sink-log.so.0.0.0
  HASH:=$(NETIFYD_HASH_SINK_LOG)
endef
$(eval $(call Download,libnetify-sink-log))

define Download/netifyd
  URL:=$(NETIFYD_BASE_URL)/usr/sbin
  URL_FILE:=netifyd
  FILE:=netifyd
  HASH:=$(NETIFYD_HASH_NETIFYD)
endef
$(eval $(call Download,netifyd))

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	$(CP) $(DL_DIR)/libnetifyd.so.4.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-plm.so.1.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-proc-aggregator.so.0.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-proc-core.so.0.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-proc-flow-actions.so.0.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-sink-http.so.0.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-sink-log.so.0.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/netifyd $(PKG_BUILD_DIR)/netifyd
endef

define Build/Configure
	true
endef

define Build/Compile
	true
endef

define Package/netifyd/conffiles
/etc/config/netifyd
/etc/netifyd.conf
/etc/netifyd/agent.uuid
/etc/netifyd/netify-proc-core-auto.json
/etc/netifyd/netify-sink-http-auto.json
/etc/netifyd/plugins.d/99-netify-proc-core-auto.conf
/etc/netifyd/plugins.d/99-netify-sink-http-auto.conf
endef

define Package/netifyd/install
	$(INSTALL_DIR) $(1)/etc
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_DIR) $(1)/etc/netifyd
	$(INSTALL_DIR) $(1)/etc/netifyd/categories.d
	$(INSTALL_DIR) $(1)/etc/netifyd/interfaces.d
	$(INSTALL_DIR) $(1)/etc/netifyd/plugins.d
	$(INSTALL_DIR) $(1)/etc/netifyd/profiles.d
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_DIR) $(1)/usr
	$(INSTALL_DIR) $(1)/usr/lib
	$(INSTALL_DIR) $(1)/usr/sbin
	$(INSTALL_DIR) $(1)/usr/share
	$(INSTALL_DIR) $(1)/usr/share/netifyd
	$(INSTALL_DIR) $(1)/usr/share/netifyd/plugins.d
	$(INSTALL_DIR) $(1)/usr/share/nftables.d/table-pre

	# netifyd
	$(INSTALL_DATA) ./files/etc/config/netifyd $(1)/etc/config/netifyd
	$(INSTALL_BIN) ./files/etc/init.d/netifyd $(1)/etc/init.d/netifyd
	$(INSTALL_DATA) ./files/etc/netifyd.conf $(1)/etc/netifyd.conf
	$(INSTALL_DATA) ./files/etc/netifyd/interfaces.d/10-nfqueue.conf $(1)/etc/netifyd/interfaces.d/10-nfqueue.conf
	$(INSTALL_DATA) ./files/etc/netifyd/netify-apps.conf $(1)/etc/netifyd/netify-apps.conf
	$(INSTALL_DATA) ./files/etc/netifyd/netify-categories.json $(1)/etc/netifyd/netify-categories.json
	$(INSTALL_DATA) ./files/etc/netifyd/profiles.d/00-default.conf $(1)/etc/netifyd/profiles.d/00-default.conf
	$(INSTALL_BIN) ./files/etc/uci-defaults/99-netify-v4-migrate.uci-default $(1)/etc/uci-defaults/99-netify-v4-migrate
	$(INSTALL_BIN) ./files/etc/uci-defaults/99-netify-enable-nfqueue.uci-default $(1)/etc/uci-defaults/99-netify-enable-nfqueue
	$(INSTALL_BIN) ./files/etc/uci-defaults/99-netify-disable-autoconfig.uci-default $(1)/etc/uci-defaults/99-netify-disable-autoconfig
	$(INSTALL_BIN) ./files/etc/uci-defaults/99-netify-disable-coredumps.uci-default $(1)/etc/uci-defaults/99-netify-disable-coredumps
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/netifyd $(1)/usr/sbin/netifyd
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetifyd.so.4.0.0 $(1)/usr/lib/libnetifyd.so.4.0.0
	$(LN) /usr/lib/libnetifyd.so.4.0.0 $(1)/usr/lib/libnetifyd.so
	$(LN) /usr/lib/libnetifyd.so.4.0.0 $(1)/usr/lib/libnetifyd.so.4
	$(INSTALL_DATA) ./files/usr/share/netifyd/functions.sh $(1)/usr/share/netifyd/functions.sh
	$(INSTALL_DATA) ./files/usr/share/netifyd/netify-apps.conf $(1)/usr/share/netifyd/netify-apps.conf
	$(INSTALL_DATA) ./files/usr/share/netifyd/netify-categories.json $(1)/usr/share/netifyd/netify-categories.json
	$(INSTALL_DATA) ./files/usr/share/netifyd/netify-proc-core-auto.json $(1)/usr/share/netifyd/netify-proc-core-auto.json
	$(INSTALL_DATA) ./files/usr/share/netifyd/netify-sink-http-auto.json $(1)/usr/share/netifyd/netify-sink-http-auto.json
	$(INSTALL_DATA) ./files/usr/share/netifyd/plugins.d/99-netify-proc-core-auto.conf $(1)/usr/share/netifyd/plugins.d/99-netify-proc-core-auto.conf
	$(INSTALL_DATA) ./files/usr/share/netifyd/plugins.d/99-netify-sink-http-auto.conf $(1)/usr/share/netifyd/plugins.d/99-netify-sink-http-auto.conf
	# nethesis additional files
	$(INSTALL_BIN) ./files/usr/sbin/ns-netifyd-configure.py $(1)/usr/sbin/ns-netifyd-configure
	# netify-plm
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-plm.so.1.0.0 $(1)/usr/lib/libnetify-plm.so.1.0.0
	$(LN) /usr/lib/libnetify-plm.so.1.0.0 $(1)/usr/lib/libnetify-plm.so
	$(LN) /usr/lib/libnetify-plm.so.1.0.0 $(1)/usr/lib/libnetify-plm.so.1
	# netify-proc-aggregator
	$(INSTALL_DATA) ./files/etc/netifyd/netify-proc-aggregator.json $(1)/etc/netifyd/netify-proc-aggregator.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-proc-aggregator.conf $(1)/etc/netifyd/plugins.d/10-netify-proc-aggregator.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-proc-aggregator.so.0.0.0 $(1)/usr/lib/libnetify-proc-aggregator.so.0.0.0
	$(LN) /usr/lib/libnetify-proc-aggregator.so.0.0.0 $(1)/usr/lib/libnetify-proc-aggregator.so
	$(LN) /usr/lib/libnetify-proc-aggregator.so.0.0.0 $(1)/usr/lib/libnetify-proc-aggregator.so.0
	# netify-proc-core
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-proc-core.conf $(1)/etc/netifyd/plugins.d/10-netify-proc-core.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-proc-core.so.0.0.0 $(1)/usr/lib/libnetify-proc-core.so.0.0.0
	$(LN) /usr/lib/libnetify-proc-core.so.0.0.0 $(1)/usr/lib/libnetify-proc-core.so
	$(LN) /usr/lib/libnetify-proc-core.so.0.0.0 $(1)/usr/lib/libnetify-proc-core.so.0
	# netify-proc-flow-actions
	$(INSTALL_DATA) ./files/etc/netifyd/netify-proc-flow-actions.json $(1)/etc/netifyd/netify-proc-flow-actions.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-proc-flow-actions.conf $(1)/etc/netifyd/plugins.d/10-netify-proc-flow-actions.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-proc-flow-actions.so.0.0.0 $(1)/usr/lib/libnetify-proc-flow-actions.so.0.0.0
	$(LN) /usr/lib/libnetify-proc-flow-actions.so.0.0.0 $(1)/usr/lib/libnetify-proc-flow-actions.so
	$(LN) /usr/lib/libnetify-proc-flow-actions.so.0.0.0 $(1)/usr/lib/libnetify-proc-flow-actions.so.0
	# netify-sink-http
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-sink-http.conf $(1)/etc/netifyd/plugins.d/10-netify-sink-http.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-sink-http.so.0.0.0 $(1)/usr/lib/libnetify-sink-http.so.0.0.0
	$(LN) /usr/lib/libnetify-sink-http.so.0.0.0 $(1)/usr/lib/libnetify-sink-http.so
	$(LN) /usr/lib/libnetify-sink-http.so.0.0.0 $(1)/usr/lib/libnetify-sink-http.so.0
	# netify-sink-log
	$(INSTALL_DATA) ./files/etc/netifyd/netify-sink-log.json $(1)/etc/netifyd/netify-sink-log.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-sink-log.conf $(1)/etc/netifyd/plugins.d/10-netify-sink-log.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-sink-log.so.0.0.0 $(1)/usr/lib/libnetify-sink-log.so.0.0.0
	$(LN) /usr/lib/libnetify-sink-log.so.0.0.0 $(1)/usr/lib/libnetify-sink-log.so
	$(LN) /usr/lib/libnetify-sink-log.so.0.0.0 $(1)/usr/lib/libnetify-sink-log.so.0
endef

$(eval $(call BuildPackage,netifyd))
