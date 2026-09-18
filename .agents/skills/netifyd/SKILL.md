---
name: netifyd
description: Work with the Netify Agent (netifyd) DPI daemon on NethSecurity — its configuration graph, processor/sink plugins, flow-actions rules, criteria expressions, address groups, telemetry records and CLI. Always use this skill when the task touches netifyd, netify-proc-*/netify-sink-* plugins, /etc/netifyd, netifyd.conf, plugins.d, address-groups.d, DPI criteria or flow expressions, nfqueue capture, conntrack labels set by DPI, or netify telemetry (flow, flow-purge, flow-stats, agent-status, intelligence) — even when the user only says "DPI", "flow actions", "netify", "app blocking" or "the agent". It fetches the live Netify v5 documentation index instead of relying on memory, and maps out which file on a NethSecurity device owns what.
compatibility: Works with OpenCode and other Agent Skills-compatible tools. Needs network access for the Netify docs index, and SSH to a live device for anything that must be verified against a running agent.
metadata:
  domain: nethsecurity-dpi
  type: daemon-integration
---

## What I do

- Route you to the authoritative Netify Agent v5 documentation before you write anything
- Explain netifyd's configuration graph as it actually exists on NethSecurity: who owns which file, and what a reload re-reads
- Get processor/sink plugin wiring right, including the two different ways a sink is referenced
- Point criteria expressions at the field and type authority instead of at guesswork
- Give you the on-device verification loop: the dumps, reload vs restart, and where to watch

## When to use me

Any task involving: netifyd configuration or plugins, flow-actions rules, criteria/expression authoring, address groups, category lists, application overlay, capture interfaces and nfqueue, netify telemetry records, or debugging a netifyd that crash-loops or classifies nothing.

Not for: bumping the `netifyd` package version or touching `netify-dist.mk` — that's `openwrt-package`. Writing the `ns.dpi` API surface — that's `ns-api`.

---

## Step 1 — Fetch the live docs index first

Netify's agent docs move between releases, and the v5 plugin/telemetry surface is large enough that
recalling field names from memory is how configs get written with keys that silently do nothing. So the
first action of every netifyd task, before opening any file:

```
WebFetch https://www.netify.ai/developer/agent/v5/llms.txt
```

That is a link map, not documentation — it lists every page and schema with a one-line summary. Read it,
pick the one to three pages that actually cover the task, and fetch those. Do not fetch the whole set.

Docs are machine-readable Markdown at `…/developer/agent/v5/docs/<name>.md`; JSON Schemas for plugin
configs and telemetry records are at `…/developer/agent/v5/schemas/<name>.json`. Prefer these over the
human-facing `netify.ai/documentation/…` HTML pages — same content, less noise. Older notes in this repo
still link the HTML paths; treat them as equivalent, and use the index to find the current URL.

Which page to fetch, by task:

| Task | Fetch |
|---|---|
| Writing or reviewing a criteria expression | Expression Engine (**always** — it is the field authority) |
| Blocking / QoS / enforcement rules | Flow Actions Processor + Expression Engine |
| Adding a telemetry consumer | Core or Aggregator Processor + the relevant Sink + the telemetry record page |
| Parsing telemetry someone else emitted | the matching Telemetry page, plus its schema if you need every field |
| Capture setup, nfqueue, interface roles | Network Interfaces |
| Runtime tuning (flow table, caches, threads) | Agent Settings |
| Reusable IP/MAC groups | Address Groups |
| Custom domain/regex/CIDR categories | Category Lists (BYOC) |
| Relabelling detected apps | Application Overlay |
| Verifying a config key exists at all | the plugin's JSON Schema under `schemas/` |

`…/developer/agent/v5/llms-full.txt` is the comprehensive dump. Reach for it only when the task spans many
plugins at once, or when a specific page turns out not to answer the question — it is large.

**Check the version.** The index is v5; the agent this repo ships is pinned in
`packages/netifyd/Makefile` (`NETIFYD_VERSION`), and a live device reports its own via
`netifyd --version`. If they disagree at the minor level, say so before relying on a newly documented
option — the docs describe the current v5, not necessarily the build in the tree.

---

## Step 2 — Know the configuration graph

netifyd reads one entry-point file and follows it into directories. Nothing merges implicitly; every
piece is loaded because something named it.

```
/etc/netifyd.conf                     entry point: names the profile, the state paths, the PLM library
└── /etc/netifyd/profiles.d/00-default.conf
                                      the actual [netifyd] tuning: flow map, TTLs, caches, protocols,
                                      max_detection_pkts, netify-api, netlink buffers
/etc/netifyd/
├── interfaces.d/10-nfqueue.conf      capture sources — on NethSecurity these are nfqueue, not devices
├── plugins.d/*.conf                  plugin LOADERS (ini). One section = one plugin instance
├── netify-<name>.json                per-instance plugin config, named by its loader's conf_filename
├── address-groups.d/NN-<tag>.conf    @tag groups; one address per line
├── categories.d/NN-<tag>.conf        BYOC pattern lists (dom:/rxp:/net: entries)
├── netify-apps.conf                  application signatures
├── netify-categories.json            category definitions
├── netify-*-catalog.json             display metadata, refreshed nightly by dpi-data-update
└── agent.uuid                        agent identity (conffile — do not regenerate casually)
```

In this repo those files live under `packages/netifyd/files/etc/…`, plus
`packages/ns-monitoring/files/netifyd/…` for the monitoring consumers and `packages/ns-dpi/files/…` for
the DPI pipeline. `/usr/share/netifyd/` holds the shipped templates and `functions.sh`; treat it as
read-only reference at runtime.

### Never hand-edit a generated file

Several files under `/etc/netifyd/` are written by NethSecurity code on every run, so an edit survives
until the next reload and then vanishes. Change the generator or its UCI input instead.

| File | Written by | Real input |
|---|---|---|
| `netify-proc-flow-actions.json` | `/usr/sbin/dpi-config` (via `/usr/sbin/dpi`) | `/etc/config/dpi` |
| `table inet netifyd` (nftables) | `/usr/sbin/ns-netifyd-configure` (on start and reload) | `/etc/config/netifyd` → `ns_config` |
| `netify-application-catalog.json` and the other catalog/category files | `dpi-data-update` (nightly cron) | Netify's data service |
| `/usr/share/nftables.d/table-pre/` DPI chains | `/usr/sbin/dpi-nft` | `/etc/config/dpi` |

`/usr/sbin/dpi` is the whole DPI apply path: `dpi-config` → `dpi-nft` → `/etc/init.d/netifyd reload`.
Run it after changing `/etc/config/dpi`; don't reproduce its steps by hand.

---

## Plugin loaders — the part the docs assume you already know

A plugin is not enabled by writing its JSON. It is enabled by an ini section in `plugins.d/`:

```ini
[proc-ns-flows]
enable = yes
plugin_library = ${path_plugin_libdir}/libnetify-proc-core.so.0.0.0
conf_filename = ${path_state_persistent}/netify-ns-flows-proc.json
```

Three things follow from this, and each one is a real mistake if missed:

**The section name is the instance name.** It is the handle every other config uses to point at this
plugin. Rename the section and every reference breaks silently.

**One library can be loaded many times under different names.** `ns-monitoring` loads
`libnetify-proc-core.so` as `proc-ns-flows` and `libnetify-proc-aggregator.so` as `proc-ns-stats`, each
with its own HTTP sink instance (`sink-ns-flows`, `sink-ns-stats`) and its own JSON. That is the pattern to
copy for a new consumer: your own loader file, your own instance names, your own JSON — never bolt a
channel onto someone else's instance, because then their reload semantics and failure modes become yours.

**A sink is referenced in two different shapes**, depending on who is doing the referencing:

- From a **processor** config — a nested map, `sinks` → sink instance → channel:
  ```json
  { "sinks": { "sink-ns-flows": { "default": { "enable": true, "types": ["stream-flows"] } } } }
  ```
- From a **flow-actions target** — flat `sink` and `channel` keys:
  ```json
  { "log": { "target_type": "sink", "target_enabled": true, "sink": "sink-log", "channel": "nfa_block_log" } }
  ```

The two are different schemas, so check which one you are writing against — the processor schema for a
proc config, the flow-actions schema for a target — and confirm delivery on a device rather than assuming
a loaded plugin is a delivering one.

Channel names inside a sink config are yours to choose, but the processor or target that routes to them
must use the exact same string.

---

## Criteria expressions

Fetch the Expression Engine page before writing one. It carries the field list and the type table, and
those are the two things that decide whether an expression is valid — neither is guessable, and both are
what a generator has to encode.

**Terminate every expression with `;`.** Standard syntax requires the terminator; only the compact syntax
does without. Normalise it on everything you emit, whatever the source — the current generator appends it
to criteria it builds itself, but not to raw `criteria` taken from UCI and not to entries in the global
`exemptions` array, so both of those paths need it added.

**Quote according to the type table, not by analogy.** Address-typed fields take bare literals; only
`string` and `mixed` types are quoted:

```
local_ip == 10.0.2.0/24            # address type: no quotes
app == 'netify.youtube'            # string type: quoted
local_ip == @objects_ns_hostset_1  # @tag reference: no quotes
```

**Only emit fields the Expression Engine documents,** and whitelist them in a generator rather than
passing user input straight through. Values are looser than fields — an app, protocol or category tag the
agent doesn't know simply never matches.

**Match by name, never by numeric ID.** Use `app`, `proto`, `app_category`, `proto_category`, not the
`_id` variants. Signature and category data is refreshed nightly by `dpi-data-update` and is free to
renumber IDs; names stay readable in stored config and survive the refresh.

**Never emit an empty criteria.** Validate before writing and skip-and-log what fails, rather than writing
it out and finding out later.

---

## Address groups

A group is a file whose **name defines the tag**: netifyd strips the two-digit prefix and the `.conf`
suffix, so `/etc/netifyd/address-groups.d/30-objects_ns_hostset_1.conf` is referenced as
`local_ip == @objects_ns_hostset_1`. Contents are one address, CIDR or MAC per line.

Why this matters: a criteria stays one term wide however large the group gets, and editing group membership
touches one small file instead of regenerating the whole plugin config. A reload re-reads every group file.

Two operational facts:

- **The directory does not exist by default.** netifyd logs `Error opening directory` on every start until
  something creates it. Create it in the package install and re-ensure it in any writer.
- **Prefixes below `20-` belong to the agent**, which manages its own groups over its control socket.
  NethSecurity writers start at `20-`. Each writer must delete only files in its own range, or it will
  destroy agent-managed and hand-placed groups.

MAC members only match via `mac ==`, so don't put them in a group a `local_ip` rule references.

---

## Verify on a live device

The agent's own dumps are the authority on what it can currently match:

```bash
netifyd --version
netifyd --status              # PID, uptime, flow counts
netifyd --dump-apps           # applications the running agent can match
netifyd --dump-protos
netifyd --dump-categories     # category TAGS — e.g. social-media, not social
netifyd --dump-category <type>
```

Use the dumps, not the catalog JSONs, to decide whether a tag can match. The catalogs carry display names
and icons for ~1500+ apps; the *loaded signature list* drops to ~200 without a subscription (`ns-dpi`'s
`70dpi` strips premium signatures on unregister). A catalog entry with no loaded signature never matches.

Applying and watching:

```bash
/etc/init.d/netifyd reload    # re-runs ns-netifyd-configure, then signals the agent: re-reads
                              # plugin configs, address groups and category lists. Enough for
                              # almost every config change.
/etc/init.d/netifyd restart   # only for netifyd.conf, the profile, or interfaces.d changes
/usr/sbin/dpi                 # after editing /etc/config/dpi — regenerate, apply nft, reload
logread -f -e netifyd         # watch a reload land, and whether the agent stays up
nft list table inet netifyd   # the nfqueue capture table (bypass sets, queue chains)
```

Then generate traffic that should match and confirm the outcome — for enforcement, that the conntrack entry
carries the expected label from `/etc/connlabel.conf`; for telemetry, that records reach the consumer.

---

## Before you ship a config change

- Fetched the relevant docs page this session, rather than working from recall
- Every key checked against the plugin's JSON Schema — a wrong key is silent
- Every expression semicolon-terminated, quoting per the type table, fields whitelisted, matched by name
- Editing the generator or its UCI input, not a generated file
- Reload vs restart chosen deliberately, and the agent still running afterwards (`logread` clean)
- Traffic actually generated, and the label or the telemetry record confirmed
- New consumer got its own loader section, instance names and JSON, and did not attach to an existing instance

---

## References

- `references/nethsecurity-wiring.md` — the full NethSecurity-side inventory: UCI options, the nfqueue
  table and bypass sets, the DPI pipeline and conntrack labels, telemetry consumers, HA triggers. Read it
  when the task crosses from the daemon into NethSecurity's own plumbing.
