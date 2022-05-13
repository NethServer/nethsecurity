# NethServer packages

Add new packages to this directory, packages will be automatically available inside `make menuconfig`.
Make sure to enable it on build time adding the correct configuration file inside `../conf` dir.

Conventions:
- the name of the package should always start with `ns-` prefix. Example: `ns-myapp`
- set the `CATEGORY` to `NextSecurity` and `SECTION` to `base`, the package will show up under `NextSecurity` section
  when executing `make menuconfig`

When creating a new package which includes all the code, do *not* set `PKG_SOURCE_URL` and `PKG_SOURCE` variables.

Example:
```
PKG_NAME:=ns-myapp
PKG_VERSION:=0.0.1
PKG_RELEASE:=$(AUTORELEASE)

PKG_BUILD_DIR:=$(BUILD_DIR)/ns-myapp-$(PKG_VERSION)
include $(INCLUDE_DIR)/package.mk

define Package/ns-myapp
	SECTION:=base
	CATEGORY:=NextSecurity
	TITLE:=My mighty myapp
	URL:=<app_url>
	DEPENDS:=+firstdepend
	PKGARCH:=all
endef
```

For more info, see [upstream guide](https://openwrt.org/docs/guide-developer/packages)
