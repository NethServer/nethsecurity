---
layout: default
title: Development process
nav_order: 25
---

# Development process

* TOC
{:toc}

## Issues

An issue is a formal description of a known problem, or desired
feature, inside a tracker. There are two kind of issues:

- **Bug**: 
  describes a defect of the software; it must lead to a
  resolution of the problem. For example, a process crashing under certain
  conditions.

- **Feature/Enhancement**:
  describes an improvement of the current code or an entirely new
  feature. For example, remove a harmless warning of a running process or
  designing a new UI panel.

Bugs and enhancements will always produce some code changes inside one or more
Git repositories.

### Do I need to open a new issue?

Yes, if what you’re talking about will produce some code.
By the way, it’s perfectly reasonable not to fill issues for
occasional small fixes, like typos in translations.

When implementing small fixes, always avoid commits to the main branch.
Open a [pull request](#pull-requests) and carefully describe the problem.
Creation of issues can be avoided only for trivial fixes which require
no QA effort.

Issues are not a to-do list. Issues track the status changes of a job, the
output of the job will be a new package or image resolving the issue itself.
If you are exploring some esoteric paths for new feature or hunting
something like a [heisenbug](http://en.wikipedia.org/wiki/Heisenbug>),
please open a discussion with your thoughts.
Then create a new issue only when you’re ready to write a formal description
and produce some output object.

A process for a new feature should be something like this:

- open a new topic on [http://community.nethserver.org](http://community.nethserver.org) and discuss it

- if a feature is planned for the future it is also recorded in a [project
  draft card](https://github.com/orgs/NethServer/projects/10)

- ongoing development can be tracked inside a [draft pull request](#draft-pull-requests)

- once the work on the feature starts, open the issue on GitHub
  [https://github.com/NethServer/nethsecurity/issues/new](https://github.com/NethServer/nethsecurity/issues/new)


### Writing issues

How to write a bug report:

* Apply the **bug** label
* Point to the right software component with the associated version
* Describe the error, and how to reproduce it
* Describe the expected behavior
* If possible, suggest a fix or workaround
* If possible, add a piece of system output (log, command, etc)
* Text presentation matters: it makes the whole report more readable
  and understandable

How to write a feature or enhancement:

* Everybody should understand what you’re talking about: describe the
  feature with simple words using examples
* If possible, add links to external documentation
* Text presentation and images matter: they make the whole report more readable
  and understandable

Also remember to attach labels to the issue, to help the team to categorize it.

More information:

* [Mozilla bug writing guidelines](https://bugzilla.mozilla.org/page.cgi?id=bug-writing.html)
* [Fedora howto file a bug](https://docs.fedoraproject.org/en-US/quick-docs/howto-file-a-bug/)


### Issue priority

Bugs should always have priority over features.

The priority of a bug depends on:

* security: if it's a security bug, it should have maximum priority
* number of affected users: more affected users means more priority


### Issue tracker

The NethServer project is hosted on GitHub and is constituted by many Git
repositories.  We set one of them to be the issue tracker:

[https://github.com/NethServer/nethsecurity](https://github.com/NethServer/nethsecurity)

Issues created on it help coordinating the development process, determining
who is in charge of what.

Issues recorded in the tracker are a fundamental source of information for
future changes and a reference for documentation and support requests.

Issues recorded as project draft cards constitute the project roadmap and
are published here:

[https://github.com/orgs/NethServer/projects/10](https://github.com/orgs/NethServer/projects/10)

### Issue labels and tags

Issues can be tagged using a set of well-known labels that indicate the status:

- `bug`: a defect of the software
- `testing`: packages are available from testing repositories (see [QA section](#qa-team-member-testing))
- `verified`: all test cases were verified successfully (see [QA section](#qa-team-member-testing)
- `invalid`: invalid issue, not a bug, duplicate or wontfix. Add a detailed description and link
  to other related issue when using this tag.

Other labels can be used to categorize the issue:

- `feature`: a new feature or an enhancement
- `firewall`: a bug or feature related to the firewall
- `controller`: a bug or feature related to the controller
- `docs`: a bug or feature related to the documentation

Before introducing new labels, please discuss them with the development team
and make sure to describe carefully the new label inside the [label page](https://github.com/NethServer/nethsecurity/labels).

An issue should be associated to a [Milestone](https://github.com/NethServer/nethsecurity/milestones?with_issues=no) when it is planned to be released.
It's a good practice to associate the issue to the `NethSecurity 8` project to track the progress of the issue.

An issue inside the `NethSecurity 8` project could also have one or more extra fields:
- `Implementation`: it can be `Frontend`, `Backend` or `Frontend/Backend` to indicate the area of the code that will be affected by the issue
- `Iteration`: it indicates the iteration of the issue, the iteration is a sequence of steps to reach the final goal. The iteration usually has start and end dates
- `Mockup`: it can be empty if no mockup is needed, or `Ready` if the mockup is ready, or `Not ready` if the mockup is not ready yet. If an issue is marked
   as `Not ready` the developer should wait for the mockup to be ready before starting the implementation

### Process the issue

After an issue is filed in the tracker, it goes through the hands of teammates who assume various roles. While the same person may take on multiple roles simultaneously, we prefer to distribute responsibilities as much as possible.

#### Developer

The *Developer*.

- Sets *Assignee* to himself.

- Sets the *Project* to `NethSecurity 8`

- Bundle the commits as one or more GitHub [pull requests](#pull-request)

- For *enhancements*, writes the test case (for *bugs* the procedure to
  reproduce the problem should be already set).

- Writes and updates the [documentation](#documentation) associated with the code.

If the issue is not valid, it must be closed using the **invalid** label.
A comment must convey the reason why it is invalid, like *"duplicate of (URL of issue), wontfix because ..."*.


#### QA team member (testing)

The *QA team member*.

* Takes an issue with label **testing** and adds themselves to the *Assignee*
  field

* Tests the package, following the test case documentation written by the
  *Developer*.

* Tests the documentation changes, if present

* When test finishes they remove the **testing** label.  If the test is
  *successful*, they set the **verified** label, otherwise they alert the
  *Developer* and the *Packager* to plan a new process iteration.


#### Packager

The *Packager* coordinates the *Developer* and *QA member* work.  After the
*Developer* opens one or more pull requests:

* Selects issues with open pull requests

* Reviews the pull request code and merges it
  The CI will build and upload a new image

After the *QA member* has completed the testing phase:

* Takes an issue with label **verified**

* Update the involved package and bump the release inside the Makefile

* Merges the documentation changes in the `nethserver/nethsecurity-docs` repo

* Closes the issue, specifying the list of released packages or image

When the package is CLOSED, all related [documentation](#documentation) must be in place.

At any time of the issue lifecycle they ensure that there are no release
conflict with other issues.

## Pull requests

A Pull Request (PR) is the main method of submitting code contributions to NethSecurity.

You can find an overview of the whole workflow [here](https://guides.github.com/introduction/flow/).

### Submitting a pull request

When submitting a PR, check that:

1. PR is submitted against the main branch (for current stable release)

2. PR title contains a brief explanation of the feature, fix or enhancement

3. PR comment contains a link to the related issue, in the form ``NethServer/nethsecurity#<number>``, eg: NethServer/nethsecurity#1122

4. PR comment describes the changes and how the feature is supposed to work

5. Multiple dependent PRs in multiple repositories must include the dependencies between them in the description

6. Select at least one PR reviewer (GitHub suggestions are a usually good)

7. Select yourself as the initial PR assignee


### Managing an open pull request

After submitting a PR, before it is merged:

1. If enabled, automated build process must pass
   
   - If the build fails, check the error and try to narrow down the reason
   - If the failure is due to an infrastructure problem, please contact a developer who will help you

2. Another developer must review the pull request to make sure it:

   - Works as expected
   - Doesn't break existing stuff
   - The code is reasonably readable by others developers
   - The commit history is clean and adheres to [commit message rules](#commit-message-rules)

3. The PR must be approved by a developer with commit access to NethServer on GitHub:

   - Any comment raised by a developer has been addressed before the pull request is ready to merge


### Merging a pull request

When merging a PR, make sure to copy the issue reference inside the merge commit comment body, for future reference.

If the commit history is not clear enough, or you want to easily revert the whole work, it's acceptable
to squash before merge. Please make sure the issue reference is present inside the comment of the squashed commit.

Also, avoid adding the issue references directly inside non-merge commit messages to have a clean GitHub reference graph.

Example of a good merge commit:
```
  commit xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  Merge: xxxxxxx yyyyyyy
  Author: Mighty Developer <mighty.developer@netheserver.org>
  Date:   Thu Dec 14 17:12:19 2017 +0100

      Merge pull request #87 from OtherDev/branchXY

      Add new excellent feature 

      NethServer/nethsecurity#1122
```
Example of a merged PR with squash:
```
  commit xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  Author: Mighty Developer <mighty.developer@netheserver.org>
  Date:   Thu Dec 14 17:12:19 2017 +0100

    Another feature (#89)

    NethServer/nethsecurity#1133
```


### Draft pull requests

The use of draft pull requests is recommended to share an on-going development.
Draft pull requests can be used to test possible implementations of features that do not have an issue yet.
If the draft pull request does not reference an issue it must have an assignee.


## Package version numbering rules

NethSecurity packages follow OpenWrt conventions.

OpenWrt roughly follows the [semantic versioning](https://semver.org/) rules, but with some differences:
- do not use pre-release version numbers
- do not use metadata version numbers

NethSecuirty image versioning is documented [here](../build/#versioning).

## Commit message style guide

Individual commits should contain a cohesive set of changes to the code. These
[seven rules](http://chris.beams.io/posts/git-commit/#seven-rules) summarize how a good commit message should be composed.

Please follow OpenWrt [submission guidelines](https://openwrt.org/submitting-patches#submission_guidelines).

## Documentation

The developer must take care to write all documentation on:

* [Developer Manual](https://github.com/NethServer/nethsecurity/tree/main/docs), if the feature is developer-facing
* [Administrator Manual](https://github.com/NethServer/nethsecurity-docs), if the feature is user-facing
