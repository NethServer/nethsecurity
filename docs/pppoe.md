---
layout: default
title: PPPoE server
nav_order: 10
---

# Setup PPPoE testing server

This guide will describe how to setup a PPPoE testing server using
Debian 11.

Setup a clean Debian server 11 installation with at least one
ethernet interface and with Internet access.
Let's assume the network interface is called `enp1s0`.

Install dependencies:
```
apt-get install pppoe iptables
```

Create `test` user with password `password`:
```
useradd test
echo -e "password\npassword\n" | passwd test

cat << EOF > /etc/ppp/chap-secrets
"test"  * "password"    100.64.0.2
EOF

chmod 600 /etc/ppp/chap-secrets
```

Setup and start PPPoE server:
```
echo 100.64.0.2-30 > /etc/ppp/ipaddress_pool

cat <<EOF > /etc/ppp/pppoe-server-options
require-chap
login
lcp-echo-interval 5
lcp-echo-failure 0
ms-dns 1.1.1.1
netmask 255.255.255.0
defaultroute
noipdefault
usepeerdns
debug
logfile /var/log/pppoe-server.log
EOF

pppoe-server -C isp -L 100.64.0.1 -p /etc/ppp/ipaddress_pool -I enp1s0 -m 1412
```

Setup IP forward and masquerading:
```
echo 1 > /proc/sys/net/ipv4/ip_forward
iptables -t nat -F POSTROUTING
iptables -t nat -A POSTROUTING -o enp1s0 -j MASQUERADE
```

Reference: https://poundcomment.wordpress.com/2011/03/30/pppoe-server-on-ubuntu/

## Setup VLAN tagged server

Install user space tool and load kernel module:
```
apt install vlan
modprobe 8021q
```

Setup VLAN, IP forward and masquerading:
```
echo 1 > /proc/sys/net/ipv4/ip_forward
ip link add link enp1s0 name enp1s0.100 type vlan id 100
ip link set dev enp1s0.100 up
iptables -t nat -F POSTROUTING
iptables -A FORWARD -i enp1s0 -o enp1s0.100 -j ACCEPT
iptables -t nat -A POSTROUTING -o enp1s0 -j MASQUERADE
```

Start the server:
```
pppoe-server -C isp -L 100.64.0.1 -p /etc/ppp/ipaddress_pool -I enp1s0.100 -m 1412
```

## Setup OpenWrt PPPoE client

You can setup everything from the UI, but make sure to set an high value (eg. 100)
for `LCP echo failure threshold` field.

If you prefer the command line: 
```
uci set network.wan.proto='pppoe'
uci set network.wan.username='test'
uci set network.wan.password='password'
uci set network.wan.ipv6=0
uci set network.wan.keepalive="100 5"
uci commit network
service network restart
```
