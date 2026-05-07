include $(TOPDIR)/rules.mk

PKG_NAME:=netifyd
NETIFYD_VERSION:=5.2.6
PKG_VERSION:=$(NETIFYD_VERSION)
PKG_RELEASE:=3
PKG_MAINTAINER:=Darryl Sokoloski <darryl@egloo.ca>
PKG_LICENSE:=Unlicensed

# Base URL for downloads
NETIFYD_BASE_URL:=https://updates.nethsecurity.nethserver.org/netifyd-dist/netifyd-$(NETIFYD_VERSION)/$(ARCH)
DL_DIR:=$(DL_DIR)/netifyd-$(NETIFYD_VERSION)-$(ARCH)

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
  HASH:=a7bef78717e200eef177da8ee94557a565828ce796d3fd1a1f078e3f55959dd5
endef
$(eval $(call Download,libnetifyd))

define Download/libnetify-plm
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-plm.so.1.0.0
  FILE:=libnetify-plm.so.1.0.0
  HASH:=b5c8994dc5f497ef1ccf8aae3685c1541702031726bc9f2819489cacfcb67e8f
endef
$(eval $(call Download,libnetify-plm))

define Download/libnetify-proc-aggregator
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-proc-aggregator.so.0.0.0
  FILE:=libnetify-proc-aggregator.so.0.0.0
  HASH:=c9e5981fd4410776a1808902fbe284f40882823fc4c711f54e14421c80e94c6b
endef
$(eval $(call Download,libnetify-proc-aggregator))

define Download/libnetify-proc-core
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-proc-core.so.0.0.0
  FILE:=libnetify-proc-core.so.0.0.0
  HASH:=725415498d05fc29695a6f1fe14aed4c6b5967ff0d7d4703d06b80489c852222
endef
$(eval $(call Download,libnetify-proc-core))

define Download/libnetify-proc-dev-discovery
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-proc-dev-discovery.so.0.0.0
  FILE:=libnetify-proc-dev-discovery.so.0.0.0
  HASH:=c25c4a497925cc0cf9d48f353de76fd2b5c9aa223390c87f2163feb1b0d61efb
endef
$(eval $(call Download,libnetify-proc-dev-discovery))

define Download/libnetify-proc-flow-actions
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-proc-flow-actions.so.0.0.0
  FILE:=libnetify-proc-flow-actions.so.0.0.0
  HASH:=06ed65a3ec5d840edff008aaebbe294e4b0f7545ab295b287f6ed286bf28b7d7
endef
$(eval $(call Download,libnetify-proc-flow-actions))

define Download/libnetify-sink-http
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-sink-http.so.0.0.0
  FILE:=libnetify-sink-http.so.0.0.0
  HASH:=aaaadb9179f3df215f08d29f3a46db314d3990adafa5f3c4abeff305f4bb9583
endef
$(eval $(call Download,libnetify-sink-http))

define Download/libnetify-sink-log
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-sink-log.so.0.0.0
  FILE:=libnetify-sink-log.so.0.0.0
  HASH:=26d136562f7416ce4fe7c70d8023ae3f578a2d2dff4239791c65ad4289d28765
endef
$(eval $(call Download,libnetify-sink-log))

define Download/libnetify-sink-socket
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-sink-socket.so.0.0.0
  FILE:=libnetify-sink-socket.so.0.0.0
  HASH:=8772335da50b702edd2a1412c98c82e32058dee2158db6e874ba3964ac66590a
endef
$(eval $(call Download,libnetify-sink-socket))

define Download/libnetify-sink-sqlite
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-sink-sqlite.so.0.0.0
  FILE:=libnetify-sink-sqlite.so.0.0.0
  HASH:=6c2879cb8c9da36d592c85b9f8b4042339f0322fe2ebf335a5d15d06562ec65b
endef
$(eval $(call Download,libnetify-sink-sqlite))

define Download/netifyd
  URL:=$(NETIFYD_BASE_URL)/usr/sbin
  URL_FILE:=netifyd
  FILE:=netifyd
  HASH:=02a8647d779f7dc4506fe9dd10295a06f6f1cb7b701edbfe791e6f319c4d7fd3
endef
$(eval $(call Download,netifyd))

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	$(CP) $(DL_DIR)/libnetifyd.so.4.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-plm.so.1.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-proc-aggregator.so.0.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-proc-core.so.0.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-proc-dev-discovery.so.0.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-proc-flow-actions.so.0.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-sink-http.so.0.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-sink-log.so.0.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-sink-socket.so.0.0.0 $(PKG_BUILD_DIR)/
	$(CP) $(DL_DIR)/libnetify-sink-sqlite.so.0.0.0 $(PKG_BUILD_DIR)/
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
	$(INSTALL_DATA) ./files/etc/netifyd/netify-proc-core.json $(1)/etc/netifyd/netify-proc-core.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-proc-core.conf $(1)/etc/netifyd/plugins.d/10-netify-proc-core.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-proc-core.so.0.0.0 $(1)/usr/lib/libnetify-proc-core.so.0.0.0
	$(LN) /usr/lib/libnetify-proc-core.so.0.0.0 $(1)/usr/lib/libnetify-proc-core.so
	$(LN) /usr/lib/libnetify-proc-core.so.0.0.0 $(1)/usr/lib/libnetify-proc-core.so.0
	# netify-proc-dev-discovery
	$(INSTALL_DATA) ./files/etc/netifyd/netify-proc-dev-discovery.json $(1)/etc/netifyd/netify-proc-dev-discovery.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-proc-dev-discovery.conf $(1)/etc/netifyd/plugins.d/10-netify-proc-dev-discovery.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-proc-dev-discovery.so.0.0.0 $(1)/usr/lib/libnetify-proc-dev-discovery.so.0.0.0
	$(LN) /usr/lib/libnetify-proc-dev-discovery.so.0.0.0 $(1)/usr/lib/libnetify-proc-dev-discovery.so
	$(LN) /usr/lib/libnetify-proc-dev-discovery.so.0.0.0 $(1)/usr/lib/libnetify-proc-dev-discovery.so.0
	# netify-proc-flow-actions
	$(INSTALL_DATA) ./files/etc/netifyd/netify-proc-flow-actions.json $(1)/etc/netifyd/netify-proc-flow-actions.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-proc-flow-actions.conf $(1)/etc/netifyd/plugins.d/10-netify-proc-flow-actions.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-proc-flow-actions.so.0.0.0 $(1)/usr/lib/libnetify-proc-flow-actions.so.0.0.0
	$(LN) /usr/lib/libnetify-proc-flow-actions.so.0.0.0 $(1)/usr/lib/libnetify-proc-flow-actions.so
	$(LN) /usr/lib/libnetify-proc-flow-actions.so.0.0.0 $(1)/usr/lib/libnetify-proc-flow-actions.so.0
	# netify-sink-log
	$(INSTALL_DATA) ./files/etc/netifyd/netify-sink-log.json $(1)/etc/netifyd/netify-sink-log.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-sink-log.conf $(1)/etc/netifyd/plugins.d/10-netify-sink-log.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-sink-log.so.0.0.0 $(1)/usr/lib/libnetify-sink-log.so.0.0.0
	$(LN) /usr/lib/libnetify-sink-log.so.0.0.0 $(1)/usr/lib/libnetify-sink-log.so
	$(LN) /usr/lib/libnetify-sink-log.so.0.0.0 $(1)/usr/lib/libnetify-sink-log.so.0
	# netify-sink-socket
	$(INSTALL_DATA) ./files/etc/netifyd/netify-sink-socket.json $(1)/etc/netifyd/netify-sink-socket.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-sink-socket.conf $(1)/etc/netifyd/plugins.d/10-netify-sink-socket.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-sink-socket.so.0.0.0 $(1)/usr/lib/libnetify-sink-socket.so.0.0.0
	$(LN) /usr/lib/libnetify-sink-socket.so.0.0.0 $(1)/usr/lib/libnetify-sink-socket.so
	$(LN) /usr/lib/libnetify-sink-socket.so.0.0.0 $(1)/usr/lib/libnetify-sink-socket.so.0
	# netify-sink-http
	$(INSTALL_DATA) ./files/etc/netifyd/netify-sink-http.json $(1)/etc/netifyd/netify-sink-http.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-sink-http.conf $(1)/etc/netifyd/plugins.d/10-netify-sink-http.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-sink-http.so.0.0.0 $(1)/usr/lib/libnetify-sink-http.so.0.0.0
	$(LN) /usr/lib/libnetify-sink-http.so.0.0.0 $(1)/usr/lib/libnetify-sink-http.so
	$(LN) /usr/lib/libnetify-sink-http.so.0.0.0 $(1)/usr/lib/libnetify-sink-http.so.0
	# netify-sink-sqlite
	$(INSTALL_DATA) ./files/etc/netifyd/netify-sink-sqlite.json $(1)/etc/netifyd/netify-sink-sqlite.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-sink-sqlite.conf $(1)/etc/netifyd/plugins.d/10-netify-sink-sqlite.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-sink-sqlite.so.0.0.0 $(1)/usr/lib/libnetify-sink-sqlite.so.0.0.0
	$(LN) /usr/lib/libnetify-sink-sqlite.so.0.0.0 $(1)/usr/lib/libnetify-sink-sqlite.so
	$(LN) /usr/lib/libnetify-sink-sqlite.so.0.0.0 $(1)/usr/lib/libnetify-sink-sqlite.so.0
endef

$(eval $(call BuildPackage,netifyd))
