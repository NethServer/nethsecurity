---
layout: default
title: Package repositories
nav_order: 30
---

# Package repositories

Official package repository is hosted at [{{site.download_url}}]({{site.download_url}}/index.html).

You can add custom feeds by changing the `/etc/opkg/customfeeds.conf` file.

To enable upstream package repositories use the following commands
```bash
source /etc/os-release
cat << EOF > /etc/opkg/customfeeds.conf 
src/gz core https://downloads.openwrt.org/releases/$VERSION/targets/x86/64/packages
src/gz base https://downloads.openwrt.org/releases/$VERSION/packages/x86_64/base
src/gz luci https://downloads.openwrt.org/releases/$VERSION/packages/x86_64/luci
src/gz packages https://downloads.openwrt.org/releases/$VERSION/packages/x86_64/packages
src/gz routing https://downloads.openwrt.org/releases/$VERSION/packages/x86_64/routing
EOF
```
