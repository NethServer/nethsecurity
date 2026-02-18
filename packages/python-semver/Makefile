include $(TOPDIR)/rules.mk

PKG_NAME:=python-semver
PKG_VERSION:=2.13.0
PKG_RELEASE:=1

PKG_MAINTAINER:=Bailetti Tommaso <tommaso.bailetti@nethesis.it>
PKG_LICENSE:=BSD-3-Clause
PKG_LICENSE_FILES:=LICENSE.txt

PYPI_NAME:=semver
PKG_HASH:=fa0fe2722ee1c3f57eac478820c3a5ae2f624af8264cbdf9000c980ff7f75e3f

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
