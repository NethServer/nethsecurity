---
layout: default
title: Custom images
nav_order: 25
---

# Custom images

You can create custom images using [Image Builder](https://openwrt.org/docs/guide-user/additional-software/imagebuilder).

Since Image Builder is not built by default, you will need to build it:

1. setup a local [build environment](../build)
2. enable Image Builder
   ```
   cat << EOF > config/image_builder.conf
   CONFIG_IB=y
   CONFIG_IB_STANDALONE=y
   EOF
   ```
3. run the build process:
   ```
   ./run
   ```
4. you will find the Image Builder inside `bin/targets/x86/64/nextsecurity-imagebuilder->version>-x86-64.Linux-x86_64.tar.xz`

## Using Image Builder inside CentOS 7

Install the dependencies:
```
yum install perl-Thread-Queue devtoolset-7-make git unzip bzip2
```

Upload the builder inside the system and prepare it:
```
mkdir builder; tar xvf nextsecurity-imagebuilder-22.03.0-x86-64.Linux-x86_64.tar.xz -C builder
cd builder
sed -i '/logd \\/d' include/target.mk
```
Note: OpenWrt build system assumes logd is always installed, but NextSecurity image does not ship it.
The `sed` command ensure logd is not bundled inside the image.

Prepare the files directory:
```
wget https://github.com/NethServer/nextsecurity/archive/refs/heads/master.tar.gz
tar xvf master.tar.gz nextsecurity-master/files/
```

To include custom files, add them inside `nextsecurity-master/files` directory
with the full path, like:
```
echo "hello" > file/root/goofy
```

Start the build with all included packages:
```
source /opt/rh/devtoolset-7/enable
make image  FILES="nextsecurity-master/files/" PACKAGES="$(grep "Package: " packages/Packages | cut -d ':' -f 2 | tr '\n' ' ')"
```
