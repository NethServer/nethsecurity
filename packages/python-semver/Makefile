# This is free software, licensed under the GNU General Public License v2.
# See /LICENSE for more information.
#

include $(TOPDIR)/rules.mk

PKG_NAME:=python-semver
PKG_VERSION:=3.0.4
PKG_RELEASE:=1

PYPI_NAME:=semver
PKG_HASH:=afc7d8c584a5ed0a11033af086e8af226a9c0b206f313e0301f8dd7b6b589602

PKG_MAINTAINER:=Tommaso Bailetti <tommaso.bailetti@nethesis.it>
PKG_LICENSE:=BSD-3-Clause
PKG_LICENSE_FILES:=LICENSE.txt

include $(TOPDIR)/feeds/packages/lang/python/pypi.mk
include $(INCLUDE_DIR)/package.mk
include $(TOPDIR)/feeds/packages/lang/python/python3-package.mk

define Package/python3-semver
  SECTION:=lang
  CATEGORY:=Languages
  SUBMENU:=Python
  TITLE:=Python library for semantic versioning
  URL:=https://github.com/python-semver/python-semver
  DEPENDS:=+python3-light
endef

define Package/python3-semver/description
Python library for semantic versioning. Simplifies parsing, comparing,
and manipulating version numbers following the MAJOR.MINOR.PATCH style.
endef

$(eval $(call Py3Package,python3-semver))
$(eval $(call BuildPackage,python3-semver))
$(eval $(call BuildPackage,python3-semver-src))
