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
 
define Package/supervisor
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Supervisor
	URL:=https://github.com/Supervisor/supervisor
	DEPENDS:= \
		+python3-light \
		+python3-decimal \
		+python3-email \
		+python3-idna \
		+python3-setuptools \
		+python3-urllib
	PKGARCH:=all
endef
 
define Package/supervisor/description
    Supervisor is a client/server system that allows its users to control a number of processes on UNIX-like operating systems.
endef

define Build/Compile
	cd $(PKG_BUILD_DIR) && python3 setup.py install --prefix=/usr --root=$(PKG_INSTALL_DIR)
endef

define Package/supervisor/conffiles
	/etc/supervisord.conf
	/etc/supervisord.d/
endef

define Package/supervisor/install
	$(INSTALL_DIR) $(1)/etc/
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_DIR) $(1)/etc/supervisord.d/
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_DIR) $(1)/usr/lib
	$(INSTALL_DATA) ./files/supervisord.conf $(1)/etc/supervisord.conf
	$(INSTALL_BIN) ./files/supervisord.init $(1)/etc/init.d/supervisord
	$(INSTALL_BIN) $(PKG_INSTALL_DIR)/usr/bin/supervisord $(1)/usr/bin/
	$(INSTALL_BIN) $(PKG_INSTALL_DIR)/usr/bin/supervisorctl $(1)/usr/bin/
	$(INSTALL_BIN) $(PKG_INSTALL_DIR)/usr/bin/pidproxy $(1)/usr/bin/
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/* $(1)/usr/lib/
	find $(1)/usr/bin/ -type f -exec sed -i '1s|.*|#!/usr/bin/env python3|' {} +
endef

$(eval $(call BuildPackage,supervisor))
