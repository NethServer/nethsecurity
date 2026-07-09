#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=ns-checkmk-utils
# renovate: datasource=github-tags depName=nethesis/checkmk-tools
PKG_VERSION:=1.7.4
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
	FILE:=check_apk_packages-$(PKG_VERSION).py
	HASH:=137a0b7b1d390e079cb87853c141239a3ea153c1dbd7d7f4d35461e479ef6b8a
endef
$(eval $(call Download,check_apk_packages))

define Download/check_dhcp_leases
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_dhcp_leases.py
	FILE:=check_dhcp_leases-$(PKG_VERSION).py
	HASH:=04be52f99fd61f504a28e20971a6774780caec0b9785757130b2cb090c30470d
endef
$(eval $(call Download,check_dhcp_leases))

define Download/check_dns_resolution
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_dns_resolution.py
	FILE:=check_dns_resolution-$(PKG_VERSION).py
	HASH:=de7db1ea7c1ae62dab069af6a9f7539b2b76a485ae32ecd4a4a18d5c36840211
endef
$(eval $(call Download,check_dns_resolution))

define Download/check_firewall_connections
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_connections.py
	FILE:=check_firewall_connections-$(PKG_VERSION).py
	HASH:=60198e7267a2025da750a9135095d4211e198fdbce8beeb4ef12b3f0849b4801
endef
$(eval $(call Download,check_firewall_connections))

define Download/check_firewall_rules
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_rules.py
	FILE:=check_firewall_rules-$(PKG_VERSION).py
	HASH:=ceee4261b343fc1a345de16e0fe60a03f34c9da357d3a86041bcf3d6afa0c8a0
endef
$(eval $(call Download,check_firewall_rules))

define Download/check_firewall_traffic
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_traffic.py
	FILE:=check_firewall_traffic-$(PKG_VERSION).py
	HASH:=53b4fac2a085442070e39c3a0aaa1ea04f411e881e6e4d803ee23f7fd28ab338
endef
$(eval $(call Download,check_firewall_traffic))

define Download/check_ovpn_host2net
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_ovpn_host2net.py
	FILE:=check_ovpn_host2net-$(PKG_VERSION).py
	HASH:=ba6775e8e4e07221d38478e9e0a95e5c45a57cc47096a8ca35a0265732cbbd57
endef
$(eval $(call Download,check_ovpn_host2net))

define Download/check_root_access
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_root_access.py
	FILE:=check_root_access-$(PKG_VERSION).py
	HASH:=875fc88daa629b06449b4afdf4ba3afaeba62bc5ce7507d7f366f00251a34f1f
endef
$(eval $(call Download,check_root_access))

define Download/check_uptime
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_uptime.py
	FILE:=check_uptime-$(PKG_VERSION).py
	HASH:=c7fdd501c8bb6f6be44638403ee917c9b38414e38331620acd8c3aca50f9ecf5
endef
$(eval $(call Download,check_uptime))

define Download/check_vpn_tunnels
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_vpn_tunnels.py
	FILE:=check_vpn_tunnels-$(PKG_VERSION).py
	HASH:=1d7cd69f3615dd52bceb01ddee929a6b9df564e82f42f5d934a9d818a9b96667
endef
$(eval $(call Download,check_vpn_tunnels))

define Download/check_wan_status
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_wan_status.py
	FILE:=check_wan_status-$(PKG_VERSION).py
	HASH:=7681b3bae32bccfa47f33413f6a8a9ba8a7f2869bb887488fac723d36b224a95
endef
$(eval $(call Download,check_wan_status))

define Download/check_wan_throughput
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_wan_throughput.py
	FILE:=check_wan_throughput-$(PKG_VERSION).py
	HASH:=1d1f9f0c78d58dd0a57491aa1029981ad683fc565c27fb262d3142a880fdbc51
endef
$(eval $(call Download,check_wan_throughput))

define Package/ns-checkmk-utils
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Check_MK NethSecurity utilities and plugins
	URL:=https://github.com/nethesis/checkmk-tools
	DEPENDS:=+checkmk-agent +python3-base
	PKGARCH:=all
endef

define Package/ns-checkmk-utils/description
	NethSecurity-specific plugins and utilities for the Check_MK agent.
	This package extends the base checkmk-agent package with custom monitoring plugins
	tailored for NethSecurity firewall systems.
endef

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)
	$(CP) $(DL_DIR)/check_apk_packages-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_apk_packages.py
	$(CP) $(DL_DIR)/check_dhcp_leases-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_dhcp_leases.py
	$(CP) $(DL_DIR)/check_dns_resolution-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_dns_resolution.py
	$(CP) $(DL_DIR)/check_firewall_connections-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_firewall_connections.py
	$(CP) $(DL_DIR)/check_firewall_rules-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_firewall_rules.py
	$(CP) $(DL_DIR)/check_firewall_traffic-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_firewall_traffic.py
	$(CP) $(DL_DIR)/check_ovpn_host2net-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_ovpn_host2net.py
	$(CP) $(DL_DIR)/check_root_access-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_root_access.py
	$(CP) $(DL_DIR)/check_uptime-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_uptime.py
	$(CP) $(DL_DIR)/check_vpn_tunnels-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_vpn_tunnels.py
	$(CP) $(DL_DIR)/check_wan_status-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_wan_status.py
	$(CP) $(DL_DIR)/check_wan_throughput-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_wan_throughput.py
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
