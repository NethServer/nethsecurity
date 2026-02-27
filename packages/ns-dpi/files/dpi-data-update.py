#!/usr/bin/python3

#
# Copyright (C) 2025 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from urllib3.util import Retry
from requests import Session
from requests.adapters import HTTPAdapter
import os.path
import json
import logging
from os import environ


DATA_SERVER_ENDPOINT = "http://10.0.1.216:8080"
APPLICATIONS_CATEGORIES_ENDPOINT = "/api/netifyd/applications/categories"
APPLICATIONS_CATALOG_ENDPOINT = "/api/netifyd/applications/catalog"
PROTOCOLS_CATEGORIES_ENDPOINT = "/api/netifyd/protocols/categories"
PROTOCOLS_CATALOG_ENDPOINT = "/api/netifyd/protocols/catalog"
DATA_DISK_LOCATION = "/etc/netifyd"
APPLICATIONS_CATEGORIES_NAME = "netify-application-categories.json"
APPLICATIONS_CATALOG_NAME = "netify-application-catalog.json"
PROTOCOLS_CATEGORIES_NAME = "netify-protocol-categories.json"
PROTOCOLS_CATALOG_NAME = "netify-protocol-catalog.json"


def save_data(filename: str, content: str) -> None:
    filepath = os.path.join(DATA_DISK_LOCATION, filename)

    if os.path.exists(filepath):
        logging.debug(f"File {filename} exists, checking if update is needed")
        try:
            with open(filepath, "r") as f:
                if f.read() == content:
                    logging.debug(f"{filename} is up to date, no action needed")
                    return
        except Exception as e:
            logging.warning(f"Failed to read existing {filename}: {e}")

    # save the new data
    try:
        if not os.path.exists(DATA_DISK_LOCATION):
            os.makedirs(DATA_DISK_LOCATION)
        with open(filepath, "w") as f:
            f.write(content)
            logging.info(f"{filename} updated")
    except Exception as e:
        logging.error(f"Failed to write {filename}: {e}")
        raise


def download_data(endpoint: str, filename: str) -> None:
    s = Session()
    retries = Retry(
        total=20, backoff_factor=0.1, status_forcelist=range(500, 600), backoff_max=30
    )
    s.mount(DATA_SERVER_ENDPOINT, HTTPAdapter(max_retries=retries))
    s.headers.update({"Accept": "application/json"})

    try:
        logging.info(f"Downloading from {DATA_SERVER_ENDPOINT}{endpoint}")
        response = s.get(DATA_SERVER_ENDPOINT + endpoint, timeout=5)
        response.raise_for_status()
        content = response.text

        # Validate that content is valid JSON
        json.loads(content)

        save_data(filename, content)
    except Exception as e:
        logging.error(f"Failed to download {filename} from {endpoint}: {e}")
        raise


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(environ.get("LOGLEVEL", "INFO").upper())
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    errors = []

    try:
        download_data(APPLICATIONS_CATEGORIES_ENDPOINT, APPLICATIONS_CATEGORIES_NAME)
    except Exception as e:
        logger.warning(f"Failed to download applications categories: {e}")
        errors.append(str(e))

    try:
        download_data(APPLICATIONS_CATALOG_ENDPOINT, APPLICATIONS_CATALOG_NAME)
    except Exception as e:
        logger.warning(f"Failed to download applications catalog: {e}")
        errors.append(str(e))

    try:
        download_data(PROTOCOLS_CATEGORIES_ENDPOINT, PROTOCOLS_CATEGORIES_NAME)
    except Exception as e:
        logger.warning(f"Failed to download protocols categories: {e}")
        errors.append(str(e))

    try:
        download_data(PROTOCOLS_CATALOG_ENDPOINT, PROTOCOLS_CATALOG_NAME)
    except Exception as e:
        logger.warning(f"Failed to download protocols catalog: {e}")
        errors.append(str(e))

    if errors:
        logger.warning(f"Completed with {len(errors)} error(s)")
