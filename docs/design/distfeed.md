---
layout: default
title: Package repositories
parent: Design
---

# Package repositories

* TOC
{:toc}

## Channels

The distribution feed includes the following channels:

- `dev` channel: this channel is intended for unstable and development releases.
- `staging` channel: this channel contains pre-release builds and packages that passed QA and can be tested by end users.
- `stable` channel: this channel is for stable releases.
- `subscription` channel: this channel is reserved for stable releases that have undergone additional testing. Access to this channel is restricted to machines with a valid subscription.

## Repositories

Official package repositories are hosted at [{{site.download_url}}]({{site.download_url}}/index.html).

Each release in the distribution feed is associated with a fixed repository. The fixed repository contains the image
released and the packages. The repository will receive updates compatible with the same release.

### Examples

Here are some examples of releases and their corresponding repositories:

1. Dev example: `8.8.0-dev.42.20260604123010.a1b2c3d` and its repository is available at `{{site.download_url}}/dev/8.8.0-dev.42.20260604123010.a1b2c3d`

2. Staging example: `8.8.0` and its repository is available at `{{site.download_url}}/staging/8.8.0`

3. Stable example: `8.8.0` and its repository is available at `{{site.download_url}}/stable/8.8.0`

4. Branch example: `8.8.0-PR123.17.20260604123010.a1b2c3d` and its repository is available at `{{site.download_url}}/PR123/8.8.0-PR123.17.20260604123010.a1b2c3d`

### APK repository configuration

Repositories are now configured using apk variables instead of the usual rewrite of the feeds. This allows greater customization and standardization.

The `/etc/apk/repositories.d/distfeeds.list` contains a standard entry:

```
https://${endpoint}/${version}/targets/${target_arch}/packages/packages.adb
https://${endpoint}/${version}/packages/${package_arch}/base/packages.adb
https://${endpoint}/${version}/packages/${package_arch}/luci/packages.adb
https://${endpoint}/${version}/packages/${package_arch}/nethsecurity/packages.adb
https://${endpoint}/${version}/packages/${package_arch}/packages/packages.adb
```

Since all scripts inside `/etc/apk/repositories.d/*list` are executed by alphabetical order, we can define the following:

- `/etc/apk/repositories.d/99-defaults.list` this file should contain the defaults that are applied only if the variables are not set. It uses the `set -default` option for apk repositories that allows to set the variables if uset.

- `/etc/apk/repositories.d/01-enterprise.list` is created only when there's a valid subscription, this overwrites the `endpoint` variable with the correct path and authentication.

The script `distfeed-setup` is in charge of making and managing the main `distfeed.list` file and `01-enterprise.list` if needed.

#### Customization options

It's possible by nature of apk repositories override the variables added by adding the `/etc/apk/repositories.d/98-overrides.list`. This allows to overwrite previously set variables as the user sees fit.

The repository variables are generated in `/etc/apk/repositories.d/99-defaults.list`.
They include `target_arch`, `package_arch`, `repo_channel`, `version`, and the default `endpoint`.
If you need to override one of these values, create `/etc/apk/repositories.d/98-overrides.list` and write the variables there.

If you want to change the base URL, add the variable override you need in `98-overrides.list`, `apk` will then handle by itself the replacement.

This changes for image updates, to recieve the correct popup you need to update the `ns-plug.config.repository_url` variable and the `/etc/repo-channel`, this will reflect even into `apk` unless a override has been set. This can be done as the following:

```bash
echo "<channel>" > /etc/repo-channel
uci set ns-plug.config.repository_url="https://updates.nethsecurity.nethserver.org/$(cat /etc/repo-channel)"
uci commit ns-plug
distfeed-setup
```
You can now refresh the update page, and the new repository channel will be used.

### Force updates on a subscription machine

A machine with a valid subscription receives updates from the subscription channel.
The subscription channel contains stable releases that have undergone additional testing.
Updates are pushed to the subscription channel after one week from the release date.

If you have a machine with a valid subscription and want to force an update, you can do the following:

```bash
echo 'set repo_channel=staging' > /etc/apk/repositories.d/98-overrides.list
echo 'set endpoint=updates.nethsecurity.nethserver.org/${repo_channel}' >> /etc/apk/repositories.d/98-overrides.list
apk update
apk upgrade
```

You can replace the `repo_channel` with the following options:
- `stable` packages released beforehand to community
- `staging` packages yet to be released, but already been tested internally

At the end, you can move the file for later use.
```
mv /etc/apk/repositories.d/98-overrides.list /etc/apk/repositories.d/98-overrides.list.staging
apk update
```

## Upstream OpenWrt repositories

You can add custom feeds by adding the repos the `/etc/apk/repositories.d/customfeeds.list` file.

To enable OpenWrt package repositories use the following commands
```bash
cat << 'EOF' > /etc/apk/repositories.d/customfeeds.list
https://downloads.openwrt.org/releases/${openwrt_version}/targets/${target_arch}/packages/packages.adb
https://downloads.openwrt.org/releases/${openwrt_version}/packages/${package_arch}/base/packages.adb
https://downloads.openwrt.org/releases/${openwrt_version}/packages/${package_arch}/luci/packages.adb
https://downloads.openwrt.org/releases/${openwrt_version}/packages/${package_arch}/packages/packages.adb
https://downloads.openwrt.org/releases/${openwrt_version}/packages/${package_arch}/routing/packages.adb
EOF
```
