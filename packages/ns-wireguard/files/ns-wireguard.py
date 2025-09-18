#!/usr/bin/python3

import subprocess

from euci import EUci

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#


def __main__():
    e_uci = EUci()
    for item in e_uci.get('network'):
        if e_uci.get('network', item, 'proto', dtype=str, default='') == 'wireguard':
            print(f"restarting interface {item}")
            subprocess.run(
                f"ifdown {item} && ifup {item}",
                shell=True,
                check=True,
                capture_output=True,
            )


if __name__ == "__main__":
    __main__()
