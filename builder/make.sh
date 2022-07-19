#!/bin/sh

#
# Copyright (C) 2022 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Start parallel build
make -j $(nproc) V=sc world
