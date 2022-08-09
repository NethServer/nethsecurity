#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=python3-nextsec
PKG_VERSION:=0.0.1
PKG_RELEASE:=1
 
PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://github.com/NethServer/python3-nextsec
PKG_SOURCE_VERSION:=7333380b71b8f7b2d645ca5ee42ca1b5b74db569

include $(INCLUDE_DIR)/package.mk
include $(TOPDIR)/feeds/packages/lang/python/python3-package.mk
 
define Package/python3-nextsec
	SECTION:=base
	CATEGORY:=NextSecurity
	TITLE:=NextSecurity python libraries
	URL:=https://github.com/NethServer/nextsecurity-controller/
	DEPENDS:=+python3-light +python3-uci
endef
 
define Package/python3-nextsec/description
    NextSecurity python utilities
endef

$(eval $(call Py3Package,python3-nextsec))
$(eval $(call BuildPackage,python3-nextsec))
$(eval $(call BuildPackage,python3-nextsec-src))
