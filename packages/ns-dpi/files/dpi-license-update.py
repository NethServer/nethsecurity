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


# FIXME: use proper server address
LICENSE_SERVER_ENDPOINT = "http://192.168.100.1:8080"
LICENSE_FREE_ENDPOINT = "/api/netifyd/licence"
LICENSE_COMMUNITY_ENDPOINT = "/api/netifyd/community/licence"
LICENSE_ENTERPRISE_ENDPOINT = "/api/netifyd/enterprise/licence"
LICENSE_DISK_LOCATION = "/etc/netifyd"
LICENSE_NAME = "license.json"
LICENSE_DEFAULT_LOCATION = LICENSE_DISK_LOCATION + "/" + LICENSE_NAME


def __license_location() -> str:
    e_uci = EUci()
    storage_location = e_uci.get("fstab", "ns_data", "target", default=None, dtype=str)
    if storage_location is None:
        location = LICENSE_DEFAULT_LOCATION
    else:
        location = storage_location + "/" + LICENSE_NAME

    return location


def save_license(content: str) -> None:
    location = __license_location()
    logging.debug(f"Storage location: {location}")
    if os.path.exists(location):
        logging.debug("File exists, checking if update is needed")
        with open(location, "r") as f:
            if f.read() == content:
                logging.debug("License is up to date, no action needed")
                return

    # if the location is symlink, remove it first
    if os.path.islink(location):
        logging.warning("Location is a symlink, removing it first")
        os.remove(location)
    # save the new license
    license_updated = False
    with open(location, "w") as f:
        f.write(content)
        logging.info("License updated")
        license_updated = True

    # If we saved in the storage location, symlink to the default location
    if location != LICENSE_DEFAULT_LOCATION:
        if os.path.exists(LICENSE_DEFAULT_LOCATION):
            os.remove(LICENSE_DEFAULT_LOCATION)
        os.symlink(location, LICENSE_DEFAULT_LOCATION)

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


def is_license_valid() -> bool:
    try:
        with open(__license_location(), "r") as f:
            json_status = json.load(f)
            issued_to = json_status.get("issued_to", "")
            e_uci = EUci()
            subscription = e_uci.get(
                "ns-plug", "config", "type", dtype=str, default=None
            )
            if subscription is not None and "Enterprise" not in issued_to:
                logging.warning(
                    f"License type mismatch: expected Enterprise, got {issued_to}"
                )
                return False
            elif "Community" not in issued_to:
                logging.warning(
                    f"License type mismatch: expected Community, got {issued_to}"
                )
                return False

            expire_at = json_status.get("expire_at", {})
            unix_expiration = expire_at.get("unix", 0)
            current_time = int(time.time())
            if unix_expiration > current_time:
                logging.debug(f"License valid until {time.ctime(unix_expiration)}")
                return True
            else:
                logging.warning("License expired, refresh triggered")
                return False
    except FileNotFoundError:
        logging.warning("License missing, refresh triggered")
        return False


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(environ.get("LOGLEVEL", "INFO").upper())
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    if is_license_valid():
        exit(0)

    try:
        upstream_license = download_license()
        save_license(upstream_license)
    except Exception as e:
        logger.warning(f"Failed to download license: {e}")
