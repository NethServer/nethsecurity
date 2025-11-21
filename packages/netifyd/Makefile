include $(TOPDIR)/rules.mk

PKG_NAME:=netifyd
PKG_VERSION:=2025-10-01-v5.1.25
PKG_RELEASE:=1
PKG_MAINTAINER:=Darryl Sokoloski <darryl@egloo.ca>
PKG_LICENSE:=Unlicensed

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
This is a binary meta package containing precompiled Netify files.
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
/etc/netifyd/netify-apps.conf
/etc/netifyd/netify-categories.json
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
	$(INSTALL_DATA) ./files/etc/config/netifyd $(1)/etc/config/netifyd
	$(INSTALL_BIN) ./files/etc/init.d/netifyd $(1)/etc/init.d/netifyd
	$(INSTALL_DATA) ./files/etc/netifyd.conf $(1)/etc/netifyd.conf
	$(INSTALL_DATA) ./files/etc/netifyd/interfaces.d/10-example-nfq.conf $(1)/etc/netifyd/interfaces.d/10-example-nfq.conf
	$(INSTALL_DATA) ./files/etc/netifyd/interfaces.d/10-example-pcap.conf $(1)/etc/netifyd/interfaces.d/10-example-pcap.conf
	$(INSTALL_DATA) ./files/etc/netifyd/interfaces.d/10-example-tpv3.conf $(1)/etc/netifyd/interfaces.d/10-example-tpv3.conf
	$(INSTALL_DATA) ./files/etc/netifyd/netify-apps.conf $(1)/etc/netifyd/netify-apps.conf
	$(INSTALL_DATA) ./files/etc/netifyd/netify-categories.json $(1)/etc/netifyd/netify-categories.json
	$(INSTALL_DATA) ./files/etc/netifyd/netify-proc-aggregator.json $(1)/etc/netifyd/netify-proc-aggregator.json
	$(INSTALL_DATA) ./files/etc/netifyd/netify-proc-core.json $(1)/etc/netifyd/netify-proc-core.json
	$(INSTALL_DATA) ./files/etc/netifyd/netify-proc-flow-actions.json $(1)/etc/netifyd/netify-proc-flow-actions.json
	$(INSTALL_DATA) ./files/etc/netifyd/netify-sink-http.json $(1)/etc/netifyd/netify-sink-http.json
	$(INSTALL_DATA) ./files/etc/netifyd/netify-sink-log.json $(1)/etc/netifyd/netify-sink-log.json
	$(INSTALL_DATA) ./files/etc/netifyd/netify-sink-socket.json $(1)/etc/netifyd/netify-sink-socket.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-proc-aggregator.conf $(1)/etc/netifyd/plugins.d/10-netify-proc-aggregator.conf
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-proc-core.conf $(1)/etc/netifyd/plugins.d/10-netify-proc-core.conf
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-proc-flow-actions.conf $(1)/etc/netifyd/plugins.d/10-netify-proc-flow-actions.conf
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-sink-http.conf $(1)/etc/netifyd/plugins.d/10-netify-sink-http.conf
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-sink-log.conf $(1)/etc/netifyd/plugins.d/10-netify-sink-log.conf
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-sink-socket.conf $(1)/etc/netifyd/plugins.d/10-netify-sink-socket.conf
	$(INSTALL_DATA) ./files/etc/netifyd/profiles.d/00-default.conf $(1)/etc/netifyd/profiles.d/00-default.conf
	$(INSTALL_BIN) ./files/etc/uci-defaults/99-netify-v4-migrate.uci-default $(1)/etc/uci-defaults/99-netify-v4-migrate
	$(INSTALL_BIN) ./files/usr/lib/libnetifyd.so.4.0.0 $(1)/usr/lib/libnetifyd.so.4.0.0
	$(INSTALL_BIN) ./files/usr/lib/libnetify-plm.so.1.0.0 $(1)/usr/lib/libnetify-plm.so.1.0.0
	$(INSTALL_BIN) ./files/usr/lib/libnetify-proc-aggregator.so.0.0.0 $(1)/usr/lib/libnetify-proc-aggregator.so.0.0.0
	$(INSTALL_BIN) ./files/usr/lib/libnetify-proc-core.so.0.0.0 $(1)/usr/lib/libnetify-proc-core.so.0.0.0
	$(INSTALL_BIN) ./files/usr/lib/libnetify-proc-flow-actions.so.0.0.0 $(1)/usr/lib/libnetify-proc-flow-actions.so.0.0.0
	$(INSTALL_BIN) ./files/usr/lib/libnetify-sink-http.so.0.0.0 $(1)/usr/lib/libnetify-sink-http.so.0.0.0
	$(INSTALL_BIN) ./files/usr/lib/libnetify-sink-log.so.0.0.0 $(1)/usr/lib/libnetify-sink-log.so.0.0.0
	$(INSTALL_BIN) ./files/usr/lib/libnetify-sink-socket.so.0.0.0 $(1)/usr/lib/libnetify-sink-socket.so.0.0.0
	$(INSTALL_BIN) ./files/usr/sbin/netifyd $(1)/usr/sbin/netifyd
	$(INSTALL_DATA) ./files/usr/share/netifyd/functions.sh $(1)/usr/share/netifyd/functions.sh
	$(INSTALL_DATA) ./files/usr/share/netifyd/netify-apps.conf $(1)/usr/share/netifyd/netify-apps.conf
	$(INSTALL_DATA) ./files/usr/share/netifyd/netify-categories.json $(1)/usr/share/netifyd/netify-categories.json
	$(INSTALL_DATA) ./files/usr/share/netifyd/netify-proc-core-auto.json $(1)/usr/share/netifyd/netify-proc-core-auto.json
	$(INSTALL_DATA) ./files/usr/share/netifyd/netify-sink-http-auto.json $(1)/usr/share/netifyd/netify-sink-http-auto.json
	$(INSTALL_DATA) ./files/usr/share/netifyd/plugins.d/99-netify-proc-core-auto.conf $(1)/usr/share/netifyd/plugins.d/99-netify-proc-core-auto.conf
	$(INSTALL_DATA) ./files/usr/share/netifyd/plugins.d/99-netify-sink-http-auto.conf $(1)/usr/share/netifyd/plugins.d/99-netify-sink-http-auto.conf
	$(INSTALL_DATA) ./files/usr/share/nftables.d/table-pre/10-netifyd.nft $(1)/usr/share/nftables.d/table-pre/10-netifyd.nft
	$(LN) /usr/lib/libnetifyd.so.4.0.0 $(1)/usr/lib/libnetifyd.so
	$(LN) /usr/lib/libnetifyd.so.4.0.0 $(1)/usr/lib/libnetifyd.so.4
	$(LN) /usr/lib/libnetify-plm.so.1.0.0 $(1)/usr/lib/libnetify-plm.so.1
	$(LN) /usr/lib/libnetify-proc-aggregator.so.0.0.0 $(1)/usr/lib/libnetify-proc-aggregator.so.0
	$(LN) /usr/lib/libnetify-proc-core.so.0.0.0 $(1)/usr/lib/libnetify-proc-core.so.0
	$(LN) /usr/lib/libnetify-proc-flow-actions.so.0.0.0 $(1)/usr/lib/libnetify-proc-flow-actions.so.0
	$(LN) /usr/lib/libnetify-sink-http.so.0.0.0 $(1)/usr/lib/libnetify-sink-http.so.0
	$(LN) /usr/lib/libnetify-sink-log.so.0.0.0 $(1)/usr/lib/libnetify-sink-log.so.0
	$(LN) /usr/lib/libnetify-sink-socket.so.0.0.0 $(1)/usr/lib/libnetify-sink-socket.so.0
endef

$(eval $(call BuildPackage,netifyd))
