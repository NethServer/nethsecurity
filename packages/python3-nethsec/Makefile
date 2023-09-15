#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=python3-nethsec
PKG_VERSION:=0.0.1
PKG_RELEASE:=1
 
PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://github.com/NethServer/python3-nethsec
PKG_SOURCE_VERSION:=74d57b17f6e87365a294a83d5cc49288efbc0caf

include $(INCLUDE_DIR)/package.mk
include $(TOPDIR)/feeds/packages/lang/python/python3-package.mk
 
define Package/python3-nethsec
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=NethSecurity python libraries
	URL:=https://github.com/NethServer/python3-nethsec/
	DEPENDS:=+python3-light +python3-uci
	PKGARCH:=all
endef
 
define Package/python3-nethsec/description
    NethSecurity python utilities
endef

$(eval $(call Py3Package,python3-nethsec))
$(eval $(call BuildPackage,python3-nethsec))
$(eval $(call BuildPackage,python3-nethsec-src))
