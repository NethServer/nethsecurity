#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=ns-checkmk-utils
PKG_VERSION:=1.7.7
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/ns-checkmk-utils-$(PKG_VERSION)

PKG_MAINTAINER:=Tommaso Bailetti <tommaso.bailetti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

# Base URL for downloads
NS_CHECKMK_UTILS_BASE_URL:=https://raw.githubusercontent.com/nethesis/checkmk-tools/v$(PKG_VERSION)/script-check-nsec8/full

include $(INCLUDE_DIR)/package.mk

define Download/check_dhcp_leases
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_dhcp_leases.py
	FILE:=check_dhcp_leases-$(PKG_VERSION).py
	HASH:=48d4d1d7e77f126af286857987c2214a15eed9fc219f7d5b40a218999d8ebeba
endef
$(eval $(call Download,check_dhcp_leases))

define Download/check_dns_resolution
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_dns_resolution.py
	FILE:=check_dns_resolution-$(PKG_VERSION).py
	HASH:=fd1ff4f5b7cc854416c0aeabf492097ee00307944e3b3d676a311ecf978d0015
endef
$(eval $(call Download,check_dns_resolution))

define Download/check_firewall_connections
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_connections.py
	FILE:=check_firewall_connections-$(PKG_VERSION).py
	HASH:=b02b0d860c8cd4c815509b6fff366d7de3cf7445dd3dff0da747499176c657d8
endef
$(eval $(call Download,check_firewall_connections))

define Download/check_firewall_rules
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_rules.py
	FILE:=check_firewall_rules-$(PKG_VERSION).py
	HASH:=508d626f7effcbf63418c09daf10d3b8de0dc307ad75afac208fc99c19ba3771
endef
$(eval $(call Download,check_firewall_rules))

define Download/check_firewall_traffic
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_traffic.py
	FILE:=check_firewall_traffic-$(PKG_VERSION).py
	HASH:=59f1a8016292d5ef9feb9d034218ec3bbdd5ef2a33ab0a5390f5fa5836ebfd31
endef
$(eval $(call Download,check_firewall_traffic))

define Download/check_ovpn_host2net
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_ovpn_host2net.py
	FILE:=check_ovpn_host2net-$(PKG_VERSION).py
	HASH:=499d8423d5c03c563852383a7574c82bc22fbf3f5d3a6e4281dc41c150e2a612
endef
$(eval $(call Download,check_ovpn_host2net))

define Download/check_root_access
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_root_access.py
	FILE:=check_root_access-$(PKG_VERSION).py
	HASH:=de1825928c5e3879724ea4ea4a17d47ab8a97925cff6c060802a0bcb0e67918e
endef
$(eval $(call Download,check_root_access))

define Download/check_vpn_tunnels
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_vpn_tunnels.py
	FILE:=check_vpn_tunnels-$(PKG_VERSION).py
	HASH:=ce15c3f71c8a1cebb06b74dfe772e5c79baf4339f7eada5f654b7ae84e538e44
endef
$(eval $(call Download,check_vpn_tunnels))

define Download/check_wan_status
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_wan_status.py
	FILE:=check_wan_status-$(PKG_VERSION).py
	HASH:=1e721d9f606c44abe2d430e39c7b672e0798d5fc04c19e991c4c2ffbc0eecdfc
endef
$(eval $(call Download,check_wan_status))

define Download/check_wan_throughput
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_wan_throughput.py
	FILE:=check_wan_throughput-$(PKG_VERSION).py
	HASH:=e0e7744e3a3ae2d9ea720980967b7e6d09499c51de722af1e977713e66ec7b56
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
	$(CP) $(DL_DIR)/check_dhcp_leases-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_dhcp_leases.py
	$(CP) $(DL_DIR)/check_dns_resolution-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_dns_resolution.py
	$(CP) $(DL_DIR)/check_firewall_connections-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_firewall_connections.py
	$(CP) $(DL_DIR)/check_firewall_rules-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_firewall_rules.py
	$(CP) $(DL_DIR)/check_firewall_traffic-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_firewall_traffic.py
	$(CP) $(DL_DIR)/check_ovpn_host2net-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_ovpn_host2net.py
	$(CP) $(DL_DIR)/check_root_access-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_root_access.py
	$(CP) $(DL_DIR)/check_vpn_tunnels-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_vpn_tunnels.py
	$(CP) $(DL_DIR)/check_wan_status-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_wan_status.py
	$(CP) $(DL_DIR)/check_wan_throughput-$(PKG_VERSION).py $(PKG_BUILD_DIR)/check_wan_throughput.py
endef

define Build/Compile
	true
endef

define Package/ns-checkmk-utils/install
	$(INSTALL_DIR) $(1)/usr/lib/check_mk_agent/local
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_dhcp_leases.py $(1)/usr/lib/check_mk_agent/local/check_dhcp_leases
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_dns_resolution.py $(1)/usr/lib/check_mk_agent/local/check_dns_resolution
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_firewall_connections.py $(1)/usr/lib/check_mk_agent/local/check_firewall_connections
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_firewall_rules.py $(1)/usr/lib/check_mk_agent/local/check_firewall_rules
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_firewall_traffic.py $(1)/usr/lib/check_mk_agent/local/check_firewall_traffic
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_ovpn_host2net.py $(1)/usr/lib/check_mk_agent/local/check_ovpn_host2net
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_root_access.py $(1)/usr/lib/check_mk_agent/local/check_root_access
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_vpn_tunnels.py $(1)/usr/lib/check_mk_agent/local/check_vpn_tunnels
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_wan_status.py $(1)/usr/lib/check_mk_agent/local/check_wan_status
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_wan_throughput.py $(1)/usr/lib/check_mk_agent/local/check_wan_throughput
endef

$(eval $(call BuildPackage,ns-checkmk-utils))
