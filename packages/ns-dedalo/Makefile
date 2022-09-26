#
# Copyright (C) 2022 Nethesis
#
# This is free software, licensed under the GNU General Public License v3.
#

include $(TOPDIR)/rules.mk
 
PKG_NAME:=ns-dedalo
PKG_VERSION:=0.0.1
PKG_RELEASE:=$(AUTORELEASE)
 
PKG_BUILD_DIR:=$(BUILD_DIR)/ns-dedalo-$(PKG_VERSION)

PKG_MAINTAINER:=Giacomo Sanchietti <giacomo.sanchietti@nethesis.it>
PKG_LICENSE:=GPL-3.0-only

PKG_SOURCE_PROTO:=git
PKG_SOURCE_URL:=https://github.com/nethesis/icaro.git
PKG_SOURCE_VERSION:=v85

include $(INCLUDE_DIR)/package.mk
 
define Package/ns-dedalo
	SECTION:=base
	CATEGORY:=NextSecurity
	TITLE:=Dedalo Network Access Controller, runs on the firewall and intercepts all guest connections
	URL:=https://github.com/nethesis/icaro
	DEPENDS:=+curl +grep +ca-bundle +haserl +uuidgen +coova-chilli
	PKGARCH:=all
endef
 
define Package/ns-dedalo/description
	Dedalo is the Network Access Controller, runs on the firewall and intercepts all guest connections.
	It's a configuration helper for Coova-Chilli
endef

# this is required, otherwise compile will fail
define Build/Compile
endef

define Package/ns-dedalo/conffiles
/etc/config/dedalo
endef

define Package/ns-dedalo/networks_config

set network.hotspot=interface
set network.hotspot.proto='none'
set network.hotspot.type=bridge
set network.hotspot.ipv6=0

set network.dedalo=interface
set network.dedalo.proto='none'
set network.dedalo.ifname='tun-dedalo'
set network.dedalo.ipv6=0

commit

endef

define Package/ns-dedalo/firewall_config

set firewall.hotspot=zone
set firewall.hotspot.name='hotspot'
set firewall.hotspot.network='hotspot'
set firewall.hotspot.mtu_fix=1
set firewall.hotspot.forward='DROP'
set firewall.hotspot.input='DROP'
set firewall.hotspot.output='ACCEPT'

set firewall.dedalo=zone
set firewall.dedalo.name='dedalo'
set firewall.dedalo.network='dedalo'
set firewall.dedalo.mtu_fix=1
set firewall.dedalo.forward='DROP'
set firewall.dedalo.input='DROP'
set firewall.dedalo.output='ACCEPT'

set firewall forwarding
set firewall.@forwarding[-1].src='dedalo'
set firewall.@forwarding[-1].dest='wan'

set firewall.hs_uamport=rule
set firewall.hs_uamport.name='hs_uamport'
set firewall.hs_uamport.src='dedalo'
set firewall.hs_uamport.proto='tcp'
set firewall.hs_uamport.dest_port='3990'
set firewall.hs_uamport.target='ACCEPT'

set firewall.hs_dhcp_broadcast=rule
set firewall.hs_dhcp_broadcast.name='hs_dhcp_broadcast'
set firewall.hs_dhcp_broadcast.family='ipv4'
set firewall.hs_dhcp_broadcast.src='dedalo'
set firewall.hs_dhcp_broadcast.proto='udp'
set firewall.hs_dhcp_broadcast.dest_ip='255.255.255.255'
set firewall.hs_dhcp_broadcast.dest_port='67:68'
set firewall.hs_dhcp_broadcast.target='ACCEPT'

set firewall.hs_dhcp=rule
set firewall.hs_dhcp.name='hs_dhcp'
set firewall.hs_dhcp.src='dedalo'
set firewall.hs_dhcp.proto='udp'
set firewall.hs_dhcp.dest_port='67:68'
set firewall.hs_dhcp.target='ACCEPT'

set firewall.hs_dns=rule
set firewall.hs_dns.name='hs_dns'
set firewall.hs_dns.src='dedalo'
set firewall.hs_dns.proto='udp'
set firewall.hs_dns.dest_port='53'
set firewall.hs_dns.target='ACCEPT'

set firewall.hs_icmp=rule
set firewall.hs_icmp.name='hs_icmp'
set firewall.hs_icmp.src='dedalo'
set firewall.hs_icmp.proto='icmp'
set firewall.hs_icmp.target='ACCEPT'

set firewall.host_include=include
set firewall.host_include.path='/etc/firewall.dedalo'

commit

endef

define Package/ns-dedalo/postinst
#!/bin/sh
if [ -z "$${IPKG_INSTROOT}" ]; then
uci batch <<EOF
$(Package/ns-dedalo/networks_config)
EOF
uci batch <<EOF
$(Package/ns-dedalo/firewall_config)
EOF
else
echo "#!/bin/sh" > $${IPKG_INSTROOT}/etc/uci-defaults/dedalo
echo uci batch "<<EOF" "$(Package/ns-dedalo/networks_config)""EOF" >> $${IPKG_INSTROOT}/etc/uci-defaults/dedalo
echo uci batch "<<EOF" "$(Package/ns-dedalo/firewall_config)""EOF" >> $${IPKG_INSTROOT}/etc/uci-defaults/dedalo
echo "exit 0" >> $${IPKG_INSTROOT}/etc/uci-defaults/dedalo
set +x /etc/uci-defaults/dedalo
fi
exit 0
endef

define Package/ns-dedalo/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/dedalo/dedalo $(1)/usr/bin/

	$(INSTALL_DIR) $(1)/opt/icaro/dedalo
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/dedalo/config $(1)/opt/icaro/dedalo/config
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/dedalo/up.sh $(1)/opt/icaro/dedalo/
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/dedalo/down.sh $(1)/opt/icaro/dedalo/
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/dedalo/dedalo_users_auth.sh $(1)/opt/icaro/dedalo/

	$(INSTALL_DIR) $(1)/opt/icaro/dedalo/template
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/dedalo/template/engine $(1)/opt/icaro/dedalo/template/engine
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/dedalo/template/chilli.conf.tpl $(1)/opt/icaro/dedalo/template/chilli.conf.tpl

	$(INSTALL_DIR) $(1)/opt/icaro/dedalo/walled_gardens/integrations
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/dedalo/walled_gardens/facebook.conf $(1)/opt/icaro/dedalo/walled_gardens/facebook.conf
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/dedalo/walled_gardens/linkedin.conf $(1)/opt/icaro/dedalo/walled_gardens/linkedin.conf
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/dedalo/walled_gardens/instagram.conf $(1)/opt/icaro/dedalo/walled_gardens/instagram.conf
	$(INSTALL_CONF) $(PKG_BUILD_DIR)/dedalo/walled_gardens/wifi4eu.conf $(1)/opt/icaro/dedalo/walled_gardens/wifi4eu.conf

	$(INSTALL_DIR) $(1)/opt/icaro/dedalo/www
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/dedalo/www/temporary.chi $(1)/opt/icaro/dedalo/www/temporary.chi

	touch $(1)/opt/icaro/dedalo/local.conf
	touch $(1)/opt/icaro/dedalo/walled_gardens/local.conf

	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_BIN) files/dedalo.init $(1)/etc/init.d/dedalo
	$(INSTALL_BIN) files/dedalo_users_auth.init $(1)/etc/init.d/dedalo_users_auth
	$(INSTALL_DIR) $(1)/etc/config
	$(INSTALL_DATA) files/dedalo.config $(1)/etc/config/dedalo
	$(INSTALL_DIR) $(1)/etc/
	$(INSTALL_DATA) files/firewall.dedalo $(1)/etc/firewall.dedalo
endef
 
$(eval $(call BuildPackage,ns-dedalo))
