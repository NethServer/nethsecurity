include $(TOPDIR)/rules.mk

PKG_NAME:=netifyd
PKG_VERSION:=2025.10.01-5.1.25
PKG_RELEASE:=3
PKG_MAINTAINER:=Darryl Sokoloski <darryl@egloo.ca>
PKG_LICENSE:=Unlicensed

# Base URL for downloads
NETIFYD_BASE_URL:=https://updates.nethsecurity.nethserver.org/netifyd-dist/netifyd-$(PKG_VERSION)/$(ARCH)
DL_DIR:=$(DL_DIR)/netifyd-$(PKG_VERSION)-$(ARCH)

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
Netifyd meta package compiled for NethSecurity 8.
endef

define Download/libnetifyd
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetifyd.so.4.0.0
  FILE:=libnetifyd.so.4.0.0
  HASH:=bc17464b4efb7c5eef7475695db05642a37b4e941fca961fed3b6066de74657d
endef
$(eval $(call Download,libnetifyd))

define Download/libnetify-plm
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-plm.so.1.0.0
  FILE:=libnetify-plm.so.1.0.0
  HASH:=21967b48ac5cb07fbb73b02b1dd8aac3526d5531a8744c3cec229e4f89c2c091
endef
$(eval $(call Download,libnetify-plm))

define Download/libnetify-proc-aggregator
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-proc-aggregator.so.0.0.0
  FILE:=libnetify-proc-aggregator.so.0.0.0
  HASH:=930fe7b42ce087bab9c3811a134969a0619ccecd6f8f0753c7986f081c8ac6a8
endef
$(eval $(call Download,libnetify-proc-aggregator))

define Download/libnetify-proc-core
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-proc-core.so.0.0.0
  FILE:=libnetify-proc-core.so.0.0.0
  HASH:=38c1c2f05c8e3c0391b1c8ad84ee00fcb30b17718948be621df62f1ac0d515ed
endef
$(eval $(call Download,libnetify-proc-core))

define Download/libnetify-proc-flow-actions
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-proc-flow-actions.so.0.0.0
  FILE:=libnetify-proc-flow-actions.so.0.0.0
  HASH:=e459359172b6742d769600491625fa226b1f06219182b00680b07e5fd9167025
endef
$(eval $(call Download,libnetify-proc-flow-actions))

define Download/libnetify-sink-http
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-sink-http.so.0.0.0
  FILE:=libnetify-sink-http.so.0.0.0
  HASH:=0d94866bc5eebd31d4e5cab2c2bdee54adf6c20084f13117383015e8f4e64a88
endef
$(eval $(call Download,libnetify-sink-http))

define Download/libnetify-sink-log
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-sink-log.so.0.0.0
  FILE:=libnetify-sink-log.so.0.0.0
  HASH:=36bdc8f70f2052ad6a4d7d6de7ea25b95bf9d377a71c42d5b13317d677eb7c75
endef
$(eval $(call Download,libnetify-sink-log))

define Download/libnetify-sink-socket
  URL:=$(NETIFYD_BASE_URL)/usr/lib
  URL_FILE:=libnetify-sink-socket.so.0.0.0
  FILE:=libnetify-sink-socket.so.0.0.0
  HASH:=7876b3dd4fd178c7c5fde47fc3e4965bf65d5cb2c83a8e7a4b8eb43dd29265bc
endef
$(eval $(call Download,libnetify-sink-socket))

define Download/netifyd
  URL:=$(NETIFYD_BASE_URL)/usr/sbin
  URL_FILE:=netifyd
  FILE:=netifyd
  HASH:=40ed6d2242b64552d0782ccdc716751ba9cc76fac165510574b03a465a7565f0
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
	$(CP) $(DL_DIR)/libnetify-sink-socket.so.0.0.0 $(PKG_BUILD_DIR)/
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

	# netifyd
	$(INSTALL_DATA) ./files/etc/config/netifyd $(1)/etc/config/netifyd
	$(INSTALL_BIN) ./files/etc/init.d/netifyd $(1)/etc/init.d/netifyd
	$(INSTALL_DATA) ./files/etc/netifyd.conf $(1)/etc/netifyd.conf
	$(INSTALL_DATA) ./files/etc/netifyd/interfaces.d/10-nfqueue.conf $(1)/etc/netifyd/interfaces.d/10-nfqueue.conf
	$(INSTALL_DATA) ./files/etc/netifyd/netify-apps.conf $(1)/etc/netifyd/netify-apps.conf
	$(INSTALL_DATA) ./files/etc/netifyd/netify-categories.json $(1)/etc/netifyd/netify-categories.json
	$(INSTALL_DATA) ./files/etc/netifyd/profiles.d/00-default.conf $(1)/etc/netifyd/profiles.d/00-default.conf
	$(INSTALL_BIN) ./files/etc/uci-defaults/99-netify-v4-migrate.uci-default $(1)/etc/uci-defaults/99-netify-v4-migrate
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/netifyd $(1)/usr/sbin/netifyd
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetifyd.so.4.0.0 $(1)/usr/lib/libnetifyd.so.4.0.0
	$(INSTALL_DATA) ./files/usr/share/netifyd/functions.sh $(1)/usr/share/netifyd/functions.sh
	$(INSTALL_DATA) ./files/usr/share/netifyd/netify-apps.conf $(1)/usr/share/netifyd/netify-apps.conf
	$(INSTALL_DATA) ./files/usr/share/netifyd/netify-categories.json $(1)/usr/share/netifyd/netify-categories.json
	$(INSTALL_DATA) ./files/usr/share/netifyd/netify-proc-core-auto.json $(1)/usr/share/netifyd/netify-proc-core-auto.json
	$(INSTALL_DATA) ./files/usr/share/netifyd/netify-sink-http-auto.json $(1)/usr/share/netifyd/netify-sink-http-auto.json
	$(INSTALL_DATA) ./files/usr/share/netifyd/plugins.d/99-netify-proc-core-auto.conf $(1)/usr/share/netifyd/plugins.d/99-netify-proc-core-auto.conf
	$(INSTALL_DATA) ./files/usr/share/netifyd/plugins.d/99-netify-sink-http-auto.conf $(1)/usr/share/netifyd/plugins.d/99-netify-sink-http-auto.conf
	$(INSTALL_DATA) ./files/usr/share/nftables.d/table-pre/10-netifyd-nfqueue.nft $(1)/usr/share/nftables.d/table-pre/10-netifyd-nfqueue.nft
	$(LN) /usr/lib/libnetifyd.so.4.0.0 $(1)/usr/lib/libnetifyd.so
	$(LN) /usr/lib/libnetifyd.so.4.0.0 $(1)/usr/lib/libnetifyd.so.4
	# netify-plm
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-plm.so.1.0.0 $(1)/usr/lib/libnetify-plm.so.1.0.0
	$(LN) /usr/lib/libnetify-plm.so.1.0.0 $(1)/usr/lib/libnetify-plm.so.1
	# netify-proc-aggregator
	$(INSTALL_DATA) ./files/etc/netifyd/netify-proc-aggregator.json $(1)/etc/netifyd/netify-proc-aggregator.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-proc-aggregator.conf $(1)/etc/netifyd/plugins.d/10-netify-proc-aggregator.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-proc-aggregator.so.0.0.0 $(1)/usr/lib/libnetify-proc-aggregator.so.0.0.0
	$(LN) /usr/lib/libnetify-proc-aggregator.so.0.0.0 $(1)/usr/lib/libnetify-proc-aggregator.so.0
	# netify-proc-core
	$(INSTALL_DATA) ./files/etc/netifyd/netify-proc-core.json $(1)/etc/netifyd/netify-proc-core.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-proc-core.conf $(1)/etc/netifyd/plugins.d/10-netify-proc-core.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-proc-core.so.0.0.0 $(1)/usr/lib/libnetify-proc-core.so.0.0.0
	$(LN) /usr/lib/libnetify-proc-core.so.0.0.0 $(1)/usr/lib/libnetify-proc-core.so.0
	# netify-proc-flow-actions
	$(INSTALL_DATA) ./files/etc/netifyd/netify-proc-flow-actions.json $(1)/etc/netifyd/netify-proc-flow-actions.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-proc-flow-actions.conf $(1)/etc/netifyd/plugins.d/10-netify-proc-flow-actions.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-proc-flow-actions.so.0.0.0 $(1)/usr/lib/libnetify-proc-flow-actions.so.0.0.0
	$(LN) /usr/lib/libnetify-proc-flow-actions.so.0.0.0 $(1)/usr/lib/libnetify-proc-flow-actions.so.0
	# netify-sink-log
	$(INSTALL_DATA) ./files/etc/netifyd/netify-sink-log.json $(1)/etc/netifyd/netify-sink-log.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-sink-log.conf $(1)/etc/netifyd/plugins.d/10-netify-sink-log.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-sink-log.so.0.0.0 $(1)/usr/lib/libnetify-sink-log.so.0.0.0
	$(LN) /usr/lib/libnetify-sink-log.so.0.0.0 $(1)/usr/lib/libnetify-sink-log.so.0
	# netify-sink-socket
	$(INSTALL_DATA) ./files/etc/netifyd/netify-sink-socket.json $(1)/etc/netifyd/netify-sink-socket.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-sink-socket.conf $(1)/etc/netifyd/plugins.d/10-netify-sink-socket.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-sink-socket.so.0.0.0 $(1)/usr/lib/libnetify-sink-socket.so.0.0.0
	$(LN) /usr/lib/libnetify-sink-socket.so.0.0.0 $(1)/usr/lib/libnetify-sink-socket.so.0
	# netify-sink-http
	$(INSTALL_DATA) ./files/etc/netifyd/netify-sink-http.json $(1)/etc/netifyd/netify-sink-http.json
	$(INSTALL_DATA) ./files/etc/netifyd/plugins.d/10-netify-sink-http.conf $(1)/etc/netifyd/plugins.d/10-netify-sink-http.conf
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/libnetify-sink-http.so.0.0.0 $(1)/usr/lib/libnetify-sink-http.so.0.0.0
	$(LN) /usr/lib/libnetify-sink-http.so.0.0.0 $(1)/usr/lib/libnetify-sink-http.so.0
endef

$(eval $(call BuildPackage,netifyd))
