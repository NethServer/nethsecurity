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
- If the branch is `staging`, the image will be built and published to the `staging` channel.
- If the branch is `release`, the image will be built and published to the `stable` channel.
- If the build is for a pull request, the image will be published under a branch channel named `PR<id>`.

Artifacts will be created and available for download from the GitHub actions page for 90 days for every build.

### Build targets

By default, the CI will build the `x86_64` target. To build a different target, you need to select an alternate target using the `TARGET` environment variable, refer to [Environment variables](#environment-variables) for more details.

## Build locally

To build locally, it's recommended to populate the `build.conf` file with the options you want to use for the build.
This file is ignored by Git and should not be committed to the repository.
The `build.conf.defaults` file contains the versioned defaults and is always tracked by Git.

You can create a local `build.conf` override that inherits from `build.conf.defaults`:
```bash
cp build.conf.defaults build.conf
# Edit build.conf to override any variables as needed
```

Refer to [Environment variables](#environment-variables) for more details on the available options.

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

The `build-nethsec.sh` script behavior can be changed by setting environment variables or by populating the `build.conf` file (git-ignored, local overrides only).

**Variable loading order:**
1. `build.conf.defaults` (versioned, always loaded first — contains the canonical build defaults tracked in Git)
2. `build.conf` (git-ignored, optional — can override any variable)
3. Environment variables set before calling `./build-nethsec.sh` (highest priority)

**Available variables:**

- `OWRT_VERSION`: specify the OpenWrt version to build, it can be either a TAG or a branch in the [GitHub OpenWRT repo](https://github.com/openwrt/openwrt); **required**
- `NETHSECURITY_VERSION`: specify what to call the NethSecurity image; **required**
- `TARGET`: specify the target to build; if not set default is `x86_64`
- `REPO_CHANNEL`: specify the channel to publish the image to; if not set, the build and CI default to `dev`
- `BUILD_SEMVER_SUFFIX`: optional semver suffix appended to the image version only (not the distfeed URL). Use pre-release format (`-rc.1`, `-beta.2`) or metadata format (`+hotfix.1`, `+testing`) or both (`-rc.1+fix.1`).
- `APK_PUB_KEY` and `APK_PRIV_KEY`: see [package signing section](#package-signing)

The `APK_PUB_KEY`, `APK_PRIV_KEY` variables are always set as secrets inside the CI pipeline, but 
for [security reasons](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#accessing-secrets)
they are not accessible when building pull requests from forks.

### Build locally for a release

If you need to build some packages locally for a release, make sure the following environment variables are set:
- `APK_PUB_KEY` and `APK_PRIV_KEY`: refer to the [package signing section](#package-signing) for more info

Then execute the build as described in the [Build locally](#build-locally) section.

See the [release process](../development_process/#release-process) for the branch-driven publish flow, the image bump workflow, and the tag-based draft release flow.

### Build a snapshot

A snapshot is a build that is based on OpenWrt main branch.

To build a snapshot, just change the `OWRT_VERSION` variable in the `build.conf` file to `main` or `master`.

Then build the image normally using the `build-nethsec.sh` script.

## Versioning

The release version depends on the channel that published it:

- `dev`: rolling development builds with a run number, timestamp, and commit hash
- `staging`: pre-release builds using the base version
- `stable`: final release builds using the base version
- `PR<id>`: ephemeral pull-request builds using the same rolling format as `dev`

For `dev` or PRs:

```
8.8.0-dev.42.20260604123010.a1b2c3d
8.8.0-PR123.17.20260604123010.a1b2c3d
```

For other channels:

```
8.8.0
8.8.0-rc1
9.0.0-beta
```

## Upstream version change

To change the OpenWrt version used by NethSecurity, update the `OWRT_VERSION` variable inside the `build.conf.defaults` file (versioned, always tracked by Git).
This ensures all developers and CI get the same default version.

## Release new image checklist

When releasing a new image, follow these steps:

1. **Update the versioned build defaults**: Bump `NETHSECURITY_VERSION` in [build.conf.defaults](https://github.com/NethServer/nethsecurity/tree/main/build.conf.defaults) if this release needs a new base version.

2. **Merge the release branch**: Push the tested change to `release` so CI publishes the final image and packages automatically.

3. **Create the Git tag:**
  - Create the tag on the stable release commit in the NethSecurity repository.
  - The tag is the human-facing release marker and is visible in the repository tags list on GitHub.

4. **Draft the GitHub release:**
  - Use the tag as the release name.
  - Attach the manifest file and the SBOM file.
  - Do not attach image artifacts.

5. **Finalize the release notes:**
  - Update the changelog with the date of release and relevant changes inside the [administrator manual](https://github.com/NethServer/nethsecurity-docs).
  - Merge any pending documentation PRs and rebuild the docs if needed.

6. **Complete the rest of the release tasks:**
  - Close related issues and milestones.
  - Archive completed project-board items.
  - Release NethSecurity Controller if applicable.
  - Publish the user-facing announcement once the release draft is approved.


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

Packages are signed using an EC prime256v1 key pair (PEM format) via the APK package manager.

To generate a new signing key pair:
```
openssl ecparam -name prime256v1 -genkey -noout -out private-key.pem
openssl ec -in private-key.pem -pubout -out public-key.pem
```

To sign the packages, execute the `build-nethsec.sh` script with the following environment variables:
- `APK_PUB_KEY`
- `APK_PRIV_KEY`

Usage example:
```
APK_PUB_KEY=$(cat public-key.pem) APK_PRIV_KEY=$(cat private-key.pem) ./build-nethsec.sh
```

Or you can place the keys as two files named `private-key.pem` and `public-key.pem` in the root of the repository. They will be automatically used by the build script.

If no keys are provided, OpenWrt will auto-generate a throwaway key pair at build time.

Builds executed inside CI will sign the packages with the correct key.

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
