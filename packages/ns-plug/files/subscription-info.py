#!/usr/bin/python3
#
# Copyright (C) 2023 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

#
# Retrieve subscription information, cached in CACHE_FILE.
#
# No flag: print the cached information, checking the remote server first when the
#          cache is missing, expired, for another system or not valid.
# --refresh: check the remote server now, used by cron and register/unregister hooks.
# --wait: check the remote server until it gives an answer, used at boot.
#

import argparse
import fcntl
import json
import os
import sys
import time

import requests
from euci import EUci

CACHE_FILE = "/etc/ns-plug/subscription.json"
ATTEMPT_FILE = "/var/run/subscription-info.json"
LOCK_FILE = "/var/run/subscription-info.lock"
# a valid answer is trusted for this long when the remote server can't be reached
GRACE_PERIOD = 86400
# minimum time between two checks triggered by reading the information
THROTTLE = 30
WAIT_DELAYS = [0, 10, 30, 60, 120, 300, 600, 1200]


def fetch(u, timeout):
    """Ask the remote server, return (state, data) or None when it gives no answer."""
    system_id = u.get("ns-plug", "config", "system_id", default="")
    secret = u.get("ns-plug", "config", "secret", default="")
    try:
        if u.get("ns-plug", "config", "type", default="") == "enterprise":
            url = u.get("ns-plug", "config", "collect_url", default="") + "/info"
            r = requests.get(url, auth=(system_id, secret), headers={"Accept": "application/json"}, timeout=timeout)
        else:
            url = u.get("ns-plug", "config", "api_url", default="").rstrip("/") + "/machine/info"
            r = requests.get(
                url,
                headers={"Accept": "application/json", "Authorization": f"token {secret}"},
                timeout=timeout,
            )
        if r.status_code in (401, 403, 404):
            return "invalid", None
        if r.status_code != 200:
            return None
        response = r.json()
    except (requests.RequestException, ValueError):
        return None

    if u.get("ns-plug", "config", "type", default="") == "enterprise":
        s = response.get("data") or {}
        organization = (s.get("organization") or {}).get("name") or ""
        state = "valid" if s.get("registered") and not s.get("suspended") else "invalid"
        data = {
            "id": s.get("system_key") or "",
            "system_name": s.get("name") or "",
            "organization": organization,
            "subscription": {"valid_until": None, "subscription_plan": {"name": organization or "-"}},
        }
        return state, data

    state = "valid" if (response.get("subscription") or {}).get("status") == "valid" else "invalid"
    return state, response


def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def write_json(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as f:
        json.dump(content, f)
    os.replace(path + ".tmp", path)


def refresh(u, timeout, blocking=True):
    """Check the remote server and update the cache, return True when it gave an answer."""
    with open(LOCK_FILE, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            # another check is running, its result lands in the cache
            return False
        system_id = u.get("ns-plug", "config", "system_id", default="")
        if not system_id:
            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)
            return True
        result = fetch(u, timeout)
        write_json(ATTEMPT_FILE, {"time": int(time.time()), "ok": result is not None})
        if result is None:
            return False
        state, data = result
        # a valid answer is always written, its checked_at extends the grace period
        cache = read_json(CACHE_FILE) or {}
        if (
            state != "valid"
            and cache.get("system_id") == system_id
            and (cache.get("state"), cache.get("data")) == (state, data)
        ):
            return True
        write_json(CACHE_FILE, {"system_id": system_id, "state": state, "checked_at": int(time.time()), "data": data})
        return True


def usable_cache(system_id):
    cache = read_json(CACHE_FILE)
    if not cache or cache.get("system_id") != system_id:
        return None
    if cache.get("state") == "valid" and time.time() - cache.get("checked_at", 0) > GRACE_PERIOD:
        return None
    return cache


def info(u):
    system_id = u.get("ns-plug", "config", "system_id", default="")
    if not system_id:
        return {"uuid": ""}

    cache = usable_cache(system_id)
    if cache is None or cache["state"] != "valid":
        attempt = read_json(ATTEMPT_FILE) or {}
        if time.time() - attempt.get("time", 0) >= THROTTLE:
            refresh(u, 5, blocking=False)
            cache = usable_cache(system_id)

    attempt = read_json(ATTEMPT_FILE) or {}
    ret = {
        "uuid": system_id,
        "id": None,
        "subscription": {"valid_until": None, "subscription_plan": {"name": "-"}},
        "checked_at": 0,
        "stale": not attempt.get("ok", True),
    }
    if cache:
        ret.update(cache.get("data") or {})
        ret["uuid"] = system_id
        ret["checked_at"] = cache["checked_at"]
        ret["subscription"] = ret["subscription"] or {"valid_until": None, "subscription_plan": {"name": "-"}}
    # status is None when the state is unknown
    ret["subscription"]["status"] = cache["state"] if cache else None
    return ret


def main():
    parser = argparse.ArgumentParser(description="Retrieve subscription information")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--refresh", action="store_true", help="check the remote server now")
    group.add_argument("--wait", action="store_true", help="check the remote server until it answers")
    args = parser.parse_args()

    u = EUci()
    if args.refresh:
        sys.exit(0 if refresh(u, 20) else 1)
    if args.wait:
        for delay in WAIT_DELAYS:
            time.sleep(delay)
            if refresh(u, 20):
                sys.exit(0)
        sys.exit(1)
    print(json.dumps(info(u)))


if __name__ == "__main__":
    main()
