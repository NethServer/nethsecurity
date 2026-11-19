---
name: ns-code-placement
description: Decide where new NethSecurity logic goes — the `python3-nethsec` library, an `ns.*` RPCD API, a standalone script, a pre/post-commit hook run by `ns.commit`, or a procd reload trigger — and write it there correctly, with library tests. Use whenever a task adds or moves Python logic, adds an API method, needs "something to happen when the user saves/applies", reacts to a UCI change, keeps two configs consistent, touches `packages/python3-nethsec`, `/usr/libexec/ns-api/pre-commit`, `/usr/libexec/ns-api/post-commit`, `ns.commit`, or when the user asks "where should this code live", "should this be a hook", "add it to the library", even if they don't name a layer.
metadata:
  domain: nethsecurity-packages
  type: architecture
---

## The layers

| Layer | Lives in | Runs when |
|---|---|---|
| `nethsec` library | `packages/python3-nethsec/src/nethsec/<module>/__init__.py` | imported by everything else |
| `ns.*` API | `packages/ns-api/files/ns.<name>` → `/usr/libexec/rpcd/ns.<name>` | UI/controller call, stages UCI changes |
| `ns.commit` pre-commit hook | `/usr/libexec/ns-api/pre-commit/<name>.py` | on Apply, before the UCI commit |
| `ns.commit` post-commit hook | `/usr/libexec/ns-api/post-commit/<name>.py` | on Apply, after the commit, before `reload_config` |
| procd reload trigger | `service_triggers` in the package's init script | when `reload_config` sees the config changed |
| Script | `/usr/sbin/<name>` or `/usr/libexec/<pkg>/` | cron, init script, hotplug, another script |

Apply flow: the UI sends the staged changes to `ns.commit commit`, which runs the hooks around the commit, then `reload_config`.

## Pick the layer

| Need | Put it in |
|---|---|
| Logic on UCI data: validation, building sections, lookups, anything an API, script or hook could reuse | the library, with tests |
| Expose an operation to the UI/controller | an API method that parses input, calls the library and prints JSON |
| Reload/restart your own service when its config changes | procd `service_triggers` on that config, see the `ns-background-work` skill |
| Keep **another** config consistent with a change (delete references to a removed interface, rewrite a derived option) | pre-commit hook |
| Side effect after commit that has no owning service to trigger (timezone symlink, invalidating tokens) | post-commit hook |
| Periodic or boot-time work | script + cron/procd, see `ns-background-work` |

Start from the bottom of the stack: if procd can reload the service from its trigger, don't write a hook. Hooks run on every Apply, so each one costs time on every save.

## Library (`python3-nethsec`)

Read the existing module before adding to it, and follow its conventions. `nethsec.dpi` is the reference for a recent, tested module.

- **New module**: also add it to the hand-written `packages=[...]` list in `setup.py`, or it won't be installed.
- **Tests**: `tests/test_<module>.py` with pytest, using an `EUci` on a temp dir like the `e_uci` fixture in `tests/test_dpi.py`. Mock `subprocess.run` for anything that touches the system.
- **Run**: `cd packages/python3-nethsec && ./test.sh`.
- **Version**: don't bump it. An API needing a new library function ships in the same release as the library change, since `ns-api` doesn't pin the `python3-nethsec` version.

New library code must pass ruff (see the `python-nethsecurity` skill).

## API (`ns.*`)

Keep it a dispatcher: parse stdin, call the library, map exceptions to the error format, print JSON. `packages/ns-api/files/ns.dpi` is the model. Protocol, ACLs and docs are in the `ns-api` skill.

APIs stage changes and let `ns.commit` apply them. Commit and restart from an API only when the operation needs an immediate effect (registration, HA setup, adding storage), and say so in the method's README entry.

## Commit hooks

Read `execute_hook` in `packages/ns-api/files/ns.commit` before writing one: `.py` hooks are `exec()`'d in-process with `changes` in scope, so in a `.py` hook:

- mutate `changes`, never rebind it;
- don't rely on top-level imports inside functions you define; keep the hook flat and call the library;
- no `print()`, no `sys.exit()`.

Model a pre-commit hook on `packages/ns-threat_shield/files/configure-adblock-devices.py`, shipped by the feature's own package.

- Return early unless a config you care about is in `changes`.
- Compare before writing, so an unrelated Apply doesn't generate new changes.
- `uci.save()` and add the config to `changes`. Never `uci.commit()` in a pre-commit hook.
- Put the logic in the library and test it there. The hook stays a few lines of glue.
- In a post-commit hook, don't restart a service that has a procd trigger.

## Don't copy

Hooks that commit, restart services on every change or index `changes` without checking the key, and APIs that keep their logic inline without tests. New logic goes in the library.

## Verify on a device

```sh
ubus call uci changes                        # what the UI would send
api-cli ns.commit commit --data "$(ubus call uci changes)"
```

A non-empty `pre_errors`/`post_errors` in the response names the failing hook; the exception is in `/var/log/messages`.

## Sources

- `packages/ns-api/files/ns.commit`, `packages/ns-api/README.md` (ns.commit section), `docs/design/index.md` ("Commit hooks")
- UI side: https://github.com/NethServer/nethsecurity-ui/blob/main/src/stores/standalone/uciPendingChanges.ts
- `packages/python3-nethsec/README.md`, `setup.py`, `test.sh`, `tests/`
- procd triggers and `reload_config`: `ns-background-work` skill
