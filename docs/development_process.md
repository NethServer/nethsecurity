---
layout: default
title: Development process
nav_order: 25
---

# Development process

All NethServer projects follow a shared development process.

See [NethServer development handbook](https://handbook.nethserver.org/) for a detailed guide on how to contribute to NethSecurity.

## Release process

The release process is a set of steps to prepare a new image or a new package release.

### New image

A new image should be released when:
- a new OpenWrt release is available
- a new security fix is available
- a group of relevant features are ready to be released

A new image is released for both the community and subscription repositories.

See [release new image checklist](../build#release-new-image-checklist) for more information.

### Packages

A new package should be released when:
- a new bug fix is available
- a new feature that does not require new software dependencies is available

When releasing a package, remember to:
- ensure that the package has been tested by the QA team
- update the package version in the Makefile
- initiate the release process

Unfortunately, when a new package is created, it is initially placed in the dev channel. Before it can be released, it is necessary to ensure that there
 are no ongoing QA processes and that all packages in the repository are ready for release.
Due to the way the build system works, partial release of a package is not possible.

When ready, launch the [Release stable packages](https://github.com/NethServer/nethsecurity/actions/workflows/release-stable.yml) action on GitHub.
This action will synchronize the packages from the dev channel to the stable channel; images will not be released.

The subscription repository, located at `distfeed.nethesis.it`, automatically pulls updates from the stable channel on a nightly basis.
This process ensures that the repository stays current with the latest stable releases.

Update schedule:
1. nightly: New packages are pulled from the stable channel
2. one-week delay: After the initial pull, there is a one-week holding period
3. release: Following the holding period, the updated packages are released to subscription machines

This staged approach allows for:
- regular updates to the repository
- a buffer period for additional testing and verification
- controlled distribution to end-users

The one-week delay helps ensure stability by providing time for any potential issues to be identified and addressed before wider distribution.
This delay does not apply to security updates nor new images, which are released immediately.

#### Manually releasing packages

To manually release a package, follow these steps, assuming the major version is `23.05.4`:
1. Build the packages using a [local system](../build/#build-locally-for-a-release)
2. Copy the packages to the object storage using rclone, currently hosted on DigitalOcean. Packages must be first published to the `dev` channel:
   ```
   RCLONE_CONFIG_SPACES_TYPE=s3 RCLONE_CONFIG_SPACES_PROVIDER=DigitalOcean RCLONE_CONFIG_SPACES_ENV_AUTH=false RCLONE_CONFIG_SPACES_ACCESS_KEY_ID=xxx RCLONE_CONFIG_SPACES_SECRET_ACCESS_KEY=xxx RCLONE_CONFIG_SPACES_ENDPOINT=ams3.digitaloceanspaces.com RCLONE_CONFIG_SPACES_ACL=public-read rclone sync -M --no-update-modtime -v  --exclude "/targets/**" bin/ "spaces:nethsecurity/dev/23.05.4/"
   ```
3. Move the packages from the `dev` channel to the `stable` channel:
   ```
   RCLONE_CONFIG_SPACES_TYPE=s3 RCLONE_CONFIG_SPACES_PROVIDER=DigitalOcean RCLONE_CONFIG_SPACES_ENV_AUTH=false RCLONE_CONFIG_SPACES_ACCESS_KEY_ID=xxx RCLONE_CONFIG_SPACES_SECRET_ACCESS_KEY=xxx RCLONE_CONFIG_SPACES_ENDPOINT=ams3.digitaloceanspaces.com RCLONE_CONFIG_SPACES_ACL=public-read rclone sync -M --no-update-modtime -v  --exclude "/targets/**" "spaces:nethsecurity/dev/23.05.4/" "spaces:nethsecurity/stable/23.05.4/"
   ```
4. Community repositories are now updated with the new packages. To update the subscription repositories, the same data must be copied to [parceler]() storage.
   Assuming the parceler install is located at `distfeed.nethesis.it` and runs inside a podman container, execute:
   ```
   podman exec -ti parceler-php php artisan repository:sync nethsecurity
   ```
5. Search for the latest snapshot:
   ```
   podman exec -ti parceler-php php artisan repository:snapshots nethsecurity 
   ```
   Let's assume the latest snapshot is `2024-10-02T08:43:17+02:00`.
6. If you want to push all the packages to all firewall without waiting the tier period, execute:
   ```
   podman exec -ti parceler-php php artisan repository:freeze nethsecurity 2024-10-02T08:43:17+02:00
   ```
