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

A new image must be released when:
- a rebase to the new OpenWRT version has been made during development
- a new security fix is available
- a group of relevant features are ready to be released

A new image is released for both the community and subscription repositories.

See [release new image checklist](../build#release-new-image-checklist) for more information.

### Packages

A new package should be released when:
- a new bug fix is available
- a new feature is ready to be released
- a new security fix is available

When releasing a package, remember to:
- ensure that the package has been tested by the QA team
- update the package version in the Makefile
- initiate the release process

Unfortunately, when a new package is created, it is initially placed in the dev channel. Before it can be released, it is necessary to ensure that there
 are no ongoing QA processes and that all packages in the repository are ready for release.
Due to the way the build system works, partial release of a package is not possible.

When ready, merge the tested change to the `stable` branch.
That push will publish the `stable` channel automatically. Packages are always synchronized; image artifacts are uploaded only if the target stable image release does not already exist.

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

Direct object-storage publication is no longer the standard stable release path. If an emergency manual publication is required, build the artifacts using a [local system](../build/#build-locally-for-a-release) and coordinate the repository update separately.

Community repositories are updated by CI on branch push. To update the subscription repositories, the same data must be copied to [parceler]() storage.
Assuming the parceler install is located at `distfeed.nethesis.it` and runs inside a podman container, execute:
```
podman exec -ti parceler-php php artisan repository:sync nethsecurity
```
1. Search for the latest snapshot:
```
podman exec -ti parceler-php php artisan repository:snapshots nethsecurity 
```
Let's assume the latest snapshot is `2024-10-02T08:43:17+02:00`.
2. If you want to push all the packages to all firewall without waiting the tier period, execute:
```
podman exec -ti parceler-php php artisan repository:freeze nethsecurity 2024-10-02T08:43:17+02:00
```
