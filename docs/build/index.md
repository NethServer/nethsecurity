---
layout: default
title: Build system
has_children: true
nav_order: 20
---

# Build system

* TOC
{:toc}


---

NethSecurity runs the [OpenWrt](https://openwrt.org/) build system inside a rootless [podman](https://podman.io/) container.
This allows to build the images in a reproducible and isolated environment.
The container image is named [builder](#builder-image).

## Automatic builds (GitHub CI)

Automatic builds run inside [GitHub actions](https://github.com/NethServer/nethsecurity/actions)
on every pull request (PR), git push and git merge.
The build runs inside a [GitHub self-hosted runner](#self-hosted-runner).

The GitHub actions also take care of publishing images and packages to the repository. The current logic is the following:

- If the branch is `main`, the image will be built and published to the `dev` [channel](/design/distfeed/#channels).
- If the branch is `main` and the tag is a stable version, the image will be built and published to the `stable` channel.
- If the branch is other than `main`, the image will published under a dev branch that has the name of the branch as the name of the release.

Artifacts will be created and available for download from the GitHub actions page for 90 days for every build.

### Build targets

By default, the CI will build the `x86_64` target. To build a different target, you need to select an alternate target using the `TARGET` environment variable, refer to [Environment variables](#environment-variables) for more details.

## Build locally

To build locally, it's recommended to populate the `build.conf` file with the options you want to use for the build.
This file is ignored by Git and should not be committed to the repository.
You can use the `build.conf.example` file as a starting point. Refer to [Environment variables](#environment-variables) for more details on the available options.

To build images locally on your machine, make sure these minimum requirements are met:

- Linux distribution with Podman 4.x
- 2GB or more of RAM
- at least 40GB of free disk space
- 4 or more CPU cores

Clone the repository, then to start the build just execute:
```
./build-nethsec.sh
```

The script will create a `bin` and `build-logs` directories inside the repository. The `bin` directory will contain the built images and packages, while the `build-logs` directory will contain the build logs.
Directory `build-logs` will be created even if the build fails, so you can check the logs to understand what went wrong.

If you need a shell inside the build container, execute:
```
./build-nethsec.sh bash
```

During the start-up, the container will download netifyd plugins if configuration is set to do so.

### Environment variables

The `build-nethsec.sh` script behavior can be changed by giving the following environment variables or setting them inside the `build.conf` file:

- `OWRT_VERSION`: specify the OpenWrt version to build, it can be either a TAG or a branch in the [GitHub OpenWRT repo](https://github.com/openwrt/openwrt); **required**
- `NETHSECURITY_VERSION`: specify what to call the NethSecurity image; **required**
- `TARGET`: specify the target to build; if not set default is `x86_64`
- `REPO_CHANNEL`: specify the channel to publish the image to; if not set default is `dev`
- `NETIFYD_ENABLED`: configure if netifyd plugins should be downloaded and compiled; if not set, default is `0` (disabled)
- `NETIFYD_ACCESS_TOKEN`: token to download the netifyd plugins; if not set, default is empty, required if `NETIFYD_ENABLED` is set to `1`
- `USIGN_PUB_KEY` and `USIGN_PRIV_KEY`: see [package signing section](#package-signing)
   with the given keys

The `USIGN_PUB_KEY`, `USIGN_PRIV_KEY` and `NETIFYD_ACCESS_TOKEN` variables are always set as secrets
inside the CI pipeline, but for [security reasons](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#accessing-secrets)
they are not accessible when building pull requests from forks.

### Build locally for a release

If you need to build some packages locally for a release, make sure the following environment variables are set:
- `USIGN_PUB_KEY` and `USIGN_PRIV_KEY`: refer to the [package signing section](#package-signing) for more info
- `NETIFYD_ENABLED` and `NETIFYD_ACCESS_TOKEN`: required to download and compile netifyd closed source plugins

Then execute the build as described in the [Build locally](#build-locally) section.

See the [manual release process](../development_process/#manually-releasing-packages) for additional info.

### Build a snapshot

A snapshot is a build that is based on OpenWrt main branch.

To build a snapshot, just change the `OWRT_VERSION` variable in the `build.conf` file to `main` or `master`.

Then build the image normally using the `build-nethsec.sh` script.

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
- `g<commit_hash>`: Unique identifier for the current commit, present only in development versions.


Stable version example:
```
8.6.0
```

Unstable version example
```
8.6.0-beta.1
```

Development version example:
```
8.6.0-feature-branch-name-26d3f78
```

## Upstream version change

To change the OpenWrt version used by NethSecurity, you can just replace the `OWRT_VERSION` variable inside the `build.conf.example` file with the new OpenWrt version.

## Release new image checklist

When releasing a new image, follow these steps:

1. **Tag the stable release:**
  - Example: `8.5.2`

2. **Update the changelog:**
  - Include the date of release and relevant changes inside the [administrator manual](https://github.com/NethServer/nethsecurity-docs).

3. **Merge all documentation PRs:**
  - Ensure all pending documentation pull requests are merged.

4. **Execute documentation build:**
  - Execute the build of the documentation on [Read the Docs](https://readthedocs.org/projects/nethsecurity-docs/) to include latest changes
    and update the downaload links.

5. **Close all open issues:**
  - Ensure all issues related to the release are closed.

6. **Close the milestone:**
  - Close the relevant milestone on [GitHub](https://github.com/NethServer/nethsecurity/milestones).

7. **Archive completed items:**
  - Archive all items in the "Done" column of the [project board](https://github.com/orgs/NethServer/projects/10/views/2).

8. **Release NethSecurity Controller:**
  - Release the version of NethSecurity Controller on NethServer 8, if applicable.

9. **Release the milestone inside the subscription repository:**
  - Access distfeed.nethesis.it and release the [milestone](https://github.com/nethesis/parceler?tab=readme-ov-file#milestone-release):
    the image with its own packages will be available also in the subscription repository.

10. **Announce the release:**
  - Post English announcement on [NethServer Community](https://community.nethserver.org).
  - Post Italian announcement on [Nethesis Partner Portal](https://partner.nethesis.it).


## Image configuration

### OpenWrt configuration

Configuration is handled by generating a diffconfig file that contains the differences from the default OpenWrt configuration. This is the recommended way to customize the OpenWrt build system.
The file than gets enriched with the NethSecurity specific configuration and target specific configuration.
Then `make defconfig` is executed to generate the final `.config` file used by OpenWrt build system.

Additional configuration can be found in the official [OpenWrt documentation](https://openwrt.org/docs/guide-developer/toolchain/use-buildsystem#configure_using_config_diff_file).

To edit the config file, you can use the `make menuconfig` command inside the build container. Simply execute:
```
./build-nethsec.sh make menuconfig
```

Then, once saved the configuration, you can generate the diffconfig file by executing:
```
./scripts/diffconfig.sh > .diffconfig
```

To see what changed in the configuration, you can use:
```
diff -u .diffconfig config/.diffconfig
```

### Target configuration

Target configuration is defined inside the `targets` directory under the `config` directory.
Each target is a configuration named after the target architecture, like `x86_64.conf`.

During the build process, the target will be selected using the `TARGET` environment variable. See [Environment variables](#environment-variables) for more details.
To add a new target, just create a new `.conf` file inside the `targets` directory with `<target_name>.conf` name.

### Custom files

All files from the `files` directory will be copied inside the final image.

To setup a UCI default, just put a file inside `files/etc/uci-defaults`.

See [UCI  defaults](https://openwrt.org/docs/guide-developer/uci-defaults) for more info.

### Custom packages

All new packages can be added inside the `packages` directory.

See [packages doc](../packages/).

### Package patches

Some packages do not have sources that can be patched using [quilt](https://openwrt.org/docs/guide-developer/toolchain/use-patches-with-buildsystem).
To patch an existing package put a patch inside the `patches` directory, reflecting the structure of the `feeds` directory.

The patch can be created following these steps:

- run the build system in interactive mode
- enter the package directory to edit
- generate a patch and copy it outside the container

First, enter the build system by executing `./build-nethsec.sh bash`, then enter the directory package to edit. Example:
```
cd /home/buildbot/openwrt/feeds/packages/net/adblock
```

Edit the files, then generate the patch using `git`:
```
cd /home/buildbot/openwrt
mkdir -p patches/feeds/packages
git -C feeds/packages diff > patches/feeds/packages/100-adblock-bypass.patch
```

Finally, copy the patch outside the container and run the build.

Note: before submitting a patch using this method, please try to open a pull request to the upstream repository!

### Override upstream packages

It is possible to replace upstream packages with local ones.
This is useful when you want to use a more recent version than the one already released by OpenWrt.

To replace an upstream package just create a new package with the same name inside the `packages` directory.

### Package signing

All packages are signed with the following public key generated with [OpenBSD signify](nethsecurity-pub.key).

Public key fingerprint: `7640d16662de3b89`

Public key content:
```
untrusted comment: NethSecurity sign key
RWR2QNFmYt47ieK7g/zEPwgk+MN8bHsA2vFnPThSpnLZ48L7sh6wxB/f
```

To sign the packages, just execute the `build-nethsec.sh` script with the following environment variables:
- `USIGN_PUB_KEY`
- `USIGN_PRIV_KEY`

Usage example:
```
USIGN_PUB_KEY=$(cat nethsecurity-pub.key) USIGN_PRIV_KEY=$(cat nethsecurity-priv.key) ./build-nethsec.sh
```

Or you can have the keys as two files named `key-build` and `key-build.pub` in the root of the repository. They will be automatically used by the build script.

Builds executed inside CI will sign the packages with the correct key.

### Netifyd plugins

NethSecurity uses two [netifyd](https://gitlab.com/netify.ai/public/netify-agent) proprietary plugins from [Netify](https://www.netify.ai/):

- Netify Flow Actions Plugin (netify-flow-actions)
- Netify Agent Stats Plugin (netify-plugin-stats)

The plugins should be used with the latest netifyd stable version (4.4.3 at the time of writing).
To create the files for the build, follow the steps below. Such steps should be needed only after a netifyd/plugin version change.

Both plugins source code is hosted on a private repository at [GitLab](https://gitlab.com).
To access it, you must set `NETIFYD_ENABLED=1` and provide a personal access token with read access to the private repositories. And then `NETIFYD_ACCESS_TOKEN` environment variable must be set to the token value.


## Self-hosted runner

The build system uses a GitHub-hosted runner to build the images.

Before proceeding, make sure that your hosted runner is fast enough to build the images.
The runner should have:
- 8GB or more of RAM
- a fast NVME disk
- at least 100GB of free disk space
- 8 or more CPU cores
- a fast internet connection

To setup a self-hosted runner, follow the [official documentation](https://docs.github.com/en/actions/hosting-your-own-runners/adding-self-hosted-runners).
To setup a self-hosted runner on Ubuntu 23.10, follow the steps below.

First, create the user `runner1` and install podman and git. Then, create the systemd service:
```
apt-get install podman git -y
useradd runner1 -s /bin/bash -m
loginctl enable-linger runner1
cat <<EOF > /etc/systemd/system/runner1.service
[Unit]
Description=GitHub Actions runner1
After=network.target

[Service]
ExecStart=/home/runner1/actions-runner/run.sh
User=runner1
WorkingDirectory=/home/runner1/actions-runner
KillMode=process
KillSignal=SIGTERM
TimeoutStopSec=5min

[Install]
WantedBy=multi-user.target
EOF
```

Then, login as `runner1` and follow the [instructions](https://github.com/NethServer/nethsecurity/settings/actions/runners/new) to download
and register the runner.
   
Finally, as root, enable and start the service:
```
systemctl enable --now runner1
```

The build_dir directory also keeps old versions, which speeds up the builds but quickly fills up the machine's disk.
On a fast machine, cleaning the build_dir reduces the execution time from around 7-10 minutes to 20-22 minutes.

Since OpenWrt documentation suggests performing a "make clean" occasionally, and to avoid filling up the disk, a cron job is set up to clean the build_dir weekly:
```
echo 'runuser  -s /usr/bin/env -l runner1 podman volume rm nethsecurity-build_dir' > /etc/cron.weekly/nethsec-cleanup.sh
chmod a+x /etc/cron.weekly/nethsec-cleanup.sh
```
