#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=python3-nethsec
PKG_VERSION:=0.0.22
PKG_RELEASE:=1
 
PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

PKG_SOURCE:=python3-nethsec-$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/nethserver/python3-nethsec/tar.gz/$(PKG_VERSION)?
PKG_HASH:=skip

PYTHON3_PKG_WHEEL_NAME=nethsec

include $(INCLUDE_DIR)/package.mk
include $(TOPDIR)/feeds/packages/lang/python/python3-package.mk
 
define Package/python3-nethsec
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity python libraries
	URL:=https://github.com/NethServer/python3-nethsec/
	DEPENDS:=+python3-uci +python3-passlib
	PKGARCH:=all
endef
 
define Package/python3-nethsec/description
    NethSecurity python utilities
endef

$(eval $(call Py3Package,python3-nethsec))
$(eval $(call BuildPackage,python3-nethsec))
$(eval $(call BuildPackage,python3-nethsec-src))
