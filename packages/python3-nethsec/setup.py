#!/usr/bin/env python

import os

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = 'nethsec',
    # Set by the OpenWrt Makefile (PKG_VERSION); falls back for local/dev builds.
    version = os.environ.get('NETHSEC_PKG_VERSION', '0.0.0'),
    author = 'Giacomo Sanchietti',
    author_email = 'giacomo.sanchietti@nethesis.it',
    description = 'Utilities for NethSecurity development',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/NethServer/python3-nethsec",
    license = "GPLv3",
    package_dir = {'': 'src'},
    packages = ['nethsec', 'nethsec.utils', 'nethsec.firewall', 'nethsec.mwan', 'nethsec.dpi', 'nethsec.ipsec', 'nethsec.ovpn', 'nethsec.users', 'nethsec.reverse_proxy', 'nethsec.inventory', 'nethsec.conntrack', 'nethsec.ldif', 'nethsec.objects', 'nethsec.snort'],
    requires = [ "pyuci" ],
    classifiers = [
        "Programming Language :: Python :: 3",
        "License v3 (LGPLv3)   License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires = '>=3.13',
)
