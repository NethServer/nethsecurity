#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

#
# Send the IPs blocked by the banip log service to the Nethesis Insights server.
#
# Events are spooled by /usr/libexec/ts-insights-hook (banip ban_blockhook) and
# pushed here in batches by cron. The unit is identified with the ns-plug
# subscription credentials; without them the script is a no-op.
#

import base64
import ipaddress
import json
import os
import shutil
import ssl
import syslog
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from euci import EUci

SPOOL_DIR = "/var/run/ns-insights"
SPOOL = os.path.join(SPOOL_DIR, "threat-events.jsonl")
SENDING = SPOOL + ".sending"
STATUS = os.path.join(SPOOL_DIR, "last_push.json")

DEFAULT_URL = "https://insights.nethesis.it"
MAX_DECISIONS_PER_REQUEST = 500
MAX_SPOOLED_EVENTS = 5000
MAX_EVENT_AGE = timedelta(hours=2)
TIMEOUT = 20


def log(priority, message):
    syslog.syslog(priority, message)


def read_config(uci):
    """Return (base_url, system_id, secret, verify_tls) or None if the unit is not registered."""
    system_id = uci.get("ns-plug", "config", "system_id", default="")
    secret = uci.get("ns-plug", "config", "secret", default="")
    if not system_id or not secret:
        return None

    base_url = uci.get("ns-plug", "config", "insights_url", default=DEFAULT_URL).rstrip(
        "/"
    )
    verify_tls = uci.get("ns-plug", "config", "tls_verify", default="1") != "0"

    return base_url, system_id, secret, verify_tls


def claim_spool():
    """Move the spool file aside so the hook can keep appending, then return its lines."""
    if os.path.exists(SPOOL):
        if os.path.exists(SENDING):
            # leftover from a previous failed run: keep the oldest events first
            with open(SENDING, "a") as dst, open(SPOOL) as src:
                shutil.copyfileobj(src, dst)
            os.unlink(SPOOL)
        else:
            os.rename(SPOOL, SENDING)

    if not os.path.exists(SENDING):
        return []

    with open(SENDING) as spool:
        return spool.readlines()


def is_reportable(value):
    """Only public unicast addresses leave the firewall: never report local traffic."""
    try:
        return ipaddress.ip_address(value).is_global
    except ValueError:
        return False


def parse_events(lines):
    """Validate the spooled lines, returning (decisions, discarded_count)."""
    decisions = []
    discarded = 0
    oldest = datetime.now(timezone.utc) - MAX_EVENT_AGE

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            decision = json.loads(line)
            value = decision["value"]
            created_at = datetime.strptime(
                decision["created_at"], "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)
        except (ValueError, KeyError, TypeError):
            discarded += 1
            continue

        # the server promotes an IP only if it has been reported recently, stale events are useless
        if not is_reportable(value) or created_at < oldest:
            discarded += 1
            continue

        decisions.append(decision)

    if len(decisions) > MAX_SPOOLED_EVENTS:
        discarded += len(decisions) - MAX_SPOOLED_EVENTS
        decisions = decisions[-MAX_SPOOLED_EVENTS:]

    return decisions, discarded


def requeue(decisions):
    """Put the decisions which have not been sent back into the spool."""
    if not decisions:
        if os.path.exists(SENDING):
            os.unlink(SENDING)
        return

    with open(SENDING, "w") as spool:
        for decision in decisions:
            spool.write(json.dumps(decision) + "\n")


def send_batch(config, decisions):
    """Post a batch of decisions, returning the server counters."""
    base_url, system_id, secret, verify_tls = config
    payload = json.dumps(
        {"schema_version": 1, "system_id": system_id, "decisions": decisions}
    ).encode()
    credentials = base64.b64encode(f"{system_id}:{secret}".encode()).decode()
    request = urllib.request.Request(
        f"{base_url}/v1/threat-events",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {credentials}",
        },
    )
    context = None if verify_tls else ssl._create_unverified_context()

    with urllib.request.urlopen(request, timeout=TIMEOUT, context=context) as response:
        return json.loads(response.read())


def write_status(status):
    status["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(STATUS, "w") as status_file:
        json.dump(status, status_file)


def main():
    syslog.openlog("ts-insights-report")

    uci = EUci()
    config = read_config(uci)
    if config is None:
        return

    os.makedirs(SPOOL_DIR, exist_ok=True)
    decisions, discarded = parse_events(claim_spool())
    if discarded:
        log(
            syslog.LOG_INFO,
            f"discarded {discarded} invalid, stale or non-public events",
        )
    if not decisions:
        requeue([])
        return

    sent = stored = duplicates = 0
    for index in range(0, len(decisions), MAX_DECISIONS_PER_REQUEST):
        batch = decisions[index : index + MAX_DECISIONS_PER_REQUEST]
        try:
            counters = send_batch(config, batch)
        except (urllib.error.URLError, OSError, ValueError) as error:
            # keep the events for the next run, the server deduplicates redeliveries
            requeue(decisions[index:])
            log(
                syslog.LOG_WARNING,
                f"push of {len(decisions) - index} events failed: {error}",
            )
            write_status(
                {
                    "success": False,
                    "sent": sent,
                    "stored": stored,
                    "duplicates": duplicates,
                    "error": str(error),
                }
            )
            return

        sent += len(batch)
        stored += counters.get("stored", 0)
        duplicates += counters.get("duplicates", 0)

    requeue([])
    log(
        syslog.LOG_INFO,
        f"pushed {sent} events (stored: {stored}, duplicates: {duplicates})",
    )
    write_status(
        {
            "success": True,
            "sent": sent,
            "stored": stored,
            "duplicates": duplicates,
            "error": None,
        }
    )


if __name__ == "__main__":
    main()
