#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=python3-nethsec
# renovate: datasource=github-tags depName=NethServer/python3-nethsec
PKG_VERSION:=1.6.5
PKG_RELEASE:=1
 
PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://github.com/NethServer/python3-nethsec.git
PKG_SOURCE_VERSION:=8389c32cb7d4e9dcd72acf8e0dc882855b4034d7
PKG_SOURCE_SUBDIR:=python3-nethsec-$(PKG_SOURCE_VERSION)
PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_SOURCE_SUBDIR)
PKG_MIRROR_HASH:=skip

PYTHON3_PKG_WHEEL_NAME=nethsec
PYTHON3_PKG_WHEEL_VERSION:=$(PKG_VERSION)

include $(INCLUDE_DIR)/package.mk
include $(TOPDIR)/feeds/packages/lang/python/python3-package.mk
 
define Package/python3-nethsec
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity python libraries
	URL:=https://github.com/NethServer/python3-nethsec/
	DEPENDS:=+python3-uci +python3-libpass
	PKGARCH:=all
endef
 
define Package/python3-nethsec/description
    NethSecurity python utilities
endef

$(eval $(call Py3Package,python3-nethsec))
$(eval $(call BuildPackage,python3-nethsec))
$(eval $(call BuildPackage,python3-nethsec-src))
