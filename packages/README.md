# Packages

The NethSecurity build system is based on OpenWrt, which uses the concept of packages to manage software components.
NethSecurity includes two different sets of packages: NethSecurity packages and OpenWrt packages.

## NethSecurity packages

NethSecurity packages are added to a special `nspackages` feed, which is included in the image
at every build. This feed is used to include custom packages that are not part of the OpenWrt.

To add a new package, just create a new directory inside the `packages` directory.
All packages inside this directory will be automatically available inside `make menuconfig`.
Make sure to enable it on build time adding the correct configuration file inside `conf` dir.

Conventions:
- the name of the package should always start with `ns-` prefix. Example: `ns-myapp`
- set the `CATEGORY` to `NethSecurity` and `SECTION` to `base`, the package will show up under `NethSecurity` section
  when executing `make menuconfig`

When creating a new package which includes all the code, do *not* set `PKG_SOURCE_URL` and `PKG_SOURCE` variables.

Example:
```
PKG_NAME:=ns-myapp
PKG_VERSION:=0.0.1
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/ns-myapp-$(PKG_VERSION)
include $(INCLUDE_DIR)/package.mk

define Package/ns-myapp
	SECTION:=base
	CATEGORY:=NethSecurity
	TITLE:=My mighty myapp
	URL:=<app_url>
	DEPENDS:=+firstdepend
	PKGARCH:=all
endef
```

To compile only the package, launch the shell inside the container then use:
```
make package/feeds/nethsecurity/ns-myapp/{download,compile} V=sc
```

Or, using a one-liner:
```
./run bash -- -c "make package/feeds/nethsecurity/ns-myapp/{download,compile} V=sc"
```

The package will be available inside `bin/packages/x86_64/nethsecurity/ns-myapp_<version>_all.ipk`.

For more info, see [upstream guide](https://openwrt.org/docs/guide-developer/packages)

## OpenWrt packages

OpenWrt packages are included in the NethSecurity image only when creating the image builder.
The image builder is container used to create the final NethSecurity image.

There is a [packages repository](https://github.com/openwrt/packages/) inside GitHub that contains all the packages.
Please note that the branches inside this repository, like `openwrt-23.05` are not the ones used by the build system.

The version of the packages repository used in the build is the one indicated in the `feeds.conf.default` file.
You can find it by running `./run bash`.

Example of the content of `feeds.conf.default`:
```
src-git packages https://git.openwrt.org/feed/packages.git^b5ed85f6e94aa08de1433272dc007550f4a28201
src-git luci https://git.openwrt.org/project/luci.git^63ba3cba5b7bfb803a875d4d8f01248634687fd5
src-git routing https://git.openwrt.org/feed/routing.git^e351d1e623e9ef2ab78f28cb1ce8d271d28c902d
src-link nethsecurity /home/build/openwrt/nspackages
```

This file indicates that the `packages` repository is used at commit `b5ed85f6e94aa08de1433272dc007550f4a28201`.
Since the image builder is created only once per release, the packages are not updated at every build,
but only when a new release is created.

Every build produces a Packages.manifest file that contains the list of all the packages included in the image.
Note that a manifest can change between builds, even if the packages are not updated.
This means that builds are not reproducible, but it is not a problem if the version of the packages does not change.
