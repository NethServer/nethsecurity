# NextSecurity

NextSecurity is a downstream rebuild of [OpenWrt](https://openwrt.org/).

Build requirements:

- Linux distribution with Podman 3.x
- 2GB or more of RAM
- at least 40GB of free disk space

The build system is based on a rootless podman container.
Tested on Debian 11 and Fedora 35.

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

## Builder image

The `nethserver/nextsecurity-builder` is a container image to build nextsecurity.
It's based on `debian-slim` and contains a OpenWrt build environment ready to be used.

### How to build it

Additional requirements:

- buildah

Execute:
```
cd builder
./build-builder.sh
```

Publish the image:
```
buildah login ghcr.io
buildah push ghcr.io/nethserver/nextsecurity-builder docker://ghcr.io/nethserver/nextsecurity-builder
```

