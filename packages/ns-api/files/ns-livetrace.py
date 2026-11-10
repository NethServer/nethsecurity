#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Trace new connections and DNS queries of one client, write results to STATE.
# Usage: ns-livetrace <ip> <duration> [port] [protocol]

import glob
import ipaddress
import json
import os
import queue
import re
import signal
import subprocess
import sys
import threading
import time

import requests
from euci import EUci

STATE = "/var/run/ns-livetrace.json"
PID = "/var/run/ns-livetrace.pid"
TABLE = "ns_livetrace"
MAX_ITEMS = 200
MAX_FLOWS = 1000
LAYERS = {
    "fw4": "firewall",
    "banIP": "threat_shield_ip",
    "netifyd": "dpi",
    "snort": "ips",
    "adblock": "dns_filter",
    "ns-binding": "mac_binding",
}
# chains that only execute the verdict decided by the rule jumping into them
REJECT_CHAINS = ("handle_reject", "_reject")
PRIVATE_NETS = [
    ipaddress.ip_network(n)
    for n in (
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "100.64.0.0/10",
        "fc00::/7",
    )
]
# fw4 zone chains reached by zone policies, forwardings and user rules
ZONE_VERDICT_RE = re.compile(r"(accept|drop|reject)_(to|from)_")

TRACE_RE = re.compile(r"^trace id (\S+) \S+ (\S+) (\S+) (.*)$")
VERDICT_RE = re.compile(r"\(verdict (\w+)[^)]*\)$")
COMMENT_RE = re.compile(r'comment "!fw4: (.*)"')
QUERY_RE = re.compile(r": (\d+)\S* (?:\[\S+\] )*(\w+)\? (\S+) ")
REPLY_RE = re.compile(r": (\d+)\S* (?:([A-Z][A-Za-z]+)\S* )?(?:\[\S+\] )*\d+/\d+/\d+")


def nft(script, check=False):
    subprocess.run(
        ["nft", "-f", "-"], input=script, text=True, capture_output=True, check=check
    )


def tables():
    # a recreated table gets a new handle
    return subprocess.run(
        ["nft", "-j", "list", "tables"], capture_output=True, text=True
    ).stdout


def field(regex, text):
    m = re.search(regex, text)
    return m.group(1) if m else ""


def rule_name(text):
    comment = COMMENT_RE.search(text)
    if comment:
        return comment.group(1)
    # banIP rules: the set name tells which list matched
    ip_set = re.search(r"@(\S+)", text)
    if ip_set:
        return ip_set.group(1)
    # rule resolved against a stale ruleset cache: no text to show
    if text.startswith("unknown "):
        return ""
    text = re.sub(r"counter packets \d+ bytes \d+ ", "", text[len("rule ") :])
    return VERDICT_RE.sub("", text).strip()


def user_jump(t, chain):
    # the stored jump is a user rule targeting this zone verdict chain
    jump = t.get("jump")
    return bool(
        ZONE_VERDICT_RE.match(chain)
        and jump
        and COMMENT_RE.search(jump[2])
        and field(r"\(verdict (?:jump|goto) ([^)\s]+)", jump[2]) == chain
    )


def flow_key(protocol, source, source_port, destination, destination_port):
    return f"{protocol}|{source}|{source_port}|{destination}|{destination_port}"


def is_private(address):
    try:
        ip = ipaddress.ip_address(address)
        return any(ip in n for n in PRIVATE_NETS)
    except ValueError:
        return False


def is_multicast(address):
    try:
        return ipaddress.ip_address(address).is_multicast
    except ValueError:
        return False


# routes matching each destination, looked up again after ROUTE_TTL seconds
ROUTE_TTL = 10
ROUTES = {}


def default_route_only(address, out):
    # true when only default routes match and out is one of their devices
    try:
        cached = ROUTES.get(address)
        if not cached or time.time() - cached[0] > ROUTE_TTL:
            if len(ROUTES) >= MAX_FLOWS:
                ROUTES.clear()
            family = "-6" if ":" in address else "-4"
            p = subprocess.run(
                ["ip", family, "-j", "route", "list", "match", address],
                capture_output=True,
                text=True,
            )
            ROUTES[address] = (time.time(), json.loads(p.stdout))
        routes = ROUTES[address][1]
        return all(r.get("dst") == "default" for r in routes) and out in {
            r.get("dev") for r in routes
        }
    except Exception:
        return False


def dpi_flows():
    # ns-flows daemon is optional
    try:
        resp = requests.get("http://127.0.0.1:8080/flows", timeout=2)
        return [item.get("flow") or {} for item in resp.json().get("flows", [])]
    except Exception:
        return []


def dpi_app(flows, source, source_port, destination, destination_port):
    ends = {(source, source_port), (destination, destination_port)}
    for flow in flows:
        local = (str(flow.get("local_ip")), str(flow.get("local_port")))
        other = (str(flow.get("other_ip")), str(flow.get("other_port")))
        if {local, other} == ends:
            application = flow.get("detected_application_name") or ""
            host = flow.get("host_server_name") or ""
            return application.removeprefix("netify."), host
    return "", ""


class Collector:
    def __init__(self, ip, duration, port, protocol):
        self.ip = ip
        self.duration = duration
        self.port = port
        self.protocol = protocol
        self.start = int(time.time())
        self.traces = {}
        self.blocked = {}
        self.blocked_tuples = {}
        self.flows = {}
        self.dns = {}
        self.pending_dns = {}
        self.filtered = {}
        self.failure = ""
        self.adblock_list = None
        # nft monitor printed a rule missing from its ruleset cache
        self.stale_rules = False
        # something was skipped by the rate limit or a list cap
        self.truncated = False

    def setup(self):
        uci = EUci()
        if uci.get("adblock", "global", "adb_enabled", default="0") == "1":
            self.adblock_list = next(
                iter(glob.glob("/tmp/dnsmasq.*.d/adb_list.overall")), None
            )

    def trace_line(self, line):
        m = TRACE_RE.match(line)
        if not m:
            return
        tid, table, chain, rest = m.groups()
        if table == TABLE:
            # each traced packet starts with a packet line of our own table
            if rest.startswith("packet: "):
                # trace id reused: keep the previous group to be closed on its own
                if tid in self.traces:
                    self.traces[(tid, time.time())] = self.traces.pop(tid)
                self.traces[tid] = {
                    "time": time.time(),
                    "last": time.time(),
                    "in": "",
                    "out": "",
                    "tuple": None,
                    "routed": False,
                }
            return
        t = self.traces.get(tid)
        if t is None:
            return
        t["last"] = time.time()
        # any input or forward stage chain means the packet passed routing
        if "input" in chain or "forward" in chain:
            t["routed"] = True
        if rest.startswith("packet: "):
            t["in"] = t["in"] or field(r'\biif "([^"]+)"', rest)
            t["out"] = t["out"] or field(r'\boif "([^"]+)"', rest)
            if t["tuple"] is None:
                t["ttl"] = field(r"\b(?:ip ttl|ip6 hoplimit) (\d+)", rest)
                t["tuple"] = (
                    # conntrack names ipv6-icmp as icmpv6
                    field(r"\b(?:ip protocol|ip6 nexthdr) (\S+)", rest).replace(
                        "ipv6-icmp", "icmpv6"
                    ),
                    field(r"\bip6? saddr (\S+)", rest),
                    field(r"\b(?:tcp|udp) sport (\d+)", rest),
                    field(r"\bip6? daddr (\S+)", rest),
                    field(r"\b(?:tcp|udp) dport (\d+)", rest),
                )
            return
        if rest.startswith("unknown rule "):
            self.stale_rules = True
        is_rule = rest.startswith(("rule ", "unknown rule "))
        verdict = (
            field(r"\(verdict (\w+)", rest)
            if is_rule
            else field(r"^policy (\w+)", rest)
        )
        if verdict in ("jump", "goto"):
            if not user_jump(t, chain):
                t["jump"] = (table, chain, rest)
        elif verdict in ("drop", "reject") and "drop" not in t:
            if "jump" in t and (chain in REJECT_CHAINS or user_jump(t, chain)):
                t["drop"] = t["jump"]
            else:
                t["drop"] = (
                    table,
                    chain,
                    rest if is_rule else "rule policy drop",
                )
        elif (
            verdict == "accept"
            and table == "fw4"
            and not chain.startswith(("srcnat", "dstnat"))
        ):
            comment = COMMENT_RE.search(t["jump"][2] if user_jump(t, chain) else rest)
            if comment and "accept" not in t:
                t["accept"] = comment.group(1)

    def finalize(self, idle):
        now = time.time()
        flows = None
        # unrouted groups wait longer: their input/forward lines may still be queued
        for tid in [
            tid
            for tid, t in self.traces.items()
            if now - t["last"] >= (idle if t["routed"] or "drop" in t else idle * 10)
        ]:
            t = self.traces.pop(tid)
            if t["tuple"] is None:
                continue
            protocol, source, source_port, destination, destination_port = t["tuple"]
            if "drop" in t:
                table, chain, text = t["drop"]
                rule = rule_name(text)
                layer = "dpi" if chain == "dpi_actions" else LAYERS.get(table, table)
                # a flow accepted first and dropped later by DPI is blocked only
                if layer == "dpi":
                    reply = (destination, destination_port, source, source_port)
                    for key in (t["tuple"], (protocol, *reply)):
                        self.flows.pop(flow_key(*key), None)
            elif not t["routed"]:
                # unjoined multicast and expiring TTL are dropped by routing on purpose
                if is_multicast(destination) or t["ttl"] in ("0", "1"):
                    continue
                # left prerouting without reaching input or forward: no route
                table, chain, rule, layer = "", "", "no_route", "routing"
            else:
                key = flow_key(*t["tuple"])
                self.flows.pop(key, None)
                self.flows[key] = {
                    "in_interface": t["in"],
                    "out_interface": t["out"],
                    "rule": t.get("accept", ""),
                }
                if len(self.flows) > MAX_FLOWS:
                    del self.flows[next(iter(self.flows))]
                    self.truncated = True
                if (
                    not t["out"]
                    or not is_private(destination)
                    or not default_route_only(destination, t["out"])
                ):
                    continue
                # private destination on the default route: missing route or tunnel down
                table, chain, rule, layer = "", "", "private_to_wan", "routing"
            key = (protocol, source, destination, destination_port, table, chain, rule)
            entry = self.blocked.get(key)
            if entry is None:
                if len(self.blocked) >= MAX_ITEMS:
                    self.truncated = True
                    continue
                entry = self.blocked[key] = {
                    "protocol": protocol,
                    "source": source,
                    "destination": destination,
                    "destination_port": destination_port,
                    "layer": layer,
                    "table": table,
                    "chain": chain,
                    "rule": rule,
                    "in_interface": t["in"],
                    "out_interface": t["out"],
                    "count": 0,
                    "first_seen": int(t["time"]),
                }
            # retry while empty: ns-flows may publish the flow after the first drop
            if layer == "dpi" and not entry.get("application"):
                if flows is None:
                    flows = dpi_flows()
                entry["application"], entry["host"] = dpi_app(
                    flows, source, source_port, destination, destination_port
                )
            # count distinct connections, not packets
            tuples = self.blocked_tuples.setdefault(key, set())
            if t["tuple"] not in tuples:
                tuples.add(t["tuple"])
                entry["count"] += 1
            entry["last_seen"] = int(t["time"])

    def is_filtered(self, name):
        if self.adblock_list is None:
            return False
        if name not in self.filtered:
            labels = name.split(".")
            suffixes = [".".join(labels[i:]) for i in range(len(labels))]
            args = []
            for s in suffixes:
                args += ["-e", f"local=/{s}/", "-e", f"local=/{s}/#"]
            found = set(
                subprocess.run(
                    ["grep", "-xF", *args, self.adblock_list],
                    capture_output=True,
                    text=True,
                ).stdout.splitlines()
            )
            # most specific match wins, allowlist lines end with "#"
            self.filtered[name] = next(
                (
                    f"local=/{s}/" in found
                    for s in suffixes
                    if f"local=/{s}/" in found or f"local=/{s}/#" in found
                ),
                False,
            )
        return self.filtered[name]

    def dns_line(self, line):
        m = QUERY_RE.search(line)
        if m:
            qid, qtype, name = m.group(1), m.group(2), m.group(3).rstrip(".")
            if self.pending_dns.get(qid) == (name, qtype):
                return
            self.pending_dns[qid] = (name, qtype)
            entry = self.dns.get((name, qtype))
            if entry is None:
                if len(self.dns) >= MAX_ITEMS:
                    self.truncated = True
                    return
                entry = self.dns[(name, qtype)] = {
                    "name": name,
                    "type": qtype,
                    "result": "",
                    "filtered": self.is_filtered(name),
                    "count": 0,
                }
            entry["count"] += 1
            entry["last_seen"] = int(time.time())
            return
        m = REPLY_RE.search(line)
        if m and m.group(1) in self.pending_dns:
            entry = self.dns.get(self.pending_dns.pop(m.group(1)))
            if entry:
                entry["result"] = (m.group(2) or "NOERROR").upper()

    def check_skipped(self):
        # false when the trace table is gone
        p = subprocess.run(
            ["nft", "list", "counter", "inet", TABLE, "skipped"],
            capture_output=True,
            text=True,
        )
        if not self.truncated:
            self.truncated = field(r"packets (\d+)", p.stdout) not in ("", "0")
        return p.returncode == 0

    def line(self, kind, line):
        (self.trace_line if kind == "trace" else self.dns_line)(line)

    def write(self, running):
        state = {
            "running": running,
            "ip": self.ip,
            "duration": self.duration,
            "port": self.port,
            "protocol": self.protocol,
            "start": self.start,
            "blocked": list(self.blocked.values()),
            "dns": list(self.dns.values()),
            "flows": self.flows,
            "failure": self.failure,
            "truncated": self.truncated,
        }
        with open(STATE + ".tmp", "w") as f:
            json.dump(state, f)
        os.replace(STATE + ".tmp", STATE)


def reader(proc, kind, lines):
    for line in proc.stdout:
        lines.put((kind, line.rstrip("\n")))


def main():
    ip = str(ipaddress.ip_address(sys.argv[1]))
    duration = int(sys.argv[2])
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    protocol = sys.argv[4] if len(sys.argv) > 4 else ""
    if protocol not in ("", "tcp", "udp"):
        raise ValueError("invalid protocol")
    family = "ip6" if ":" in ip else "ip"
    # th dport is only meaningful on tcp/udp headers
    l4proto = protocol or ("{ tcp, udp }" if port else "")
    match = (f"meta l4proto {l4proto} " if l4proto else "") + (
        f"th dport {port} " if port else ""
    )
    collector = Collector(ip, duration, port, protocol)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    collector.write(True)
    procs = []
    threads = []
    lines = queue.Queue()
    try:
        collector.setup()
        nft(f"table inet {TABLE}\ndelete table inet {TABLE}\n")
        new = (
            f"{family} saddr {ip} {match}ct state new ct original packets 1",
            f"{family} daddr {ip} {match}ct state new ct original packets 1",
        )
        # DPI blocks a flow after its first packets
        blocked = f"{family} saddr {ip} {match}ct label netify-blocked"
        # accept only ends this chain; new connections reaching the counter were not traced
        rules = "".join(
            f"{r} limit rate 50/second burst 100 packets meta nftrace set 1 accept\n"
            for r in (*new, blocked)
        ) + "".join(f"{r} counter name skipped\n" for r in new)
        nft(
            f"table inet {TABLE} {{\ncounter skipped {{}}\nchain pre {{\n"
            f"type filter hook prerouting priority -199;\n{rules}}}\n}}\n",
            check=True,
        )
        # only queries sent by the client and their replies
        dns_filter = f"udp and ((src host {ip} and dst port 53) or (dst host {ip} and src port 53))"

        def spawn(kind, cmd):
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                errors="replace",
            )
            threads.append(
                threading.Thread(target=reader, args=(proc, kind, lines), daemon=True)
            )
            threads[-1].start()
            return proc

        known = tables()
        for kind, cmd in (
            ("trace", ["nft", "monitor", "trace"]),
            ("dns", ["tcpdump", "-l", "-n", "-i", "any", dns_filter]),
        ):
            procs.append(spawn(kind, cmd))
        monitor = threads[0]
        with open(PID, "w") as f:
            f.write(str(os.getpid()))
        end = time.time() + duration
        last_write = 0
        while time.time() < end and not stop.is_set():
            try:
                collector.line(*lines.get(timeout=0.5))
            except queue.Empty:
                pass
            if time.time() - last_write >= 1:
                # a recreated table reuses rule handles: no unknown rule is printed
                current = tables()
                if current != known:
                    known = current
                    collector.stale_rules = True
                # nft monitor caches the ruleset at start: restart it after a reload
                if collector.stale_rules:
                    procs[0].kill()
                    procs[0].wait()
                    # lines of the old monitor must not ask for another restart
                    monitor.join(1)
                    while not lines.empty():
                        collector.line(*lines.get())
                    # groups cut by the restart would be reported as no_route
                    collector.traces = {
                        k: t
                        for k, t in collector.traces.items()
                        if t["routed"] or "drop" in t
                    }
                    procs[0] = spawn("trace", procs[0].args)
                    monitor = threads[-1]
                    collector.stale_rules = False
                for proc in procs:
                    if proc.poll() is not None:
                        raise RuntimeError(f"{proc.args[0]} exited")
                collector.finalize(0.5)
                if not collector.check_skipped():
                    raise RuntimeError("trace table removed")
                collector.write(True)
                last_write = time.time()
    except Exception as e:
        collector.failure = (getattr(e, "stderr", None) or str(e)).strip()
    finally:
        collector.check_skipped()
        nft(f"delete table inet {TABLE}\n")
        for proc in procs:
            proc.kill()
            proc.wait()
        for thread in threads:
            thread.join(1)
        # process lines still queued before closing the open groups
        try:
            while not lines.empty():
                collector.line(*lines.get())
        except Exception as e:
            collector.failure = collector.failure or str(e)
        collector.finalize(0)
        collector.write(False)
        if os.path.exists(PID):
            os.remove(PID)


if __name__ == "__main__":
    main()
