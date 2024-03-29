---
layout: default
title: License headers
parent: Design
---

# License headers

This is a derivative work of [OpenWrt](https://github.com/openwrt/openwrt/), all the work should be released under
the same license: GPLv2 only.

Code files should contain an header with valid [SPDX](https://spdx.dev/ids/) ID and a copyright statement.

Example for `sh`, `bash`, `python` and `Makefile` files:
```
#
# Copyright (C) {{ 'now' | date: "%Y" }} Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#
```

Extra packages could be released under a different license.
