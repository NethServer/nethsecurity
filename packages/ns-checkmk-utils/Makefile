#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=ns-checkmk-utils
# renovate: datasource=github-tags depName=nethesis/checkmk-tools
PKG_VERSION:=1.7.3
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/ns-checkmk-utils-$(PKG_VERSION)

PKG_MAINTAINER:=Tommaso Bailetti <tommaso.bailetti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

# Base URL for downloads
NS_CHECKMK_UTILS_BASE_URL:=https://raw.githubusercontent.com/nethesis/checkmk-tools/v$(PKG_VERSION)/script-check-nsec8/full

include $(INCLUDE_DIR)/package.mk

define Download/check_apk_packages
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_apk_packages.py
	FILE:=check_apk_packages.py
	HASH:=c6c62cb53d0dc3d909dd4d0c9003dd362f06c9eb0dfaabc3c2f70ac5c15f0cf
endef
$(eval $(call Download,check_apk_packages))

define Download/check_dhcp_leases
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_dhcp_leases.py
	FILE:=check_dhcp_leases.py
	HASH:=a26fece5b788faf3ee2531b8fd7ef149e8937056cdd28f9d11a79e7a79ce975d
endef
$(eval $(call Download,check_dhcp_leases))

define Download/check_dns_resolution
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_dns_resolution.py
	FILE:=check_dns_resolution.py
	HASH:=7f3e41ee03eb68e49fdabc495e21462df39c1ae839de62a4a20b8cf8cd3c9d82
endef
$(eval $(call Download,check_dns_resolution))

define Download/check_firewall_connections
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_connections.py
	FILE:=check_firewall_connections.py
	HASH:=0e916e816843baa6e3b0f14790e40fef6a17d51efeb6c45cfb1f5e965c0f4551
endef
$(eval $(call Download,check_firewall_connections))

define Download/check_firewall_rules
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_rules.py
	FILE:=check_firewall_rules.py
	HASH:=238311e66223380fa22cf0360cef631ce65217e25be8c8da2fbf6c8effc22b90
endef
$(eval $(call Download,check_firewall_rules))

define Download/check_firewall_traffic
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_traffic.py
	FILE:=check_firewall_traffic.py
	HASH:=fbb32b89c93dadc1a8a09ca8fee457268f3378b27cc92e7a88b1a01db62bba1e
endef
$(eval $(call Download,check_firewall_traffic))

define Download/check_ovpn_host2net
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_ovpn_host2net.py
	FILE:=check_ovpn_host2net.py
	HASH:=32094f9732ae75f630ad9f75efbc914d9e8d8a87bb10e9a4adbbee32e3c76b03
endef
$(eval $(call Download,check_ovpn_host2net))

define Download/check_root_access
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_root_access.py
	FILE:=check_root_access.py
	HASH:=305fe9ba1bfe4efa50348a3183fbd0666f9bb924c0b6ec08cee30fedd8e79e85
endef
$(eval $(call Download,check_root_access))

define Download/check_uptime
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_uptime.py
	FILE:=check_uptime.py
	HASH:=51995951c2592153d55a6bf5aeb58d76c394dfe3c76c27a1b0c4d32d6e5e2c0c
endef
$(eval $(call Download,check_uptime))

define Download/check_vpn_tunnels
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_vpn_tunnels.py
	FILE:=check_vpn_tunnels.py
	HASH:=8a12d756d7fee87429cd1846359be6a43c2feb57f32c76b9e4c1a6b3e8b5c7f2
endef
$(eval $(call Download,check_vpn_tunnels))

define Download/check_wan_status
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_wan_status.py
	FILE:=check_wan_status.py
	HASH:=d10f72f902dc58ea9db983a7e50c2a38e2cc0ef72c9bf0a08c5e7b7d6e5f4a3c
endef
$(eval $(call Download,check_wan_status))

define Download/check_wan_throughput
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_wan_throughput.py
	FILE:=check_wan_throughput.py
	HASH:=6ba86bd3a4c3473ed8055744e47d978f8e31e6aff5c8b7a9e1d0c3b2f5a8d1e
endef
$(eval $(call Download,check_wan_throughput))

define Package/ns-checkmk-utils
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Check_MK NethSecurity utilities and plugins
	URL:=https://github.com/nethesis/checkmk-tools
	DEPENDS:=+checkmk-agent
	PKGARCH:=all
endef

define Package/ns-checkmk-utils/description
	NethSecurity-specific plugins and utilities for the Check_MK agent.
	This package extends the base checkmk-agent package with custom monitoring plugins
	tailored for NethSecurity firewall systems.
endef

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	$(CP) $(DL_DIR)/check_apk_packages.py $(PKG_BUILD_DIR)/check_apk_packages.py
	$(CP) $(DL_DIR)/check_dhcp_leases.py $(PKG_BUILD_DIR)/check_dhcp_leases.py
	$(CP) $(DL_DIR)/check_dns_resolution.py $(PKG_BUILD_DIR)/check_dns_resolution.py
	$(CP) $(DL_DIR)/check_firewall_connections.py $(PKG_BUILD_DIR)/check_firewall_connections.py
	$(CP) $(DL_DIR)/check_firewall_rules.py $(PKG_BUILD_DIR)/check_firewall_rules.py
	$(CP) $(DL_DIR)/check_firewall_traffic.py $(PKG_BUILD_DIR)/check_firewall_traffic.py
	$(CP) $(DL_DIR)/check_ovpn_host2net.py $(PKG_BUILD_DIR)/check_ovpn_host2net.py
	$(CP) $(DL_DIR)/check_root_access.py $(PKG_BUILD_DIR)/check_root_access.py
	$(CP) $(DL_DIR)/check_uptime.py $(PKG_BUILD_DIR)/check_uptime.py
	$(CP) $(DL_DIR)/check_vpn_tunnels.py $(PKG_BUILD_DIR)/check_vpn_tunnels.py
	$(CP) $(DL_DIR)/check_wan_status.py $(PKG_BUILD_DIR)/check_wan_status.py
	$(CP) $(DL_DIR)/check_wan_throughput.py $(PKG_BUILD_DIR)/check_wan_throughput.py
endef

define Build/Compile
	true
endef

define Package/ns-checkmk-utils/install
	$(INSTALL_DIR) $(1)/usr/lib/check_mk_agent/local
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_apk_packages.py $(1)/usr/lib/check_mk_agent/local/check_apk_packages
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_dhcp_leases.py $(1)/usr/lib/check_mk_agent/local/check_dhcp_leases
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_dns_resolution.py $(1)/usr/lib/check_mk_agent/local/check_dns_resolution
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_firewall_connections.py $(1)/usr/lib/check_mk_agent/local/check_firewall_connections
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_firewall_rules.py $(1)/usr/lib/check_mk_agent/local/check_firewall_rules
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_firewall_traffic.py $(1)/usr/lib/check_mk_agent/local/check_firewall_traffic
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_ovpn_host2net.py $(1)/usr/lib/check_mk_agent/local/check_ovpn_host2net
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_root_access.py $(1)/usr/lib/check_mk_agent/local/check_root_access
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_uptime.py $(1)/usr/lib/check_mk_agent/local/check_uptime
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_vpn_tunnels.py $(1)/usr/lib/check_mk_agent/local/check_vpn_tunnels
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_wan_status.py $(1)/usr/lib/check_mk_agent/local/check_wan_status
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_wan_throughput.py $(1)/usr/lib/check_mk_agent/local/check_wan_throughput
endef

$(eval $(call BuildPackage,ns-checkmk-utils))
