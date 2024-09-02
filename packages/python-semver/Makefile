#
# Copyright (C) 2024 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=python-semver
PKG_VERSION:=3.0.2
PKG_RELEASE:=1
 
PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

PKG_SOURCE:=python-semver-$(PKG_VERSION).tar.gz
PKG_SOURCE_URL:=https://codeload.github.com/python-semver/python-semver/tar.gz/$(PKG_VERSION)?
PKG_HASH:=skip

PYTHON3_PKG_WHEEL_NAME=semver
PKG_HOST_ONLY:=1
HOST_BUILD_DEPENDS:= \
	python3/host \
	python-build/host \
	python-installer/host \
	python-setuptools-scm/host

include ../pypi.mk
include $(INCLUDE_DIR)/package.mk
include $(INCLUDE_DIR)/host-build.mk
include $(TOPDIR)/feeds/packages/lang/python/python3-host-build.mk
include $(TOPDIR)/feeds/packages/lang/python/python3-package.mk
 
define Package/python-semver
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Python SemVer
	URL:=https://github.com/python-semver/python-semver/
	DEPENDS:=+python3-setuptools-scm +python3-setuptools
	PKGARCH:=all
endef
 
define Package/python-semver/description
    python3-semver library
endef

$(eval $(call Py3Package,python-semver))
$(eval $(call BuildPackage,python-semver))
$(eval $(call BuildPackage,python-semver-src))
