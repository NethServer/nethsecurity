# Management tools

This directory contains tools for managing the project.

Tools:

- cleanup: used by `cleanup.yml` to remove old image versions from the CDN
- issue-comment: used by `build-image.yml` to comment on issues when a PR is merged into the main branch
- netifyd-update: refresh the netifyd binaries pinned by the `netifyd` package

## cleanup

The script scans the DigitalOcean Space and removes old image versions.
It keeps the 3 latest version for the dev branch and all the versions for the stable branch.

How to use on a local machine:
```
pip install -r requirements.txt
DO_SPACE_ACCESS_KEY=xxx DO_SPACE_SECRET_KEY=yyy ./cleanup.py
```

## issue-comment

The script comments on issues when a PR is merged into the main branch.
It reports the image version and the link to download it.

How to use on a local machine:
```
export VERSION=23.05.3-ns.0.0.3-rc1-38-g9d146dc
export CDN_NAME=updates.nethsecurity.nethserver.org
export REPO_CHANNEL=dev
export OWRT_VERSION=23.05.3
tools/issue-comment
```

It works only for x86_64 target.

## changelog

Create a changelog in JSON format from a given GitHub project.
It searches all the cards inside the the column that starts with the given name (default is "Done").

Usage example:
```
GITHUB_ORG=nethserver GITHUB_PROJECT=10 GITHUB_TOKEN=xxxxxx COLUMN_NAME=Done ./changelog
```

You can pass the obtained JSON to ChatGPT (or another model) with a prompt like:
```
Create a detailed changelog from the below JSON file.
Split the changes between new features and bug fixes.
Make sure to include all changes.

Use this template for each record:
- This is the title: this is a brief description in one line

Do not use capital letter after column char.
Do not include links to external resources.
```

## openwrt-changes

Generate changelogs about OpenWrt changes between two versions.

Usage example:
```
./openwrt-changes 23.05.3 23.05.4
```

The script will:
- clone all required OpenWrt repositories
- execute [git-cliff](https://git-cliff.org) using podman

Generated changelos are saved in the current directory:
- core-changes.md
- packages-changes.md

## netifyd-update

Refresh the netifyd binaries used by the `netifyd` package.

The script:
- reads the upstream index (`SOURCES` at the top of the script, one entry per architecture)
- downloads the apk of every package listed in `PACKAGES`
- extracts them with `apk extract`
- writes `packages/netifyd/netify-dist.mk` with file name, soname, unversioned link and
  sha256 of each shipped binary, per architecture
- copies the real files (not the symlinks, they are recreated at install time) into
  `tools/netifyd-update/dist/<arch>/`, laid out as the Makefile downloads them

Requirements: `apk-tools` (`dnf install apk-tools` or `apt-get install apk-tools`) and
the Python dependencies in `requirements.txt`.

Usage example:
```
pip install -r requirements.txt
tools/netifyd-update/netifyd-update.py update
```

Use `--force` to remove an existing `work/` and `dist/` from a previous run and redo it.

The `dist/` tree must then be published manually to the netifyd-dist mirror, under
`netifyd-<version>/<dist>/`.
