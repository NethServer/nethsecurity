#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=ns-checkmk-utils
# renovate: datasource=github-tags depName=nethesis/checkmk-tools
PKG_VERSION:=0.0.5
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
	FILE:=check_dhcp_leases.py
	HASH:=f168703fa052f84a7f10c5dfceb3f566c18a8accf36767b0ace7eeecb70b5887
endef
$(eval $(call Download,check_dhcp_leases))

define Download/check_dns_resolution
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_dns_resolution.py
	FILE:=check_dns_resolution.py
	HASH:=a06de9d22df448800a1faf7cdb0a5580e0d2cfcbd3b20473e275f0ebd9086fcc
endef
$(eval $(call Download,check_dns_resolution))

define Download/check_firewall_connections
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_connections.py
	FILE:=check_firewall_connections.py
	HASH:=9aff21e3586cb36e72461f508bf7e4ececcefa1c956b07aa8dbba9d2163d3c48
endef
$(eval $(call Download,check_firewall_connections))

define Download/check_firewall_rules
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_rules.py
	FILE:=check_firewall_rules.py
	HASH:=db030f004c14955564e57ecc4e60f8b991c8e41ef090eba3b1c066bd4dfb8236
endef
$(eval $(call Download,check_firewall_rules))

define Download/check_firewall_traffic
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_firewall_traffic.py
	FILE:=check_firewall_traffic.py
	HASH:=fd76b8856a709898c05ec5b1468a028df8c5d292cbdc8890d75d47c061970bdd
endef
$(eval $(call Download,check_firewall_traffic))

define Download/check_martian_packets
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_martian_packets.py
	FILE:=check_martian_packets.py
	HASH:=577060f8c53f1c43bd216de4be921ac0a06fe91de1052d45b176f6d74805c71a
endef
$(eval $(call Download,check_martian_packets))

define Download/check_opkg_packages
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_opkg_packages.py
	FILE:=check_opkg_packages.py
	HASH:=ea8908e519e557dcd813138ae351becc75a2d6815d04e7a8a6de2479c244219d
endef
$(eval $(call Download,check_opkg_packages))

define Download/check_ovpn_host2net
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_ovpn_host2net.py
	FILE:=check_ovpn_host2net.py
	HASH:=ecf4f3240276fad68e33f4124c50f41a61fcb4afc4a64914791825a0574f7c57
endef
$(eval $(call Download,check_ovpn_host2net))

define Download/check_root_access
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_root_access.py
	FILE:=check_root_access.py
	HASH:=086dbbbdb30b4b8bbf77bf3bf0f0c5b7daa07c04bcf1acefb9771ebc79aa9b98
endef
$(eval $(call Download,check_root_access))

define Download/check_uptime
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_uptime.py
	FILE:=check_uptime.py
	HASH:=ad67d9824a598d06f9c8c7f74f1f0ff295645f1e6780ab745a3fd956005d630d
endef
$(eval $(call Download,check_uptime))

define Download/check_vpn_tunnels
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_vpn_tunnels.py
	FILE:=check_vpn_tunnels.py
	HASH:=992d94c7bf5cc5329e4ef877b5ea0a3c56a247d687d9017c28add069be4886da
endef
$(eval $(call Download,check_vpn_tunnels))

define Download/check_wan_status
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_wan_status.py
	FILE:=check_wan_status.py
	HASH:=848ee2dc5526be9d193ad5f7aa23dec3f217c8bc93e7eee7a5e0efa71f83535f
endef
$(eval $(call Download,check_wan_status))

define Download/check_wan_throughput
	URL:=$(NS_CHECKMK_UTILS_BASE_URL)
	URL_FILE:=check_wan_throughput.py
	FILE:=check_wan_throughput.py
	HASH:=90b4f106f1a8027cc696217c2da40c35bf6e766aa06b2fc534704824332dfe47
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
	$(CP) $(DL_DIR)/check_dhcp_leases.py $(PKG_BUILD_DIR)/check_dhcp_leases.py
	$(CP) $(DL_DIR)/check_dns_resolution.py $(PKG_BUILD_DIR)/check_dns_resolution.py
	$(CP) $(DL_DIR)/check_firewall_connections.py $(PKG_BUILD_DIR)/check_firewall_connections.py
	$(CP) $(DL_DIR)/check_firewall_rules.py $(PKG_BUILD_DIR)/check_firewall_rules.py
	$(CP) $(DL_DIR)/check_firewall_traffic.py $(PKG_BUILD_DIR)/check_firewall_traffic.py
	$(CP) $(DL_DIR)/check_martian_packets.py $(PKG_BUILD_DIR)/check_martian_packets.py
	$(CP) $(DL_DIR)/check_opkg_packages.py $(PKG_BUILD_DIR)/check_opkg_packages.py
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
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_dhcp_leases.py $(1)/usr/lib/check_mk_agent/local/check_dhcp_leases
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_dns_resolution.py $(1)/usr/lib/check_mk_agent/local/check_dns_resolution
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_firewall_connections.py $(1)/usr/lib/check_mk_agent/local/check_firewall_connections
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_firewall_rules.py $(1)/usr/lib/check_mk_agent/local/check_firewall_rules
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_firewall_traffic.py $(1)/usr/lib/check_mk_agent/local/check_firewall_traffic
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_martian_packets.py $(1)/usr/lib/check_mk_agent/local/check_martian_packets
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_opkg_packages.py $(1)/usr/lib/check_mk_agent/local/check_opkg_packages
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_ovpn_host2net.py $(1)/usr/lib/check_mk_agent/local/check_ovpn_host2net
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_root_access.py $(1)/usr/lib/check_mk_agent/local/check_root_access
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_uptime.py $(1)/usr/lib/check_mk_agent/local/check_uptime
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_vpn_tunnels.py $(1)/usr/lib/check_mk_agent/local/check_vpn_tunnels
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_wan_status.py $(1)/usr/lib/check_mk_agent/local/check_wan_status
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_wan_throughput.py $(1)/usr/lib/check_mk_agent/local/check_wan_throughput
endef

$(eval $(call BuildPackage,ns-checkmk-utils))
