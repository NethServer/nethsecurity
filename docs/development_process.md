---
layout: default
title: Development process
nav_order: 25
---

# Development process

All NethServer projects follow a shared development process.

See [NethServer development handbook](https://handbook.nethserver.org/) for a detailed guide on how to contribute to NethSecurity.

## Release process

The release process is branch-driven and fully automated by GitHub Actions.

The current branches and their publish targets are:

- `main` publishes rolling development builds to the `dev` channel.
- `staging` publishes tested builds to the `staging` channel.
- `release` publishes the authoritative release stream to the `stable` channel.
- pull requests publish ephemeral channels named `PR<id>` and are removed when the PR closes.

The build workflow loads its base values from [build.conf.defaults](https://github.com/NethServer/nethsecurity/tree/main/build.conf.defaults), then CI fills the channel-specific values from the branch or pull-request context.

### New image

A new image must be released when:
- a rebase to a new OpenWrt version is ready
- a new security fix is available
- a group of relevant features should be promoted together

New images are built and published automatically by CI.

Use `main` for development images, `staging` for pre-release validation, and `release` for the final release image.

### How to bump an image

When you need to bump the image version, update the tracked defaults in [build.conf.defaults](https://github.com/NethServer/nethsecurity/tree/main/build.conf.defaults), especially `NETHSECURITY_VERSION` and `OWRT_VERSION` if the OpenWrt base changed.

Then push the change to the branch that should publish the new image:

- push to `main` for a new rolling development image
- push to `staging` to publish the tested image stream
- push to `release` to publish the final stable image

CI will derive the final image name and repository channel automatically. You do not manually copy image artifacts anymore.

### Draft release from a tag

Tags are Git tags in the NethSecurity repository. They are created on the stable release commit, and on GitHub they are visible under the repository tags list and used as the name of the draft release.

When the stable image is ready, create a tag for the stable commit, then open a GitHub draft release using that tag name.

The draft release should contain:

- the manifest file
- the SBOM file

Do not attach image artifacts to the draft release. The images are already published by CI in the appropriate channel.

After the draft is reviewed, the user edits and publishes the release manually.

Example: release a new image

1. edit the `build.conf.defaults` file and update `NETHSECURITY_VERSION` variable with the new version
    
    a. you can even edit the `BUILD_SEMVER_SUFFIX` variable with `-beta` or `-rc1` to make the builder publish a pre-release 

2. push this commit to `main` to check that the image is built correctly
3. merge or cherry-pick the commit into the `staging` branch, this will publish the image under the staging repository to allow to check them out.
4. iterate this process as many times you need with any changes you want.
5. when ready, remove the suffix and push the changes to `release`, this will publish the image upstream.

### Publish packages

A new package should be released when:
- a new bug fix is available
- a new feature is ready to be released
- a new security fix is available

The package flow follows the same branch-driven model:

- merge the changes to `main` for testing
- push the tested change to `staging` when it is ready for validation
- push the promoted change to `release` when it is ready for the stable channel

*NOTE*: When a new package gets created, it is not pulled automatically by NethSecurity upon release. You must wait for a new image or add the package to the `DEPENDS` section of another package. Make sure to bump the version of the package you are tying the new package to.

The subscription repository, located at `distfeed.nethesis.it`, automatically pulls updates from the stable channel on a nightly basis.
This process ensures that the repository stays current with the latest stable releases.

Update schedule:
1. nightly: new packages are pulled from the stable channel
2. one-week delay: after the initial pull, there is a one-week holding period
3. release: following the holding period, the updated packages are released to subscription machines

This staged approach allows for:
- regular updates to the repository
- a buffer period for additional testing and verification
- controlled distribution to end-users

The one-week delay helps ensure stability by providing time for any potential issues to be identified and addressed before wider distribution.
This delay does not apply to security updates nor new images, which are released immediately.

#### Manually releasing packages

Direct object-storage publication is no longer the standard stable release path. If an emergency manual publication is required, build the artifacts using a [local system](../build/#build-locally-for-a-release) and coordinate the repository update separately.

Community repositories are updated by CI on branch push. To update the subscription repositories, the same data must be copied to enterprise repositories, refer to [parceler manual](https://github.com/nethesis/parceler) on how to do that.
