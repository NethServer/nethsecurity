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

The UI's Apply button calls `ns.commit commit` with the output of `ubus call uci changes`, so every staged change goes through the hooks, then gets committed, then `reload_config` fires the procd triggers.

## Pick the layer

| Need | Put it in |
|---|---|
| Logic on UCI data: validation, building sections, lookups, anything an API, script or hook could reuse | the library, with tests |
| Expose an operation to the UI/controller | an API method that parses input, calls the library and prints JSON |
| Reload/restart your own service when its config changes | procd `service_triggers` on that config, see the `ns-background-work` skill |
| Keep **another** config consistent with a change (delete references to a removed interface, rewrite a derived option) | pre-commit hook |
| Side effect after commit that has no owning service to trigger (timezone symlink, invalidating tokens) | post-commit hook |
| Periodic or boot-time work | script + cron/procd, see `ns-background-work` |

Start from the bottom of the stack: if procd can reload the service from its trigger, don't write a hook. Hooks run on every Apply, for every change, so each one costs time on every save.

## Library (`python3-nethsec`)

Read the existing module before adding to it. Functions take an `EUci` as first argument, raise `utils.ValidationError(parameter, message, value)` for bad input and `ValueError` for other errors, and call `uci.save(config)` without committing. `nethsec.dpi` is the reference for a recent, tested module.

- **New module**: create `src/nethsec/<module>/__init__.py` **and** add `'nethsec.<module>'` to the `packages=[...]` list in `setup.py`. The list is written by hand, so a module missing there is silently left out of the wheel and the import fails on the device.
- **Tests**: `tests/test_<module>.py` with pytest. Build an `EUci` on a temp dir with the configs the code needs, as `tests/test_dpi.py` does:

  ```python
  @pytest.fixture
  def e_uci(tmp_path: pathlib.Path) -> EUci:
      conf_dir = tmp_path.joinpath('conf')
      conf_dir.mkdir()
      save_dir = tmp_path.joinpath('save')
      save_dir.mkdir()
      conf_dir.joinpath('foo').write_text(foo_db)
      return EUci(confdir=conf_dir.as_posix(), savedir=save_dir.as_posix())
  ```

  Mock `subprocess.run` (pytest-mock's `mocker`) for anything that touches the system, like service reloads.
- **Run**: `cd packages/python3-nethsec && ./test.sh`. It builds a podman image with Python 3.13 and the OpenWrt `libubox`/`ubus`/`uci` libraries and runs pytest. CI runs the same on changes under `packages/python3-nethsec` (`.github/workflows/python3-nethsec-tests.yml`).
- **Version**: don't bump `PKG_VERSION`/`PKG_RELEASE`, here or in any other package. Versions are bumped at the end, before the release. `ns-api` depends on `+python3-nethsec` without a version, so an API that needs a new library function ships in the same release as the library change.

New library code must pass ruff like any new Python file (see the `python-nethsecurity` skill).

## API (`ns.*`)

Keep it a dispatcher: parse stdin, call the library, map exceptions to the error format, print JSON. `packages/ns-api/files/ns.dpi` is the model. Protocol, ACLs and docs are in the `ns-api` skill.

APIs stage changes and let `ns.commit` apply them. Committing and restarting from inside an API method is a last resort, for the few operations that by design or by user interaction need an immediate effect (registration, HA setup, adding storage). Avoid it whenever the change can wait for Apply, and say it in the method's README entry when you can't.

## Commit hooks

### How `ns.commit` runs them

Read `packages/ns-api/files/ns.commit` before writing one. Verified on a device (Python 3.13.9):

- Every executable file in the directory runs, in no guaranteed order (`glob.glob`, unsorted).
- **`*.py` files are `exec()`'d inside `ns.commit`'s `execute_hook()` function**, not run as a process:
  - `changes` is in scope. It's a dict `{config: [[op, section, option, value], ...]}`, e.g. `{"system": [["set", "cfg01e48a", "hostname", "fw1"]]}`.
  - Mutating `changes` sticks and reaches the commit and the post-commit hooks. Rebinding it (`changes = {...}`) is lost.
  - Imports at hook top level aren't visible inside functions the hook defines (`NameError`). Keep the hook flat, or import inside the function, or better, call a library function.
  - `print()` writes into `ns.commit`'s stdout and corrupts the API's JSON response.
  - `sys.exit()` raises `SystemExit`, which the `except Exception` around the hook doesn't catch: it aborts `ns.commit` halfway through the commit.
  - A raised exception is logged to syslog and the path is added to `pre_errors`/`post_errors`. The commit goes on anyway.
- Other executables run as a subprocess with `changes` as JSON on stdin. Output is ignored and they can't change `changes`.
- After the pre-commit hooks, `ns.commit` commits every config that is a key of `changes`. That's how a pre-commit hook gets its own edits committed.
- The whole call runs under rpcd's exec timeout (`rpcd.@rpcd[0].timeout`, 300 s on the device), together with every other hook.

### Writing one

The feature package ships its own hook (as `ns-threat_shield` does), so it exists only when the feature is installed:

```makefile
	$(INSTALL_DIR) $(1)/usr/libexec/ns-api/pre-commit
	$(INSTALL_BIN) ./files/ns-foo-pre-commit.py $(1)/usr/libexec/ns-api/pre-commit/ns-foo.py
```

Pre-commit template, modeled on `ns-threat_shield/files/configure-adblock-devices.py`:

```python
#!/usr/bin/python3

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Keep ns-foo.config.devices aligned with the devices of the configured zone.

# `changes` is injected by ns.commit when the hook is exec'd.
if 'network' in changes or 'firewall' in changes or 'ns-foo' in changes:  # noqa: F821
    from euci import EUci
    from nethsec import foo

    uci = EUci()
    if foo.sync_devices(uci):  # library: computes, compares, uci.save('ns-foo'), returns True if changed
        if 'ns-foo' not in changes:  # noqa: F821
            changes['ns-foo'] = {}  # noqa: F821
```

- Return early unless a config you care about is in `changes`.
- Compare before writing, so an unrelated Apply doesn't generate new changes.
- `uci.save()` and add the config to `changes`. Never `uci.commit()` in a pre-commit hook.
- Put the logic in the library and test it there. The hook stays a few lines of glue.
- No `print()`, no `sys.exit()`, no `subprocess` with `shell=True` on values from `changes` or UCI.
- In a post-commit hook, don't restart a service that has a procd trigger: `reload_config` runs right after and reloads it.

## Don't copy

Most of these are workarounds that couldn't be avoided at the time. Don't extend the pattern to new code.

- `ns-api/files/post-commit/restart-cron.py`: when `snort` changed it reads `changes['firewall']` (`KeyError` without firewall changes), and runs `["/etc/init.d", "cron", "restart"]`. Cron is managed through `crontab -` now, see `ns-background-work`.
- `ns-threat_shield/files/adjust-banip.py`: `uci.get(...)` returns `'0'`, which is truthy, so it never stops a disabled banIP; it stop/starts banIP on every network change; bare `except:`.
- `ns-threat_shield/files/configure-banip-wans.py`: calls `uci.commit('banip')` inside a pre-commit hook. Save and add the config to `changes` instead.
- Fat APIs: `ns.ovpnrw`, `ns.ha`, `ns.devices`, `ns.threatshield` keep their logic inline, with no tests. New logic goes in the library.

## Verify on a device

```sh
uci set ns-foo.config.x=1                    # stage a change
ubus call uci changes                        # what the UI would send
api-cli ns.commit commit --data "$(ubus call uci changes)"
logread -e ns.commit -e python               # hook exceptions land in syslog
```

A non-empty `pre_errors`/`post_errors` in the response names the failing hook.

## Sources

- `packages/ns-api/files/ns.commit`, `packages/ns-api/README.md` (ns.commit section), `docs/design/index.md` ("Commit hooks")
- UI side: https://github.com/NethServer/nethsecurity-ui/blob/main/src/stores/standalone/uciPendingChanges.ts
- `packages/python3-nethsec/README.md`, `setup.py`, `test.sh`, `tests/`
- procd triggers and `reload_config`: `ns-background-work` skill, `references/procd-init.md`
