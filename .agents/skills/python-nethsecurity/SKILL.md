---
name: python-nethsecurity
description: Write or modify Python scripts for NethSecurity packages. Use when creating new Python scripts, configuring package build systems, or writing utilities. Covers shebang, license headers, extension handling, ruff compliance, available modules, and UCI commit conventions.
compatibility: Works with OpenCode and other Agent Skills-compatible tools. Requires Python 3.11+ and understanding of NethSecurity build system.
metadata:
  domain: nethsecurity-python
  type: development
---

## What I do

- Help create or modify Python scripts for NethSecurity packages
- Ensure correct shebangs, license headers, and file extensions
- Validate ruff compliance for new files
- Advise on available stdlib and third-party modules
- Enforce UCI commit conventions (no direct `u.commit()` from API scripts)
- Guide on Makefile installation patterns for executables vs. data files

## When to use me

Use this skill when you are:
- Creating a new Python script in `packages/ns-*/files/`
- Writing a utility, hook, or standalone script
- Configuring a Makefile to install Python executables
- Checking available modules for dependency decisions
- Ensuring license headers and style compliance

## File Structure & Extensions

### Regular scripts (API methods, utilities, tools)
```
packages/ns-<name>/files/<scriptname>.py    # Source file with .py extension
```

Install with `INSTALL_BIN` (sets executable bit):
```makefile
$(INSTALL_BIN) ./files/<scriptname>.py $(1)/usr/sbin/<scriptname>
# Result on device: /usr/sbin/<scriptname> (no extension)
```

### Pre-commit and post-commit hooks
```
packages/ns-api/files/pre-commit/<hookname>.py     # Keeps .py extension
packages/ns-api/files/post-commit/<hookname>.py    # Keeps .py extension
```

Hooks are installed at:
```
/usr/libexec/ns-api/pre-commit/<hookname>.py
/usr/libexec/ns-api/post-commit/<hookname>.py
```

### Data files (YAML configs, JSON templates, etc.)
```
packages/ns-<name>/files/<datafile>.json           # No execution needed
```

Install with `INSTALL_DATA` (no executable bit):
```makefile
$(INSTALL_DATA) ./files/<datafile>.json $(1)/etc/ns-<name>/
```

## Shebang & License Header

Every Python source file **must** start with:

```python
#!/usr/bin/python3
#
# Copyright (C) <YEAR> Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# ... rest of file
```

**Important notes:**
- Shebang is **fixed path** `#!/usr/bin/python3` (never `/usr/bin/env python3`)
- License header must appear in all authored source files (Python, shell, Go, etc.)
- Year should match the current year or the year the file was created

## Entry Point Pattern

### Regular scripts (utilities, API methods)

**Must use `if __name__ == "__main__":` guard:**

```python
#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

import sys
import json

def main():
    # Your logic here
    pass

if __name__ == "__main__":
    main()
```

### Pre/Post-commit hooks

**Must NOT use `if __name__ == "__main__":` guard.** Hooks execute in an injected context with a global `changes` dict:

```python
#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from euci import EUci

# No __main__ guard; code runs immediately in injected context
u = EUci()
# changes dict is automatically provided
for section in changes.get('firewall', {}).get('rule', []):
    # Process changes
    pass
```

## Available Modules

### Standard Library (verified on Python 3.11)
- `subprocess`, `json`, `os`, `sys`, `logging`, `argparse`, `dataclasses`
- `pathlib`, `asyncio`, `sqlite3`, `syslog`, `tempfile`, `shutil`
- `re`, `hashlib`, `base64`, `socket`, `urllib.parse`, `xml.etree.ElementTree`
- `datetime`, `time`, `uuid`, `enum`, `typing`, `itertools`

### Third-party (installed on device)
- **`euci`** — Enhanced UCI library (preferred over `uci` module)
- **`nethsec`** — NethSecurity Python utility library (used by all API scripts)
- **`uci`** — Raw UCI module (use EUci instead when possible)
- **`requests`**, `urllib3` — HTTP client libraries
- **`yaml`** — YAML parsing
- **`jinja2`**, `markupsafe` — Templating
- **`passlib`** — Password hashing
- **`pyotp`** — One-time password (TOTP/HOTP)
- **`semver`** — Semantic versioning
- **`certifi`**, `chardet`, `idna` — Certificate/encoding utilities

## UCI & Commit Conventions

### Key rule: APIs must NOT commit UCI changes

**Golden rule:** Never call `u.commit()` from an API script or standalone utility. Only the `ns.commit` RPCD call commits UCI changes.

**Exception:** Migration scripts (running at first boot) may call `u.commit()` directly since they execute before the API layer.

```python
# ❌ WRONG - API or utility calling u.commit()
from euci import EUci
u = EUci()
u.set("firewall", "zone", "input", "ACCEPT")
u.commit()  # ← Never do this in API context

# ✅ CORRECT - API returning changes, caller handles ns.commit
from euci import EUci
u = EUci()
u.set("firewall", "zone", "input", "ACCEPT")
# No commit; callers invoke ns.commit separately via RPCD
return {"status": "ok"}
```

### UCI Naming Conventions

- **Zones**: `ns_<zonename>` (e.g., `ns_lan`, `ns_guest`, `ns_wan`)
- **Firewall rule IDs**: `ns_<hash>` (e.g., `ns_206325d3`)
- **System/automated rules**: include `system_rule: true` flag in rule config

## Code Style & Ruff

All new Python files must pass ruff checks:

```bash
ruff check packages/ns-<name>/files/my_script.py
ruff format --check packages/ns-<name>/files/my_script.py
```

**Configuration:** See `ruff.toml` in the repo root (Python 3.11, line-length 120).

**Existing files:** Grandfathered in via `extend-exclude` in `ruff.toml`. You are not required to fix them, but may do so incrementally.

**New files:** Must be clean from the start. Do not add them to the exclude list.

## Testing

Test Python scripts on a live device or in the container:

```bash
# Interactive shell in build container
./build-nethsec.sh bash

# Inside container, test a script with specific imports
cd /home/user/nethsecurity
python3 packages/ns-myapi/files/my_script.py
```

## Dependencies in Makefiles

When adding external Python dependencies, declare them in the package Makefile:

```makefile
define Package/ns-myapi
  TITLE:=My API
  DEPENDS:=+python3 +python3-requests +python3-yaml
endef
```

All common modules (`euci`, `nethsec`, `requests`, `yaml`, etc.) are already available as dependencies in the build system.

## Example: Simple Utility Script

```python
#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

import sys
import json
from euci import EUci

def list_zones():
    """List all network zones."""
    u = EUci()
    zones = u.get_list("network", "", "interface", {})
    return {"zones": list(zones.keys())}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "missing_action"}))
        sys.exit(1)
    
    action = sys.argv[1]
    if action == "list":
        print(json.dumps(list_zones()))
    else:
        print(json.dumps({"error": "unknown_action"}))

if __name__ == "__main__":
    main()
```

## Example: Pre-commit Hook

```python
#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

from euci import EUci

u = EUci()

# Validate firewall changes before commit
for section in changes.get("firewall", {}).get("rule", []):
    if not u.get("firewall", section, "target"):
        raise Exception(f"Rule {section} missing target field")
```

## Importing from python3-nethsec

The `nethsec` library provides common utilities:

```python
from nethsec import api
from nethsec.firewall import get_zones

zones = get_zones()
```

Refer to the [python3-nethsec repository](https://github.com/NethServer/python3-nethsec) for available APIs.
