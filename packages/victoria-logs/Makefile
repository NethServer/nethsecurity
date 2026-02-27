include $(TOPDIR)/rules.mk

PKG_NAME:=victoria-logs
# renovate: datasource=github-tags depName=VictoriaMetrics/VictoriaLogs
PKG_VERSION:=1.14.0-victorialogs
PKG_RELEASE:=1

PKG_SOURCE:=$(PKG_NAME)-$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/VictoriaMetrics/VictoriaLogs/tar.gz/v$(PKG_VERSION)?
PKG_SOURCE_SUBDIR:=VictoriaLogs-$(PKG_VERSION)
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)

PKG_HASH:=skip
PKG_MAINTAINER:=Tommaso Bailetti <tommaso.bailetti@nethesis.it>
PKG_LICENSE:=Apache-2.0

PKG_BUILD_DEPENDS:=golang/host
PKG_BUILD_PARALLEL:=1
PKG_BUILD_FLAGS:=no-mips16

GO_PKG:=github.com/VictoriaMetrics/VictoriaMetrics/app/victoria-logs
GO_BUILD_PKG:=github.com/VictoriaMetrics/VictoriaMetrics/app/victoria-logs
GO_PKG_GCFLAGS:= \
	-trimpath \
	-buildvcs=false
GO_PKG_LDFLAGS:= \
	-extldflags \
	-static
GO_PKG_LDFLAGS_X:=github.com/VictoriaMetrics/VictoriaMetrics/lib/buildinfo.Version=$(PKG_NAME)-v$(PKG_VERSION)
GO_PKG_TAGS:= \
	netgo \
	osusergo \
	musl

include $(INCLUDE_DIR)/package.mk
include $(TOPDIR)/feeds/packages/lang/golang/golang-package.mk

define Package/victoria-logs
	SECTION:=base
	CATEGORY:=NethServer
	TITLE:=Victoria Logs
	URL:=https://github.com/VictoriaMetrics/VictoriaLogs
	DEPENDS:=$(GO_ARCH_DEPENDS) +rsyslog
endef

define Package/victoria-logs/description
	VictoriaLogs — fast and easy-to-use database for logs.
endef

define Package/victoria-logs/conffiles
/etc/config/victoria-logs
endef

define Package/victoria-logs/install
	$(call GoPackage/Package/Install/Bin,$(1))
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) ./files/victoria-logs.initd $(1)/etc/init.d/victoria-logs
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DATA) ./files/victoria-logs.conf $(1)/etc/config/victoria-logs
	$(INSTALL_DIR) $(1)/etc/rsyslog.d
	$(INSTALL_CONF) ./files/rsyslog-victoria-logs.conf $(1)/etc/rsyslog.d/victoria-logs.conf
	$(INSTALL_DIR) $(1)/etc/uci-defaults
	$(INSTALL_BIN) ./files/25_victoria-logs $(1)/etc/uci-defaults/25_victoria-logs
endef

define Package/victoria-logs/postinst
#!/bin/sh
[ -z "$${IPKG_INSTROOT}" ] && /etc/init.d/victoria-logs restart
exit 0
endef

$(eval $(call GoBinPackage,victoria-logs))
$(eval $(call BuildPackage,victoria-logs))
