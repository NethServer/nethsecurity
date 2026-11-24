# modsecurity

ModSecurity v3 WAF for the nginx shipped with NethSecurity.

## What's here

- `packages/modsecurity`: builds `libmodsecurity` with yajl, libxml2, lmdb and curl. Lua and GeoIP/MaxMind are left out. It also ships `modsecurity-crs-update`, which downloads the latest [OWASP CRS](https://coreruleset.org) release on the device and enables it. Until it runs, only the base rules from `modsecurity.conf` are active.
- `patches/feeds/packages/102-nginx-modsecurity.patch`: adds the `nginx-mod-modsecurity` module ([ModSecurity-nginx](https://github.com/owasp-modsecurity/ModSecurity-nginx)) to the upstream nginx package. (TODO: probably to move this line elsewhere?)

## What it does

- Installs the ModSecurity library and its base config, and enables the WAF on every nginx server.
- Running `modsecurity-crs-update` installs the latest CRS release from the upstream repo. The rules aren't part of the backup, so after a sysupgrade or a package upgrade CRS is off until the next run.
- Moves the ModSecurity lines of the nginx error log under the `modsecurity` app, so they show up on their own in the firewall logs and Victoria Logs.- Blocks the matching requests, the engine runs in blocking mode and not in detection only: 403 when the CRS anomaly score is exceeded, 400 when a request body can't be parsed.

## TODO

- `SecRequestBodyLimit` caps request bodies at about 13 MB and rejects anything bigger, which breaks the image upload from the UI. Fine for most applications, but we'll need to figure out how to handle bigger uploads.
- Make the configuration manageable through UCI instead of patching files.
- Only blocks are logged. Detections that let the request through are logged by nginx at `info`, but the servers log errors at `error` and above, so they never reach syslog.
- CRS blocks the UI dashboard: the uptime chart queries `/api/metrics/query_range` with a PromQL expression that scores 8, over the threshold of 5.- `modsecurity-crs-update` runs only by hand, it needs a cron job.
- Verify the GPG signature of the downloaded release.
- Test the new rules with `nginx -t` before the reload and roll back to the previous copy if they fail, a broken rule set stops nginx, UI included, at the next restart.
- Skip the download when the installed version is already the latest one.
