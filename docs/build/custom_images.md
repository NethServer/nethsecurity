---
layout: default
title: Custom images
parent: Build system
---

# Custom images

You can create custom images using [Image Builder](https://openwrt.org/docs/guide-user/additional-software/imagebuilder).

Download the image builder from:
```
https://updates.nethsecurity.nethserver.org/stable/<owrt_version>/targets/x86/64/nethsecurity-imagebuilder-8-<owrt_version>-ns.<nsec_version>-x86-64.Linux-x86_64.tar.xz
```

Replace `owrt_version` with the latest OpenWrt release, like `23.05.05` and `nsec_version` with lates NethSecurity release like `1.4.1`.

## Using Image Builder inside CentOS 7

Install the dependencies:
```
yum install perl-Thread-Queue devtoolset-7-make git unzip bzip2
```

Upload the builder inside the system and prepare it:
```
mkdir builder; tar xvf nethsecurity-imagebuilder-22.03.0-x86-64.Linux-x86_64.tar.xz -C builder
cd builder
sed -i '/logd \\/d' include/target.mk
```
Note: OpenWrt build system assumes logd is always installed, but NethSecurity image does not ship it.
The `sed` command ensure logd is not bundled inside the image.

Prepare the files directory:
```
wget https://github.com/NethServer/nethsecurity/archive/refs/heads/master.tar.gz
tar xvf master.tar.gz nethsecurity-master/files/
```

To include custom files, add them inside `nethsecurity-master/files` directory
with the full path, like:
```
echo "hello" > file/root/goofy
```

Start the build with all included packages:
```
source /opt/rh/devtoolset-7/enable
make image  FILES="nethsecurity-master/files/" PACKAGES="$(grep "Package: " packages/Packages | cut -d ':' -f 2 | tr '\n' ' ')"
```
