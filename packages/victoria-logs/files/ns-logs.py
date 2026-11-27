#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

"""Read the system logs stored in VictoriaLogs, like less, tail and grep did on /var/log/messages."""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta

from euci import EUci

LEVELS = ["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug"]
UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "y": 31536000}
EXAMPLES = """examples:
  ns-logs                               last 7 days in less
  ns-logs -f                            follow new logs, like tail -f
  ns-logs -n 100 dnsmasq                last 100 lines matching dnsmasq
  ns-logs -i error -v DHCPACK -v ntpd   grep -i error | grep -v DHCPACK | grep -v ntpd
  ns-logs -a banIP -c --per 1d          banIP lines per day in the last week
  ns-logs --boot -1 -p err              errors during the previous boot
  ns-logs --since 2026-10-01 --until "2026-10-02 12:00"
"""


def parse_time(value):
    """Turn "all", a duration (30m, 2h, 7d) or a local date/time ("2026-10-01 10:00") into a UTC datetime."""
    if value == "all":
        return None
    match = re.fullmatch(r"(\d+)([smhdwy])", value)
    if match:
        return datetime.now(UTC) - timedelta(seconds=int(match[1]) * UNITS[match[2]])
    try:
        return datetime.fromisoformat(value).astimezone(UTC)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid time: {value}") from None


def rfc3339(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def vl_time(ts):
    """VictoriaLogs timestamp to datetime, without the fraction."""
    return datetime.fromisoformat(ts[:19] + "+00:00")


def local(dt):
    return f"{dt.astimezone():%Y-%m-%d %H:%M:%S}"


def time_filter(start, end):
    return f"_time:[{rfc3339(start)}, {rfc3339(end)})"


def text_filter(pattern, args):
    """grep-like match on app and message: substring by default, RE2 regex with -E."""
    regex = pattern if args.regex else re.escape(pattern)
    if args.ignore_case:
        regex = "(?i)" + regex
    quoted = json.dumps(regex)
    return f"(~{quoted} or app_name:~{quoted})"


def build_filter(args):
    if args.query:
        return args.query
    parts = []
    if args.app:
        parts.append("app_name:in(" + ",".join(json.dumps(a) for a in args.app) + ")")
    if args.priority:
        parts.append(f"severity:<={LEVELS.index(args.priority)}")
    if args.pattern:
        parts.append(text_filter(args.pattern, args))
    for pattern in args.exclude:
        parts.append("-" + text_filter(pattern, args))
    return " ".join(parts) or "*"


def request(endpoint, params):
    data = urllib.parse.urlencode(params).encode()
    try:
        return urllib.request.urlopen(
            f"http://{ADDRESS}/select/logsql/{endpoint}", data=data
        )
    except urllib.error.HTTPError as e:
        sys.exit(f"ns-logs: {e.read().decode().strip()}")
    except urllib.error.URLError as e:
        sys.exit(f"ns-logs: cannot reach VictoriaLogs at {ADDRESS}: {e.reason}")


def rows(query, **params):
    with request("query", {"query": query, **params}) as resp:
        for line in resp:
            if line.strip():
                yield json.loads(line)


def time_key(row):
    """Sortable _time: VictoriaLogs trims trailing zeros from the fraction, so it's padded back."""
    ts = row.get("_time", "")
    return ts[:19], ts[20:-1].ljust(9, "0")


def format_row(row, args):
    if args.output == "json":
        return json.dumps(row)
    if "app_name" not in row:
        # stream_context separator between chunks, or the result of a -q with stats pipes
        return "--" if row.get("_msg") == "---" else json.dumps(row)
    # same layout as the ns-file rsyslog template used for /var/log/messages
    ts = vl_time(row["_time"]).astimezone()
    pid = row.get("proc_id", "-")
    tag = row.get("app_name", "-") + ("" if pid == "-" else f"[{pid}]")
    return (
        f"{ts:%b %e %H:%M:%S} {row.get('hostname', '-')} {tag}: {row.get('_msg', '')}"
    )


def stats():
    """First log, last log and number of lines, None when there are no logs."""
    for row in rows(
        "* | stats min(_time) as first, max(_time) as last, count() as total"
    ):
        if row["total"] != "0":
            return vl_time(row["first"]), vl_time(row["last"]), row["total"]
    return None


def boots():
    """Start of every boot in the logs, from the kernel banner, plus the current one if it's not logged yet."""
    starts = sorted(
        {
            vl_time(r["_time"])
            for r in rows('app_name:kernel "Linux version" | fields _time')
        }
    )
    with open("/proc/uptime") as f:
        current = datetime.now(UTC) - timedelta(seconds=float(f.read().split()[0]))
    if not starts or starts[-1] < current - timedelta(minutes=1):
        starts.append(current)
    return starts


def boot_range(value):
    """Start and end of a boot: 0 is the current one, -1 the previous one and so on."""
    starts = boots()
    try:
        index = len(starts) - 1 + int(value)
    except ValueError:
        sys.exit(f"ns-logs: invalid boot: {value}")
    if not 0 <= index < len(starts):
        sys.exit(f"ns-logs: no boot {value}, see --boot list")
    return starts[index], starts[index + 1] if index + 1 < len(
        starts
    ) else datetime.now(UTC)


def list_boots():
    starts = boots()
    for i, start in enumerate(starts):
        end = local(starts[i + 1]) if i + 1 < len(starts) else "now"
        print(f"{i - len(starts) + 1:4} {local(start)} - {end}")


def records(args, filters):
    start, end = args.since, args.until
    if args.lines:
        yield from sorted(
            rows(f"{time_filter(start, end)} {filters}", limit=args.lines), key=time_key
        )
    elif args.context:
        yield from rows(
            f"{time_filter(start, end)} {filters} | stream_context before {args.context} after {args.context}"
        )
    else:
        # shortcut: sorting a whole range needs too much memory, so it's sorted one hour at a time
        while start < end:
            chunk_end = min(start + timedelta(hours=1), end)
            yield from rows(
                f"{time_filter(start, chunk_end)} {filters} | sort by (_time)"
            )
            start = chunk_end


def follow(args, filters):
    args.lines = args.lines or 10
    last = ("", "")
    for row in records(args, filters):
        last = time_key(row)
        print(format_row(row, args), flush=True)
    with request("tail", {"query": filters}) as resp:
        for line in resp:
            if line.strip():
                row = json.loads(line)
                # tail starts a few seconds back, skip what was already printed
                if time_key(row) > last:
                    print(format_row(row, args), flush=True)


def count(args, filters):
    if args.per:
        params = {
            "query": filters,
            "start": rfc3339(args.since),
            "end": rfc3339(args.until),
            "step": args.per,
        }
        with request("hits", params) as resp:
            for hits in json.load(resp)["hits"]:
                for ts, value in zip(hits["timestamps"], hits["values"]):
                    print(
                        f"{datetime.fromisoformat(ts).astimezone():%Y-%m-%d %H:%M} {value}"
                    )
    else:
        for row in rows(
            f"{time_filter(args.since, args.until)} {filters} | stats count() as hits"
        ):
            print(row["hits"])


def apps(args, filters):
    params = {
        "query": f"{time_filter(args.since, args.until)} {filters}",
        "field": "app_name",
    }
    with request("field_values", params) as resp:
        for value in sorted(json.load(resp)["values"], key=lambda v: v["value"]):
            print(f"{value['value']} {value['hits']}")


def info():
    summary = stats()
    if not summary:
        print("no logs")
    else:
        print(f"first log:  {local(summary[0])}")
        print(f"last log:   {local(summary[1])}")
        print(f"lines:      {summary[2]}")
    pid = subprocess.run(
        ["pidof", "victoria-logs"], check=False, capture_output=True, text=True
    ).stdout.split()
    if pid:
        with open(f"/proc/{pid[0]}/cmdline") as f:
            flags = dict(
                a.lstrip("-").split("=", 1) for a in f.read().split("\0") if "=" in a
            )
        print(f"retention:  {flags.get('retentionPeriod', '7d')}")
        if "retention.maxDiskSpaceUsageBytes" in flags:
            print(f"max disk:   {flags['retention.maxDiskSpaceUsageBytes']}")
        print(f"storage:    {flags.get('storageDataPath', '-')}")


def show(args, filters):
    out = sys.stdout
    pager = None
    if sys.stdout.isatty():
        pager = subprocess.Popen(["less", "-F"], stdin=subprocess.PIPE, text=True)
        out = pager.stdin
    try:
        for row in records(args, filters):
            out.write(format_row(row, args) + "\n")
        out.close()
    except BrokenPipeError:
        # less was closed early: the unflushed buffer goes to /dev/null instead of failing again at exit
        os.dup2(os.open(os.devnull, os.O_WRONLY), out.fileno())
    if pager:
        pager.wait()


def main():
    parser = argparse.ArgumentParser(
        prog="ns-logs",
        description="Read the system logs, like less, tail and grep on /var/log/messages.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "pattern",
        nargs="?",
        help="show only lines containing PATTERN, in the app name or message",
    )
    parser.add_argument(
        "-E",
        "--regex",
        action="store_true",
        help="patterns are RE2 regular expressions",
    )
    parser.add_argument(
        "-i", "--ignore-case", action="store_true", help="case-insensitive patterns"
    )
    parser.add_argument(
        "-v",
        "--exclude",
        metavar="PATTERN",
        action="append",
        default=[],
        help="hide lines with PATTERN",
    )
    parser.add_argument(
        "-a",
        "--app",
        action="append",
        help="only this app, e.g. dnsmasq, banIP, kernel",
    )
    parser.add_argument(
        "-p", "--priority", choices=LEVELS, help="only this severity and above"
    )
    parser.add_argument(
        "--since",
        type=parse_time,
        default="7d",
        help="start: all, 30m, 2h, 7d or 2026-10-01 10:00",
    )
    parser.add_argument(
        "--until", type=parse_time, help="end, same format as --since (default: now)"
    )
    parser.add_argument(
        "-b",
        "--boot",
        nargs="?",
        const="0",
        metavar="N|list",
        help="this boot, -1 the previous one",
    )
    parser.add_argument(
        "-n", "--lines", type=int, metavar="N", help="only the last N lines"
    )
    parser.add_argument(
        "-f", "--follow", action="store_true", help="keep printing new lines"
    )
    parser.add_argument(
        "-C",
        "--context",
        type=int,
        metavar="N",
        help="N lines of the same app around each match",
    )
    parser.add_argument(
        "-c", "--count", action="store_true", help="print the number of matching lines"
    )
    parser.add_argument(
        "--per", metavar="STEP", help="with -c, count per STEP, e.g. 1h or 1d"
    )
    parser.add_argument(
        "--apps",
        action="store_true",
        help="list the apps that logged, with their line count",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="first and last log, line count and retention",
    )
    parser.add_argument(
        "-o",
        "--output",
        choices=["short", "json"],
        default="short",
        help="output format",
    )
    parser.add_argument(
        "-q", "--query", help="raw LogsQL filter, replaces the pattern options"
    )
    parser.add_argument(
        "--show-query", action="store_true", help="print the LogsQL filter and exit"
    )
    args = parser.parse_args()

    if args.boot == "list":
        return list_boots()
    if args.info:
        return info()
    args.until = args.until or datetime.now(UTC)
    if args.boot:
        args.since, args.until = boot_range(args.boot)
    if args.since is None:
        summary = stats()
        args.since = summary[0] if summary else args.until
    filters = build_filter(args)

    if args.show_query:
        print(filters)
    elif args.follow:
        follow(args, filters)
    elif args.count or args.per:
        count(args, filters)
    elif args.apps:
        apps(args, filters)
    else:
        show(args, filters)


if __name__ == "__main__":
    ADDRESS = EUci().get(
        "victoria-logs", "main", "http_listen_addr", default="127.0.0.1:9428"
    )
    try:
        main()
    except KeyboardInterrupt:
        pass
