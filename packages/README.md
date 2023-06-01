# NethServer packages

Add new packages to this directory, packages will be automatically available inside `make menuconfig`.
Make sure to enable it on build time adding the correct configuration file inside `../conf` dir.

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

The package will be availale inside `bin/packages/x86_64/nethsecurity/ns-myapp_<version>_all.ipk`.

For more info, see [upstream guide](https://openwrt.org/docs/guide-developer/packages)
