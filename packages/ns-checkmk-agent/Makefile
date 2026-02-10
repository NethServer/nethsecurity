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

# List of plugin files to download (add more as needed)
PLUGIN_FILES:=check_dhcp_leases.sh check_dns_resolution.sh check_firewall_connections.sh check_firewall_rules.sh check_firewall_traffic.sh check_martian_packets.sh check_opkg_packages.sh check_ovpn_host2net.sh check_root_access.sh check_uptime.sh check_vpn_tunnels.sh check_wan_status.sh

define Build/Prepare
	mkdir -p $(PKG_BUILD_DIR)/plugins

	# Download main Check_MK agent
	wget -O $(PKG_BUILD_DIR)/check_mk_agent $(CHECKMK_AGENT_URL)

	# Download plugin files using shell script loop
	for plugin in $(PLUGIN_FILES); do \
		echo "Downloading plugin: $plugin"; \
		wget -O $(PKG_BUILD_DIR)/plugins/$plugin $(PLUGIN_BASE_URL)/$plugin || \
		echo "Warning: Failed to download $plugin"; \
	done
endef

define Build/Compile
endef

define Package/ns-checkmk-agent/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_DIR) $(1)/usr/lib/check_mk_agent/plugins
	
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/check_mk_agent $(1)/usr/bin/check_mk_agent
	$(INSTALL_BIN) ./files/check_mk_agent.init $(1)/etc/init.d/check_mk_agent
	
	# Install plugin files
	if [ -d $(PKG_BUILD_DIR)/plugins ]; then \
		for plugin in $(PKG_BUILD_DIR)/plugins/*; do \
			[ -f "$plugin" ] && $(INSTALL_BIN) "$plugin" $(1)/usr/lib/check_mk_agent/plugins/; \
		done; \
	fi
endef

$(eval $(call BuildPackage,ns-checkmk-agent))
