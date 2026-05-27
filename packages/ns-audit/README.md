# ns-audit

On-device NethSecurity audit reporting package.

This package provides a read-only local audit pipeline for NethSecurity. It
collects sanitized evidence, runs the available analyzers, renders
`audit-report.html` with Jinja2, packages it into `audit-report.tar.gz`, and
exposes an optional read-only `ns.audit` RPCD endpoint. It does not generate
PDF files or change appliance configuration.

## Execution model

- Runs locally on the NethSecurity appliance.
- Does not use SSH, Paramiko, remote collectors, or external report services.
- Does not write UCI configuration, call `uci commit`, restart services, or
  modify `/etc/config/*`.
- Reads local configuration and runtime state to build sanitized JSON artifacts.
- Produces HTML, JSON, and tar.gz bundle artifacts; PDF output is intentionally unsupported.
- The RPCD endpoint only writes report artifacts below
  `/var/run/ns-audit/<report_id>/`.

Expected input directory:

```text
/var/run/ns-audit/<run-id>/
  raw_snapshot.json
  inventory.json
  findings.json
  compliance_mapping.json
  summary.json
```

Report rendering:

```bash
PYTHONPATH=/usr/share/ns-audit python3 -m ns_audit.reporting.html render \
  --input /var/run/ns-audit/latest \
  --output /var/run/ns-audit/latest/audit-report.html
```

From a repository checkout, use `PYTHONPATH=packages/ns-audit/files` instead.
The top-level CLI is expected to wrap the same renderer as:

```bash
ns-audit report --input /var/run/ns-audit/latest \
  --output /var/run/ns-audit/latest/audit-report.html
ns-audit report --input /var/run/ns-audit/latest \
  --output /var/run/ns-audit/latest/audit-report.tar.gz
```

The tarball form renders the HTML report into the same output directory and then
packages the HTML, JSON artifacts, and deduplicated log files.

## Outputs

- `audit-report.html`: HTML report with embedded CSS and links to collected logs.
- `audit-report.tar.gz`: bundle containing the HTML report, JSON artifacts, and deduplicated log copies under `logs/`.
- Existing JSON artifacts remain the source of truth:
  - `raw_snapshot.json`
  - `inventory.json`
  - `findings.json`
  - `compliance_mapping.json`
  - `summary.json`

The HTML report includes:

1. Executive Summary
2. Configuration Inventory
3. Gap Analysis & Compliance Mapping
4. Actionable Remediation Plan
5. Collected Logs
6. Evidence Appendix

## Validation

Render-time validation refuses to write HTML if known private-key, password-hash,
preshared-key, or token patterns are detected.

Validate all generated artifacts:

```bash
PYTHONPATH=/usr/share/ns-audit python3 -m ns_audit.reporting.html validate /var/run/ns-audit/latest
```

The command returns JSON:

```json
{"matches": [], "status": "ok"}
```

## Package installation notes

The package integration installs the Python modules, reporting assets, and
the optional RPCD wrapper:

- depending on `+python3-jinja2`;
- installing `files/ns_audit/reporting/*.py` as Python module files;
- installing `files/ns_audit/reporting/templates/audit-report.html.j2`;
- installing `files/ns_audit/reporting/assets/audit-report.css`;
- installing `/usr/libexec/rpcd/ns.audit` and its ACL file;
- restarting `rpcd` on live package install/removal so the endpoint is
  registered.

If a downstream branch does not have an `ns-audit` Makefile yet, add equivalent
install rules when the package skeleton is introduced.

## RPCD wrapper

The package installs `/usr/libexec/rpcd/ns.audit` and
`/usr/share/rpcd/acl.d/ns.audit.json`. The endpoint is read-only with respect to
appliance configuration: it does not write UCI configuration, call
`uci commit`, or restart services.

Methods:

- `generate`: optionally accepts `report_id`, runs the installed
  `ns_audit.cli.run(output_dir)` pipeline, and returns `report_id`,
  `output_dir`, generated artifacts (including `audit-report.html` and
  `audit-report.tar.gz`), and `summary` when readable.
- `list-reports`: lists safe report directories under `/var/run/ns-audit`.
- `get-summary`: requires `report_id` and returns the matching `summary.json`.

`report_id` must match `[A-Za-z0-9_.-]+`; if omitted by `generate`, a
timestamped ID is generated. Arbitrary output paths are not accepted.

Examples:

```bash
ubus call ns.audit generate '{}'
ubus call ns.audit generate '{"report_id":"manual-2026-01-01"}'
ubus call ns.audit list-reports '{}'
ubus call ns.audit get-summary '{"report_id":"manual-2026-01-01"}'
```

The same methods are available through `api-cli`:

```bash
api-cli ns.audit generate --data '{}'
api-cli ns.audit list-reports
api-cli ns.audit get-summary --data '{"report_id":"manual-2026-01-01"}'
```
