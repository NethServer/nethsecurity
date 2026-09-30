# ns-audit

## Overview

`ns-audit` collects nftables log records through **NFLOG** instead of the kernel
ring buffer, and hands them to syslog.

The standard `log` statement in nftables goes through `printk`, which means every
matched packet is printed on the system console and mixed into `dmesg`. The
`log group N` statement instead sends the record to a `nfnetlink_log` netlink
group, which never touches `printk`. `ns-audit` runs a private [ulogd][ulogd]
instance bound to that group and re-emits each record via `syslog(3)`.

Since `victoria-logs` already forwards all syslog traffic to VictoriaLogs on
`127.0.0.1:5514`, the records become queryable with no extra plumbing.

```
nft log group 1  ->  nfnetlink_log  ->  ulogd (ns-audit)  ->  syslog
                                                               |
                                                            rsyslog
                                                               |
                                              VictoriaLogs :5514 / :9428
```

**Key components:**
- **ulogd**: netfilter userspace logging daemon, run as a private instance
- **NFLOG group 1**: netlink group `ns-audit` binds to
- **syslog facility `local3`**: what the records are emitted on

## Installation

This package is **not installed by default**.

```bash
apk add ns-audit
```

It does not start on its own. Enable and start it:

```bash
/etc/init.d/ns-audit enable
/etc/init.d/ns-audit start
```

`ns-audit` depends on the stock `ulogd` package for the binary and plugins, but
runs its own instance from its own config file. **Leave `/etc/init.d/ulogd`
disabled** — two daemons bound to the same NFLOG group will fight over it:

```bash
/etc/init.d/ulogd disable
```

## Emitting records

`ns-audit` ships no firewall rules. Add the `log` statement to the rules you
want audited, pointing at group 1:

```
log group 1 prefix "ns-audit "
```

Add `snaplen 64` when only headers are needed — by default the whole packet is
copied into the netlink socket.

Do **not** use a bare `log` statement for this: without `group` it goes back to
`printk` and the console noise returns. The `level` keyword is meaningless once
`group` is set.

## Querying

Records carry `app_name=ulogd` — the ident is hardcoded in ulogd's syslog output
plugin and cannot be changed from the config file. In the VictoriaLogs UI
(`http://127.0.0.1:9428/select/vmui`):

```
app_name:ulogd
```

Narrow to this package's records by the nftables prefix:

```
app_name:ulogd AND _msg:"ns-audit "
```

Records also land in `/var/log/messages`, since the rsyslog ruleset installed by
`victoria-logs` matches `*.*`.

## Configuration

Configuration lives in `/etc/ns-audit/ulogd.conf` and is a conffile, so local
edits survive package upgrades. It is not managed by UCI.

**Commonly changed settings:**

| Setting | Section | Default | Meaning |
|---|---|---|---|
| `group` | `[nsaudit]` | `1` | NFLOG netlink group to bind. Group 0 is reserved by the kernel for conntrack invalid messages. |
| `facility` | `[sys1]` | `LOG_LOCAL3` | Syslog facility. Accepts `LOG_DAEMON`, `LOG_KERN`, `LOG_USER`, `LOG_LOCAL0`–`LOG_LOCAL7`. |
| `level` | `[sys1]` | `LOG_INFO` | Syslog level. Accepts `LOG_EMERG` through `LOG_DEBUG`. |
| `netlink_qthreshold` | `[nsaudit]` | `20` | Packets queued kernel side before ulogd is woken. Raise to cut wakeups under load, at the cost of latency. |
| `loglevel` | `[global]` | `5` | ulogd's own status verbosity: debug(1), info(3), notice(5), error(7), fatal(8). |

After editing:

```bash
/etc/init.d/ns-audit restart
```

ulogd has no include directive — the config is a single flat file, so there is
no drop-in directory.

## Troubleshooting

ulogd's own status messages go to `/var/log/ns-audit-ulogd.log`, separate from
the packet records.

```bash
# service state
/etc/init.d/ns-audit status

# daemon status log
cat /var/log/ns-audit-ulogd.log

# is anything arriving on the group?
cat /proc/net/netfilter/nfnetlink_log
```

**No records arriving:** confirm a rule actually uses `log group 1`, and that
`nfnetlink_log` is loaded (`lsmod | grep nfnetlink_log`).

**`We are losing events` in the status log:** the netlink socket buffer is
overflowing. Raise `netlink_socket_buffer_maxsize`, raise `netlink_qthreshold`,
or add a `limit rate` to the logging rule.

**Records on the console anyway:** a rule is still using a bare `log` statement
somewhere. NFLOG cannot suppress that; find and convert the rule.

## Notes

- Logging is per-packet, not per-flow. A busy rule will fill `/var/log` quickly —
  `/var/log` is tmpfs. Use `limit rate` in the logging rule.
- One NFLOG group feeds one ulogd stack. To split rule classes into separate
  outputs, add another `[logN]`/`stack=` pair with a different group.
- Only `ulogd-mod-syslog` is wired up here. The `extra` plugin set also ships
  `output_LOGEMU` (plain file) and the package set includes `ulogd-mod-json`
  (structured output) if a different destination is wanted later.

## See Also

- [Victoria Logs](../victoria-logs/) — where the records are stored and queried
- [ulogd][ulogd] — upstream netfilter userspace logging daemon

[ulogd]: https://www.netfilter.org/projects/ulogd/index.html
