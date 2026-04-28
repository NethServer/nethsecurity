---
name: ns-api
description: Write or modify a NethSecurity Python RPCD API script or hook. Use when creating or updating `ns.*` RPCD API endpoints, handling UCI configuration changes, managing pre/post-commit hooks, defining ACL permissions, and documenting methods in OpenAPI 3.1.0. Covers stdin/stdout JSON protocol, error handling, naming conventions, code style, and spec file updates.
compatibility: Works with OpenCode and other Agent Skills-compatible tools. Requires Python 3.11+ and knowledge of OpenWrt rpcd framework.
metadata:
  domain: nethsecurity-apis
  type: api-development
---

## What I do

- Help create or modify `ns.*` RPCD API scripts and hook scripts
- Ensure proper stdin/stdout JSON protocol
- Verify error and validation formats
- Handle ACL JSON configuration
- Manage UCI changes and conventions
- Enforce code style via ruff
- Guide you through documenting methods in OpenAPI 3.1.0 spec

## When to use me

Use this skill when you are:
- Creating a new API at `packages/ns-api/files/ns.<name>`
- Modifying an existing API script or hook
- Changing error handling or validation logic
- Adding a pre-commit or post-commit hook
- Updating API documentation in `packages/ns-api/README.md` and `openapi.yml`

## File Structure

RPCD API scripts live at:
```
packages/ns-api/files/ns.<name>           # Executable Python script (no .py extension)
packages/ns-api/files/ns.<name>.json      # ACL definition file
packages/ns-api/files/pre-commit/          # Pre-commit hook scripts (optional)
packages/ns-api/files/post-commit/         # Post-commit hook scripts (optional)
```

## Protocol

### list

When called with `list` argument, print JSON schema of all methods:

```json
{
  "methods": {
    "method_name": {
      "params": {
        "param_name": { "type": "string", "required": true },
        "optional_param": { "type": "integer", "required": false }
      }
    }
  }
}
```

### call <method>

When called with `call <method>`, read JSON from stdin, process, write JSON to stdout:

```bash
# Example call
echo '{"param": "value"}' | ns.myapi call my_method
```

Response on success: any JSON object representing the result.

## Error Handling

**Generic error** (non-validation):
```json
{ "error": "error_code_here" }
```

Error codes must be **lowercase, snake_case, no spaces or special characters**, and translatable in the UI.

**Validation error**:
```json
{
  "validation": {
    "errors": [
      {
        "parameter": "field_name",
        "message": "error_code",
        "value": "provided_value"
      }
    ]
  }
}
```

## UCI Conventions

- **Zone names**: `ns_<zonename>` (e.g., `ns_lan`, `ns_guest`, `ns_wan`)
- **Firewall rule IDs**: prefix `ns_` with a hash suffix (e.g., `ns_206325d3`)
- **System/automated rules**: include `system_rule: true` flag
- **APIs must NOT commit UCI changes** — callers invoke `ns.commit` separately

## Hooks

Pre-commit and post-commit hooks run as part of `ns.commit commit`:

- **Pre-commit hooks**: `/usr/libexec/ns-api/pre-commit/<name>.py`
- **Post-commit hooks**: `/usr/libexec/ns-api/post-commit/<name>.py`

A failing hook does not abort the commit; errors are collected and returned in the response JSON:

```json
{ "pre_errors": ["path/to/hook.py"], "post_errors": [] }
```

## ACL File (ns.<name>.json)

Create a companion ACL file defining who can call each method. Place it at:
```
packages/ns-api/files/ns.<name>.json
```

Example:
```json
{
  "methods": {
    "method_name": {
      "roles": ["admin", "user"]
    }
  }
}
```

## Testing

Test manually on a live device using `api-cli` (default creds: root / Nethesis,1234):

```bash
# List all methods
api-cli ns.myapi list

# Call a method
api-cli ns.myapi method_name --data '{"param": "value"}'

# Via ubus
ubus call ns.myapi method_name '{"param": "value"}'

# Via curl with JWT
TOKEN=$(curl -sk https://localhost/api/login \
  --data '{"username":"root","password":"Nethesis,1234"}' | jq -r .token)
curl -sk -H "Authorization: Bearer $TOKEN" https://localhost/api/ubus/call \
  --data '{"path":"ns.myapi","method":"method_name","payload":{"param":"value"}}'
```

## Code Style

All Python code must pass ruff checks. New `.py` files are checked automatically:

```bash
ruff check packages/ns-api/files/my_script.py
ruff format --check packages/ns-api/files/my_script.py
```

Existing files are grandfathered; see `ruff.toml` in the repo root.

## SPDX Header

Every file must include:

```python
#
# Copyright (C) <YEAR> Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#
```

## Documentation

After creating or modifying any API, you must update **two** documentation files:

1. **`packages/ns-api/README.md`** — Human-friendly narrative documentation. Update with method descriptions, parameters, and examples. This is the primary reference until full migration to OpenAPI is complete.

2. **`packages/ns-api/openapi.yml`** — Machine-readable OpenAPI 3.1.0 specification. Add or update the method's path entry under `paths`. See **OpenAPI Documentation** section below.

## OpenAPI Documentation

All `ns.*` API methods are documented in a single file: **`packages/ns-api/openapi.yml`** (OpenAPI 3.1.0).

### File Location & Structure

```
packages/ns-api/openapi.yml
```

The file contains:
- **Info**: API title, description, version
- **Paths**: One entry per method under `paths:` with key format `POST /ubus/{ns.name}/{method}`
- **Components**: Reusable schemas (error responses, validation errors, etc.) under `components/schemas`

### Path Convention

Methods are mapped to OpenAPI paths using the **ubus call convention**:

```yaml
paths:
  POST /ubus/ns.firewall/list-zones:
    post:
      summary: List all firewall zones
      tags: [firewall]
      ...
```

**Why POST only?** RPCD/ubus only supports POST; all operations are methods, not REST resources.

### How Methods Are Actually Called

When a client calls an API method, the flow is:

1. **RPCD ubus call** (device-side):
   ```bash
   ubus call ns.firewall list-zones '{"filter": "all"}'
   ```

2. **HTTP via nethsecurity-api** (remote clients):
   ```bash
   # User calls this via Go API server with JWT auth
   POST /api/ubus/call
   {"path": "ns.firewall", "method": "list-zones", "payload": {"filter": "all"}}
   ```

3. **OpenAPI documentation**:
   ```yaml
   POST /ubus/ns.firewall/list-zones:
     # Describes the call above
   ```

The OpenAPI spec documents the **semantic interface**, not the HTTP transport layer.

### Request Body

Every method accepts a JSON object:

```yaml
POST /ubus/ns.firewall/list-zones:
  post:
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              filter:
                type: string
                description: Filter zones by name pattern
            required: [filter]
```

### Responses

All API responses use HTTP **200**, even for errors. The response JSON body indicates success or failure:

**Success (200):**
```json
{
  "zones": [{"name": "ns_lan", "input": "ACCEPT"}]
}
```

**API-level error (200):**
```json
{ "error": "invalid_filter" }
```

**Validation error (200):**
```json
{
  "validation": {
    "errors": [
      {
        "parameter": "filter",
        "message": "invalid_regex",
        "value": "@@@"
      }
    ]
  }
}
```

OpenAPI response definitions:

```yaml
responses:
  "200":
    description: Successful response
    content:
      application/json:
        schema:
          oneOf:
            - $ref: "#/components/schemas/ListZonesResponse"
            - $ref: "#/components/schemas/Error"
            - $ref: "#/components/schemas/ValidationError"
```

### Shared Components (Schemas)

Define reusable schemas once under `components/schemas` and reference them everywhere with `$ref`:

```yaml
components:
  schemas:
    Error:
      type: object
      required: [error]
      properties:
        error:
          type: string
          description: Error code (lowercase, snake_case)
          example: invalid_filter
      
    ValidationError:
      type: object
      required: [validation]
      properties:
        validation:
          type: object
          required: [errors]
          properties:
            errors:
              type: array
              items:
                $ref: "#/components/schemas/ValidationErrorDetail"
    
    ValidationErrorDetail:
      type: object
      required: [parameter, message, value]
      properties:
        parameter:
          type: string
          example: filter
        message:
          type: string
          description: Validation error code
          example: invalid_regex
        value:
          description: The value that failed validation
    
    Zone:
      type: object
      required: [name, input]
      properties:
        name:
          type: string
          example: ns_lan
        input:
          type: string
          enum: [ACCEPT, DROP, REJECT]
```

Then reference them in method responses:

```yaml
POST /ubus/ns.firewall/list-zones:
  post:
    responses:
      "200":
        description: List of zones
        content:
          application/json:
            schema:
              oneOf:
                - type: object
                  properties:
                    zones:
                      type: array
                      items:
                        $ref: "#/components/schemas/Zone"
                - $ref: "#/components/schemas/Error"
                - $ref: "#/components/schemas/ValidationError"
```

### Example: Adding a New Method

When you add a new method `ns.firewall get-rule`:

1. **Update README.md** with prose documentation
2. **Add entry to openapi.yml**:

```yaml
POST /ubus/ns.firewall/get-rule:
  post:
    summary: Retrieve a firewall rule by ID
    operationId: ns.firewall.get-rule
    tags: [firewall]
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              id:
                type: string
                description: Rule ID (e.g., ns_206325d3)
                example: ns_206325d3
            required: [id]
    responses:
      "200":
        description: Firewall rule details
        content:
          application/json:
            schema:
              oneOf:
                - type: object
                  properties:
                    rule:
                      $ref: "#/components/schemas/Rule"
                - $ref: "#/components/schemas/Error"
```

### Validating the Spec

To validate your OpenAPI spec:

```bash
# Using npm openapi-spec-validator (if available)
npx openapi-spec-validator packages/ns-api/openapi.yml

# Or manually verify:
# - YAML syntax is valid
# - All $ref paths exist
# - No undefined schemas in components
```

## Examples

See existing APIs in `packages/ns-api/files/`:
- `ns.commit` — core commit logic
- `ns.dashboard` — system info API
- `ns.firewall` — firewall rules API

See API documentation:
- **README**: `packages/ns-api/README.md` (human-friendly)
- **OpenAPI spec**: `packages/ns-api/openapi.yml` (machine-readable)
