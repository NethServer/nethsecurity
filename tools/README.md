# Management tools

This directory contains tools for managing the project.

Tools:

- cleanup: used by `cleanup.yml` to remove old image versions from the CDN
- issue-comment: used by `build-image.yml` to comment on issues when a PR is merged into the main branch
- package-bumper: used by `build-image.yml`, it searches for ns-* packages that need to be bumped

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


## package-bumper

When new commits are pushed to the main branch, it's usually necessary to bump the ns-* packages versions.
Bumped packages can then be installed directly from the repository.

The script searches only for ns-* packages that it bumps the version and creates a commit for each package.
Finally it pushes the commits and creates a PR.