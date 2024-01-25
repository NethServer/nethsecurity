---
layout: default
title: Package repositories
nav_order: 30
---

# Package repositories

* TOC
{:toc}

## Channels

The distribution feed includes the following channels:

- `dev` channel: this channel is intended for unstable and development releases.
- `stable` channel: this channel is for stable releases.
- `subscription` channel: this channel is reserved for stable releases that have undergone additional testing. Access to this channel is restricted to machines with a valid subscription.

## Repositories

Official package repositories are hosted at [{{site.download_url}}]({{site.download_url}}/index.html).

Each release in the distribution feed is associated with two repositories:

1. Fixed Repository:
    - Contains packages and images from the build.
    - This repository remains unchanged and is not used by the running images.

2. Rolling Repository:
    - Used by the running images.
    - Contains all updates compatible within the same major OpenWRT release.

### Examples

Here are some examples of releases and their corresponding repositories:

1. Dev example: `23.05.2-ns.0.0.1-217-g8786a2b`
    - Fixed repository: `{{site.download_url}}/dev/23.05.2-ns.0.0.1-217-g8786a2b`
    - Rolling repository: `{{site.download_url}}/dev/23.05.2`

2. Stable example: `23.05.2-ns.0.0.1`
    - Fixed repository: `{{site.download_url}}/stable/23.05.2-ns.0.0.1`
    - Rolling repository: `{{site.download_url}}/stable/23.05.2`

3. Unstable example: `23.05.2-ns.0.0.1-alpha1`
    - Fixed repository: `{{site.download_url}}/dev/23.05.2-ns.0.0.1-alpha1`
    - Rolling repository: `{{site.download_url}}/dev/23.05.2`

### Change repository channel

The `distfeed-setup` script simplifies the automatic setup of the repository channel, tailored to the version of the running image. 

Execute the script without any additional arguments to automatically configure the repository channel based on the version of the running image.
The script is automatically executed when a subscription is enabled or disabled.

### Customization options

The behavior of the distfeed-setup script can be customized using the following environment variables:

- `BASE_URL`: set the base URL for repositories. If not specified, the default value is taken from {{site.download}}.
- `CHANNEL`: define the desired channel for the repository. Possible values include stable, dev, and subscription.
   By default, the script attempts to extract this information from the `/etc/os-release` file.
- `OWRT_VERSION`: specify the OpenWrt version used inside the rolling repository URL.
   The script typically extracts this information from the `/etc/os-release` file.

Custom configuration example:
```
BASE_URL="https://custom-repo-url.com" CHANNEL="dev" OWRT_VERSION="21.02.3" distfeed-setup
```

## Upstream OpenWrt repositories

You can add custom feeds by changing the `/etc/opkg/customfeeds.conf` file.

To enable OpenWrt package repositories use the following commands
```bash
source /etc/os-release
VERSION=$(echo $VERSION | cut -d- -f2)
cat << EOF > /etc/opkg/customfeeds.conf 
src/gz core https://downloads.openwrt.org/releases/$VERSION/targets/x86/64/packages
src/gz base https://downloads.openwrt.org/releases/$VERSION/packages/x86_64/base
src/gz luci https://downloads.openwrt.org/releases/$VERSION/packages/x86_64/luci
src/gz packages https://downloads.openwrt.org/releases/$VERSION/packages/x86_64/packages
src/gz routing https://downloads.openwrt.org/releases/$VERSION/packages/x86_64/routing
EOF
```
