# ns-report

NethSecurity reports.

## DPI report

The `dpireport` daemon connects to netifyd socket and collects
data about local machines.

Collected data are used to create lightsquid-like reports.

Configuration environment variables:

- `NETIFYD_SOCKET`: netifyd socket path, default is `/var/run/netifyd/netifyd.sock`
- `FLOW_STALE_TIMEOUT`: cleanup flows not updated for `x` seconds, default is `3600` seconds
- `DUMP_TIMEOUT`: write statistics to the disk and perform cleanup tasks every x seconds, default is '120' seconds
- `DUMP_PATH`: destination path for statistics, default is `/var/run/dpireport`
- `LOG_LEVEL`: available log levels are `DEBUG` and `INFO`, default is `INFO`

### File format

The daemon saves data files inside the `/var/run/dpirepor/<year>/<month>/<day>/<client>/` directory where `client` is the IP address
of a network host. The directory contains a JSON for each hour of the day.
Example: `/var/run/dpireport/2023/06/15/192.168.100.152/23.json`

The JSON represents a collection of network host traffic data during one hour.
The top-level keys are:
- `protocol` indicates the protocols used, such as `ntp` (Network Time Protocol), `http/s` (HTTP/HTTPS), and `dns` (Domain Name System).
   The corresponding values are the total traffic counts in bytes for each protocol during that time period.
- `host` represents the individual network target hosts and their respective traffic counts.
   The host names could be something like "2.centos.pool.ntp.org".
   The numeric values associated with each host indicate the traffic counts in bytes attributed to them during that time period
- `application` specifies the DPI application detected by netifyd like "netify.ntp".
   The numeric values associated with each application is the the traffic counts in bytes during the interval.
- `total` denotes the overall total traffic count for that specific time period.

Overall, this JSON provides a breakdown of network host traffic, protocols used, host names, application-specific traffic,
and the total traffic count for each time period.

During data collection, the transferred bytes are accumulated and attributed to the respective keys: "protocol," "host," and "application."
For instance, let's consider an example: if a client exchanges 1MB of traffic with a Fedora mirror,
that 1MB of traffic will be added to the "mirrors.fedoraproject.org" host,
the "http/s" protocol, the "netify.fedora-project" application, and ultimately contribute to the "total" traffic count.

Example:
```json
{
  "total": 253211,
  "protocol": {
    "http": 238877,
    "dns": 3512,
    "http/s": 10642,
    "ntp": 180
  },
  "application": {
    "netify.nethserver": 241733,
    "netify.ubiquiti": 11298,
    "netify.ntp": 180
  },
  "host": {
    "ubnt.nethesis.it": 241733,
    "trace.svc.ui.com": 11298,
    "pool.ntp.org": 180
  }
}
```

### Data retention policy

A cron job is executed every night to enforce the data retention policy.

The retention policy aims to keep the `/var/run/dpireport` directory within a certain size limit (1% of /tmp filesystem)
by removing the oldest report directories that are not from the current day.
This ensures that only recent data is retained, while older data is automatically deleted to free up disk space.
