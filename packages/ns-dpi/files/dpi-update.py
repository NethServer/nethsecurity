#!/usr/bin/python3

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from urllib3.util import Retry
from requests import Session
from requests.adapters import HTTPAdapter
from euci import EUci
import os.path
import subprocess
import logging
from os import environ


SUBSCRIPTION_SERVER = "https://sp.nethesis.it"
OUT_DIR = "/etc/netifyd"
APPS_FILENAME = "netify-apps.conf"
CATEGORIES_FILENAME = "netify-categories.json"


def get_netifyd_version() -> str:
    try:
        result = subprocess.run(
            ["netifyd", "--version"], capture_output=True, text=True
        )
        for line in (result.stdout + result.stderr).splitlines():
            if "Netify Agent/" in line:
                return line.split("/")[1].split(" ")[0]
    except Exception as e:
        logging.warning(f"Failed to get netifyd version: {e}")
    return ""


def save_file(filename: str, content: str) -> bool:
    filepath = os.path.join(OUT_DIR, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                if f.read() == content:
                    logging.debug(f"{filename} is up to date, no action needed")
                    return False
        except Exception as e:
            logging.warning(f"Failed to read existing {filename}: {e}")
    try:
        if not os.path.exists(OUT_DIR):
            os.makedirs(OUT_DIR)
        with open(filepath, "w") as f:
            f.write(content)
        logging.info(f"{filename} updated")
        return True
    except Exception as e:
        logging.error(f"Failed to write {filename}: {e}")
        raise


def download_file(session: Session, url: str, filename: str) -> bool:
    logging.info(f"Downloading {filename}")
    response = session.get(url, timeout=60)
    response.raise_for_status()
    return save_file(filename, response.text)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(environ.get("LOGLEVEL", "INFO").upper())
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    e_uci = EUci()
    system_id = e_uci.get("ns-plug", "config", "system_id", dtype=str, default="")
    secret = e_uci.get("ns-plug", "config", "secret", dtype=str, default="")
    subscription_type = e_uci.get("ns-plug", "config", "type", dtype=str, default="")

    if not system_id or not secret:
        logger.info("No subscription credentials found, skipping")
        raise SystemExit(0)

    version = get_netifyd_version()
    params = f"settings_version={version}&settings_format=netifyd"
    base_url = f"{SUBSCRIPTION_SERVER}/{subscription_type}"

    s = Session()
    retries = Retry(
        total=20, backoff_factor=0.1, status_forcelist=range(500, 600), backoff_max=30
    )
    s.mount(SUBSCRIPTION_SERVER, HTTPAdapter(max_retries=retries))
    s.auth = (system_id, secret)

    errors = []
    updated = False

    try:
        if download_file(s, f"{base_url}/applications?{params}", APPS_FILENAME):
            updated = True
    except Exception as e:
        logger.warning(f"Failed to download applications: {e}")
        errors.append(str(e))

    try:
        if download_file(s, f"{base_url}/categories?{params}", CATEGORIES_FILENAME):
            updated = True
    except Exception as e:
        logger.warning(f"Failed to download categories: {e}")
        errors.append(str(e))

    if updated:
        logger.debug("Reloading netifyd service")
        subprocess.run(
            ["/etc/init.d/netifyd", "reload"], check=True, capture_output=True
        )

    if errors:
        logger.warning(f"Completed with {len(errors)} error(s)")
