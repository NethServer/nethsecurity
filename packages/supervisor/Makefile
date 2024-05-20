#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=supervisor
PKG_VERSION:=4.2.5
PKG_RELEASE:=1
 
PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

PKG_SOURCE:=supervisor-$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/Supervisor/supervisor/tar.gz/$(PKG_VERSION)?
PKG_HASH:=skip

PYTHON3_PKG_WHEEL_NAME=supervisor

include $(INCLUDE_DIR)/package.mk
include $(TOPDIR)/feeds/packages/lang/python/python3-package.mk
 
define Package/supervisor
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Supervisor
	URL:=https://github.com/Supervisor/supervisor
	DEPENDS:=+python3-setuptools
	PKGARCH:=all
endef
 
define Package/supervisor/description
    Supervisor is a client/server system that allows its users to control a number of processes on UNIX-like operating systems.
endef

$(eval $(call Py3Package,supervisor))
$(eval $(call BuildPackage,supervisor))
$(eval $(call BuildPackage,supervisor-src))
