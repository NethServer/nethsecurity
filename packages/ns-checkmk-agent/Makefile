#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

include $(TOPDIR)/rules.mk

PKG_NAME:=ns-checkmk-agent
PKG_VERSION:=0.0.1
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/ns-checkmk-agent-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

include $(INCLUDE_DIR)/package.mk

define Package/ns-checkmk-agent
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=Check_MK monitoring agent
	URL:=https://github.com/Checkmk/checkmk
	DEPENDS:=+socat
	PKGARCH:=all
endef

define Package/ns-checkmk-agent/description
	Check_MK monitoring agent for NethSecurity with custom plugins
endef

# Base URLs for downloads
CHECKMK_AGENT_URL:=https://raw.githubusercontent.com/Checkmk/checkmk/master/agents/check_mk_agent.openwrt
PLUGIN_BASE_URL:=https://raw.githubusercontent.com/Coverup20/checkmk-tools/refs/heads/main/script-check-nsec8/full

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)/plugins

	# Download main Check_MK agent
	wget -O $(PKG_BUILD_DIR)/check_mk_agent $(CHECKMK_AGENT_URL)

	# Download all plugins
	wget -O $(PKG_BUILD_DIR)/plugins/check_dhcp_leases.sh $(PLUGIN_BASE_URL)/check_dhcp_leases.sh
	wget -O $(PKG_BUILD_DIR)/plugins/check_dns_resolution.sh $(PLUGIN_BASE_URL)/check_dns_resolution.sh
	wget -O $(PKG_BUILD_DIR)/plugins/check_firewall_connections.sh $(PLUGIN_BASE_URL)/check_firewall_connections.sh
	wget -O $(PKG_BUILD_DIR)/plugins/check_firewall_rules.sh $(PLUGIN_BASE_URL)/check_firewall_rules.sh
	wget -O $(PKG_BUILD_DIR)/plugins/check_firewall_traffic.sh $(PLUGIN_BASE_URL)/check_firewall_traffic.sh
	wget -O $(PKG_BUILD_DIR)/plugins/check_martian_packets.sh $(PLUGIN_BASE_URL)/check_martian_packets.sh
	wget -O $(PKG_BUILD_DIR)/plugins/check_opkg_packages.sh $(PLUGIN_BASE_URL)/check_opkg_packages.sh
	wget -O $(PKG_BUILD_DIR)/plugins/check_ovpn_host2net.sh $(PLUGIN_BASE_URL)/check_ovpn_host2net.sh
	wget -O $(PKG_BUILD_DIR)/plugins/check_root_access.sh $(PLUGIN_BASE_URL)/check_root_access.sh
	wget -O $(PKG_BUILD_DIR)/plugins/check_uptime.sh $(PLUGIN_BASE_URL)/check_uptime.sh
	wget -O $(PKG_BUILD_DIR)/plugins/check_vpn_tunnels.sh $(PLUGIN_BASE_URL)/check_vpn_tunnels.sh
	wget -O $(PKG_BUILD_DIR)/plugins/check_wan_status.sh $(PLUGIN_BASE_URL)/check_wan_status.sh
endef

define Build/Compile
endef

define Package/ns-checkmk-agent/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_DIR) $(1)/usr/lib/check_mk_agent/plugins
	
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_mk_agent $(1)/usr/bin/check_mk_agent
	$(INSTALL_BIN) ./files/check_mk_agent.init $(1)/etc/init.d/check_mk_agent
	
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/plugins/check_dhcp_leases.sh $(1)/usr/lib/check_mk_agent/plugins/check_dhcp_leases.sh
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/plugins/check_dns_resolution.sh $(1)/usr/lib/check_mk_agent/plugins/check_dns_resolution.sh
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/plugins/check_firewall_connections.sh $(1)/usr/lib/check_mk_agent/plugins/check_firewall_connections.sh
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/plugins/check_firewall_rules.sh $(1)/usr/lib/check_mk_agent/plugins/check_firewall_rules.sh
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/plugins/check_firewall_traffic.sh $(1)/usr/lib/check_mk_agent/plugins/check_firewall_traffic.sh
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/plugins/check_martian_packets.sh $(1)/usr/lib/check_mk_agent/plugins/check_martian_packets.sh
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/plugins/check_opkg_packages.sh $(1)/usr/lib/check_mk_agent/plugins/check_opkg_packages.sh
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/plugins/check_ovpn_host2net.sh $(1)/usr/lib/check_mk_agent/plugins/check_ovpn_host2net.sh
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/plugins/check_root_access.sh $(1)/usr/lib/check_mk_agent/plugins/check_root_access.sh
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/plugins/check_uptime.sh $(1)/usr/lib/check_mk_agent/plugins/check_uptime.sh
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/plugins/check_vpn_tunnels.sh $(1)/usr/lib/check_mk_agent/plugins/check_vpn_tunnels.sh
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/plugins/check_wan_status.sh $(1)/usr/lib/check_mk_agent/plugins/check_wan_status.sh
endef

$(eval $(call BuildPackage,ns-checkmk-agent))
