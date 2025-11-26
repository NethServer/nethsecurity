#!/usr/bin/python3

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from urllib3.util import Retry
from requests import Session
from requests.adapters import HTTPAdapter
from euci import EUci
import os.path
import subprocess
import json
import logging
import time
from os import environ


LICENSE_SERVER_ENDPOINT = "https://distfeed.nethesis.it"
LICENSE_FREE_ENDPOINT = "/api/netifyd/license"
LICENSE_COMMUNITY_ENDPOINT = "/api/netifyd/community/license"
LICENSE_ENTERPRISE_ENDPOINT = "/api/netifyd/enterprise/license"
LICENSE_DISK_LOCATION = "/etc/netifyd"
LICENSE_NAME = "license.json"
LICENSE_DEFAULT_LOCATION = LICENSE_DISK_LOCATION + "/" + LICENSE_NAME


def save_license(content: str) -> None:
    if os.path.exists(LICENSE_DEFAULT_LOCATION):
        logging.debug("File exists, checking if update is needed")
        with open(LICENSE_DEFAULT_LOCATION, "r") as f:
            if f.read() == content:
                logging.debug("License is up to date, no action needed")
                return

    # save the new license
    license_updated = False
    if not os.path.exists(LICENSE_DISK_LOCATION):
        os.makedirs(LICENSE_DISK_LOCATION)
    with open(LICENSE_DEFAULT_LOCATION, "w") as f:
        f.write(content)
        logging.info("License updated")
        license_updated = True

    if license_updated:
        logging.debug("Reloading netifyd service")
        subprocess.run(
            ["/etc/init.d/netifyd", "reload"], check=True, capture_output=True
        )


def download_license() -> str:
    s = Session()
    retries = Retry(
        total=20, backoff_factor=0.1, status_forcelist=range(500, 600), backoff_max=30
    )
    s.mount(LICENSE_SERVER_ENDPOINT, HTTPAdapter(max_retries=retries))
    s.headers.update({"Accept": "application/json"})
    path = LICENSE_FREE_ENDPOINT
    e_uci = EUci()
    subscription = e_uci.get("ns-plug", "config", "type", dtype=str, default=None)
    if subscription is not None:
        s.auth = (
            e_uci.get("ns-plug", "config", "system_id", dtype=str, default=""),
            e_uci.get("ns-plug", "config", "secret", dtype=str, default=""),
        )
        if subscription == "community":
            path = LICENSE_COMMUNITY_ENDPOINT
        elif subscription == "enterprise":
            path = LICENSE_ENTERPRISE_ENDPOINT

    response = s.get(LICENSE_SERVER_ENDPOINT + path, timeout=5)
    response.raise_for_status()
    return response.text


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(environ.get("LOGLEVEL", "INFO").upper())
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    try:
        upstream_license = download_license()
        save_license(upstream_license)
    except Exception as e:
        logger.warning(f"Failed to download license: {e}")
