---
layout: default
title: Build
nav_order: 20
---

# Build images

* TOC
{:toc}

NethSecurity uses [OpenWrt](https://openwrt.org/) build system.

Automatic builds run inside [GitHub actions](https://github.com/NethServer/nethsecurity/actions)
on every pull request (PR), git push and git merge.

To build the images locally on you machine, make sure these requirements are met:

- Linux distribution with Podman 3.x
- 2GB or more of RAM
- at least 40GB of free disk space

The build system is based on a rootless [podman](https://podman.io/) container.
Tested on Debian 11 and Fedora 35/36.

## Usage

Clone the repository, then to start the build just execute:
```
./run
```

The script will create a `bin` directory inside the current working directory.
At the end, the `bin` directory will contain the output of the build.
If a previous `bin` directory already exists, it will be renamed to `bin.bak`.
If a previous `bin.bak` directory already exists, it will be removed.

To speed up next builds, the script will also create `staging_dir` and `build_dir` directories as cache.
To avoid cache creation, pass the `--no-cache` option: `./run --no-cache`.

If you need a shell inside the build container, execute:
```
./run bash
```

During the start-up, the container will:

- generate the diffconfig
- generate a random public key to sign packages

### Environment variables

The `run` script behavior can be changed using the following environment variables:

- `IMAGE_TAG`: specify the image tag of the builder, if not set default is `latest`
- `USIGN_PUB_KEY` and `USIGN_PRIV_KEY`: see [package signing section](#package-signing)
   with the given keys
- `NETIFYD_ACCESS_TOKEN`: GitLab private access token; if set, download and compile netifyd closed
   source plugins

The `USIGN_PUB_KEY`, `USIGN_PRIV_KEY` and `NETIFYD_ACCESS_TOKEN` variables are always set as secrets
inside the CI pipeline, but for [security reasons](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#accessing-secrets)
they are not accessible when building pull requests.

### Using an alternate builder

If you need to use a modified version of the builder image, edit the files inside the `builder` 
directory.
Then build the image and use it with the `run` script:
```
./builder/build-builder
declare IMAGE_TAG="mybranch"
TAG=$(podman images --quiet ghcr.io/nethserver/nethsecurity-builder:latest)
podman tag $TAG ghcr.io/nethserver/nethsecurity-builder:$IMAGE_TAG
./run
```

## Versioning


The versioning system encompasses three types of versions:

- **Stable:** Stable versions, finalized and ready for production use. 
- **Unstable:** Versions under active development, intended for testing and continuous development.
- **Development:** Versions in active development, with additional commit details, used for debugging and internal testing.


The generic format for a version is as follows:

```
<owrt_release>-ns.<nethsecurity_release>-<commit_since_last_tag>-g<commit_hash>
```

- `<owrt_release>`: Main version number of OpenWRT.
- `<nethsecurity_release>`: NethSecurity security version in [semver](https://semver.org/) format.
- `<commit_since_last_tag>`: Number of commits since the last version tag, present only in development versions.
- `g<commit_hash>`: Unique identifier for the current commit, prsent only in development versions.


Stable version example:
```
8-20.05-ns.1.2.0
```

Unstable version example
```
8-20.05-ns.0.1.0-alpha1
```

Development version example:
```
8-20.05-ns.0.0.1-224-g26d3f78
```

## Upstream version change

Create a tag that contains the new OpenWrt release followed by a NethSecurity unstable release.

Example:
```
git tag 23.05.2-ns.0.0.1-alpha1
```

Prepare a new Luci branch with NethSecurity customizations named after OpenWrt major and minor release:
```
git remote add openwrt https://github.com/openwrt/luci.git
git fetch openwrt
git checkout -b openwrt-23.05 openwrt/openwrt-23.05
git push origin openwrt-23.05
git checkout -b nethsec-23.05
```

Now cherry-pick the commits from old branch (like `nethserc-22.03`)
Then, push the changes:
```
git push origin nethsec-23.05
```

Finally, push the tags to start the build process:
```
git push --tags
```

When the builder of the image has been completed, make sure to:
- wipe podman volumes  otherwise the build will fail:
  ```
  podman volume rm nethsecurity-build_dir nethsecurity-staging_dir
  ```
- rebuild the image using latest builder container image
- rebuild the documentation to update the download link: https://readthedocs.org/projects/nethsecurity-docs/

## Image configuration

All files with `.conf` extension inside the `config` directory will be merged to create the diffconfig.
The `.conf` files must respect the syntax of OpenWrt `.config` file.

Best practices:

- create a `.conf` file for each image customization
- add comments to the conf file to explain why an option has been set

See [config diff file](https://openwrt.org/docs/guide-developer/toolchain/use-buildsystem#configure_using_config_diff_file) for more info.

## Custom files

All files from `files` directory will be copied inside the final image.

To setup a UCI default, just put a file inside `files/etc/uci-defaults`.

See [UCI  defaults](https://openwrt.org/docs/guide-developer/uci-defaults) for more info.

## Custom packages

All new packages can be added inside the `packages` directory.

See [packages doc](../packages/).

## Package patches

Some packages do not have sources that can be patched using [quilt](https://openwrt.org/docs/guide-developer/toolchain/use-patches-with-buildsystem).
To patch an existing package put a patch inside `patches` directory, reflecting the structure of `feeds` directory.

The patch can be created following these steps:

- run the build system in interactive mode
- enter the package directory to edit
- generate a patch and copy it outside the container

First, enter the build system by executing `./run bash`, then enter the directory package to edit. Example:
```
cd /home/build/openwrt/feeds/packages/net/adblock
```

Edit the files, then generate the patch using `git`:
```
cd /home/build/openwrt
mkdir -p patches/feeds/packages
git -C feeds/packages diff > patches/feeds/packages/100-adblock-bypass.patch
```

Finally, copy the patch outside the container and run the build.

Note: before submitting a patch using this method, please try to open a pull request to the upstream repository!

## Override upstream packages

It is possible to replace upstream packages with local ones.
This is useful when you want to use a more recent version then the one already
released by OpenWrt.

To replace an upstream package just create a new package with the same
name inside the `packages` directory.

## LuCI web interface fork

Some configurations should not be changed from LuCI to avoid problems on the underlaying system.
This is the reason why, during the build, a fork of LuCI will be used.
The fork is hosted at the following [repository](https://github.com/NethServer/luci).

{% assign vparts = site.version | split:'.' %}
Please make changes only to the `nethsec-{{ vparts | slice: 0,2 | join:'.' }}` branch.

LuCI fork is updated on every build run.
The original GIT commit used during the build can be found with whis command:
```
opkg info luci | grep Version | cut -d'-' -f3
```

## Package signing

All packages are signed with the following public key generated with [OpenBSD signify](nethsecurity-pub.key).

Public key fingerprint: `7640d16662de3b89`

Public key content:
```
untrusted comment: NethSecurity sign key
RWR2QNFmYt47ieK7g/zEPwgk+MN8bHsA2vFnPThSpnLZ48L7sh6wxB/f
```

To sign the packages, just execute the `run` script with the following environment variables:
- `USIGN_PUB_KEY`
- `USIGN_PRIV_KEY`

Usage example:
```
USIGN_PUB_KEY=$(cat nethsecurity-pub.key) USIGN_PRIV_KEY=$(cat nethsecurity-priv.key) ./run
```

If the above environment variables are not set, the build system will generate a local temporary signing key.
Builds executed inside CI will sign the packages with correct key.


## Builder image

The `nethserver/nethsecurity-builder` is a container image to build nethsecurity.
It's based on `debian-slim` and contains a OpenWrt build environment ready to be used.

### How to build it

Additional requirements:

- buildah

Execute:
```
cd builder
./build-builder
```

Publish the image:
```
buildah login ghcr.io
buildah push ghcr.io/nethserver/nethsecurity-builder docker://ghcr.io/nethserver/nethsecurity-builder
```

## Netifyd plugins

NethSecurity uses two [netifyd](https://gitlab.com/netify.ai/public/netify-agent) proprietary plugins from [Netify](https://www.netify.ai/):

- Netify Flow Actions Plugin (netify-flow-actions)
- Netify Agent Stats Plugin (netify-plugin-stats)

The plugins should be used with the latest netifyd stable version (4.2.2 at the time of writing).
To create the files for the build, follow the steps below. Such steps should be needed only after a netifyd/plugin version change.

Both plugins source code is hosted on a private repository at [GitLab](https://gitlab.com).
To access it, you must set `_PERSONAL_ACCESS_TOKEN_` from GitLab.
During build time, if `_PERSONAL_ACCESS_TOKEN_` is not set, the final image
will not contain any of these plugins.

Prepare the environment:
```
sudo apt install -y  libcurl4-openssl-dev libmnl-dev libnetfilter-conntrack-dev libpcap-dev zlib1g-dev pkg-config bison flex uuid-runtime libnftables-dev
git clone --recursive https://gitlab.com/netify.ai/public/netify-agent.git
```

Setup netifyd version:
```
export NETIFY_ROOT=$(pwd)/netify-root
cd netify-agent
git checkout v4.2.2 -b latest
./autogen.sh && ./configure --prefix=/usr --libdir=/usr/lib
make DESTDIR=${NETIFY_ROOT} -j $(nproc) install
cd ..
```

Setup netify-flow-actions plugin:
```
git clone https://oauth2:_PERSONAL_ACCESS_TOKEN_@gitlab.com/netify.ai/private/nethesis/netify-flow-actions.git
cd netify-flow-actions
export PKG_CONFIG_PATH=${NETIFY_ROOT}/usr/lib/x86_64-linux-gnu/pkgconfig:${NETIFY_ROOT}/usr/lib/pkgconfig:/usr/lib/pkgconfig
 export CPPFLAGS=$(pkg-config --define-variable=includedir=${NETIFYD_PREFIX}/usr/include --define-variable=libdir=${NETIFYD_PREFIX}/usr/lib libnetifyd --cflags)
export LDFLAGS=$(pkg-config --define-variable=includedir=${NETIFYD_PREFIX}/usr/include --define-variable=libdir=${NETIFYD_PREFIX}/usr/lib libnetifyd --libs-only-L)
./autogen.sh && ./configure --prefix=/usr --libdir=/usr/lib
unset PKG_CONFIG_PATH
unset CPPFLAGS
unset LDFLAGS
cd ..
```

Setup netify-plugin-stats plugin:
```
git clone https://oauth2:_PERSONAL_ACCESS_TOKEN_@gitlab.com/netify.ai/private/nethesis/netify-agent-stats-plugin.git
cd netify-agent-stats-plugin
export PKG_CONFIG_PATH=${NETIFY_ROOT}/usr/lib/x86_64-linux-gnu/pkgconfig:${NETIFY_ROOT}/usr/lib/pkgconfig:/usr/lib/pkgconfig
 export CPPFLAGS=$(pkg-config --define-variable=includedir=${NETIFYD_PREFIX}/usr/include --define-variable=libdir=${NETIFYD_PREFIX}/usr/lib libnetifyd --cflags)
export LDFLAGS=$(pkg-config --define-variable=includedir=${NETIFYD_PREFIX}/usr/include --define-variable=libdir=${NETIFYD_PREFIX}/usr/lib libnetifyd --libs-only-L)
./autogen.sh && ./configure --prefix=/usr --libdir=/usr/lib
unset PKG_CONFIG_PATH
unset CPPFLAGS
unset LDFLAGS
cd ..
```

Copy files to the package directories:
```
mkdir -vp packages/net/netifyd/files
cp netify-agent/deploy/openwrt/Makefile packages/net/netifyd/
shopt -s extglob
cp netify-agent/deploy/openwrt/files/!(*.in) packages/net/netifyd/files/

mkdir -p nspackages/netify-flow-actions/
cp netify-flow-actions/deploy/openwrt/Makefile nspackages/netify-flow-actions/
cp netify-flow-actions/deploy/openwrt/Config.in nspackages/netify-flow-actions/

mkdir -p nspackages/netify-plugin-stats/files
cp netify-agent-stats-plugin/deploy/openwrt/Makefile nspackages/netify-plugin-stats/
cp netify-agent-stats-plugin/deploy/netify-plugin-stats.json nspackages/netify-plugin-stats/files/
```

Setup Makefile to use a local copy of private repositories:
```
sed -i 's/PKG_SOURCE_URL.*$/PKG_SOURCE_URL:=file:\/\/\/home\/build\/openwrt\/netify-flow-actions/' nspackages/netify-flow-actions/Makefile
sed -i 's/PKG_SOURCE_URL.*$/PKG_SOURCE_URL:=file:\/\/\/home\/build\/openwrt\/netify-agent-stats-plugin/' nspackages/netify-plugin-stats/Makefile
```

To manually build the stack, use:
```
make -j $(nproc) package/feeds/packages/netifyd/{download,compile} V=sc
make -j $(nproc) package/feeds/nethsecurity/netify-plugin-stats/{download,compile} V=sc
make -j $(nproc) package/feeds/nethsecurity/netify-flow-actions/{download,compile} V=sc
```
