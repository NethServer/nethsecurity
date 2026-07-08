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
	HASH:=c85fc116edb1e75f59c0596a3e93913cc3cb2fdc30308a5c060c3f5c648bd26b
endef
$(eval $(call Download,check_apk_packages))

define Download/check_dhcp_leases
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_dhcp_leases.py
	FILE:=check_dhcp_leases.py
	HASH:=42dbbd3ad2d9e45f97d9f383afaeae85dcf761ba18a13a7b42fa7f1b2c011b96
endef
$(eval $(call Download,check_dhcp_leases))

define Download/check_dns_resolution
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_dns_resolution.py
	FILE:=check_dns_resolution.py
	HASH:=a2f1309d70a142d41a0e9fd3c47ffd7aba52727fd68ec33e1f60311a944792e5
endef
$(eval $(call Download,check_dns_resolution))

define Download/check_firewall_connections
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_connections.py
	FILE:=check_firewall_connections.py
	HASH:=68e259d3f9649c4c3447b97539d6d474e494e391d3f73b1fffd8a99b184e2eca
endef
$(eval $(call Download,check_firewall_connections))

define Download/check_firewall_rules
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_rules.py
	FILE:=check_firewall_rules.py
	HASH:=92e99de0482407a323c692750d265491aa0c62fe37589845cc8ff8cd5f59ddc8
endef
$(eval $(call Download,check_firewall_rules))

define Download/check_firewall_traffic
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_traffic.py
	FILE:=check_firewall_traffic.py
	HASH:=8ea2f633b359652496b176b40727bece6726b0be5c5aac08cc6e613f48596295
endef
$(eval $(call Download,check_firewall_traffic))

define Download/check_ovpn_host2net
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_ovpn_host2net.py
	FILE:=check_ovpn_host2net.py
	HASH:=3680793726763ff7bd71d1a298d36dadb67be7b6c91831589ae86a70c6a19a94
endef
$(eval $(call Download,check_ovpn_host2net))

define Download/check_root_access
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_root_access.py
	FILE:=check_root_access.py
	HASH:=84806b5dabb6985674caca02153fd022f996948bab20639b27553950cc350f2f
endef
$(eval $(call Download,check_root_access))

define Download/check_uptime
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_uptime.py
	FILE:=check_uptime.py
	HASH:=388a9a51887248df4248bb604da8059bc746f32732bba9cf8e232292f878cd28
endef
$(eval $(call Download,check_uptime))

define Download/check_vpn_tunnels
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_vpn_tunnels.py
	FILE:=check_vpn_tunnels.py
	HASH:=82a4701f041512840d88d54802295537ae6ab73cfbc07a990866684886e00d49
endef
$(eval $(call Download,check_vpn_tunnels))

define Download/check_wan_status
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_wan_status.py
	FILE:=check_wan_status.py
	HASH:=e245549eda4df50703cf98f10ef1f42dfeff3befd4d1a922cc17218521f0f69c
endef
$(eval $(call Download,check_wan_status))

define Download/check_wan_throughput
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_wan_throughput.py
	FILE:=check_wan_throughput.py
	HASH:=73326e5b3109e1f008c6f07e6497ec69f1d2886dd89e357b7b51096cc6e8958b
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
