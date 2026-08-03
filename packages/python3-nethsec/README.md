# python3-nethsec

Python3 library for NethSecurity.

Requirements:

* Python3
* [pyuci](https://gitlab.nic.cz/turris/pyuci)

[![Run tests](https://github.com/NethServer/nethsecurity/actions/workflows/python3-nethsec-tests.yml/badge.svg?branch=main)](https://github.com/NethServer/nethsecurity/actions/workflows/python3-nethsec-tests.yml)

## Reference

Library reference: [https://dev.nethsecurity.org/apidocs/python3-nethsec/](https://dev.nethsecurity.org/apidocs/python3-nethsec/).

## Usage

The `nethsec` library is composed by the following sub-packages:

- utils
- firewall

Usage example:
```python
from euci import EUci
from nethsec import firewall

u = EUci()
firewall.add_to_lan(u, 'tunrw')
firewall.add_service(u, 'openvpn_rw', '1194', ['udp', 'tcp'])
firewall.apply(u)
```

## Documentation

Documentation can be generated using [pydoctor](https://pydoctor.readthedocs.io) or [pydoc](https://docs.python.org/3/library/pydoc.html).

Documentation is automatically generated at each new commit on master branch.
Online doc is hosted on [GitHub pages](https://dev.nethsecurity.org/apidocs/python3-nethsec/).

Generate doc using pydoctor:
```
pip install -U pydoctor
pydoctor  \
  --project-name=python3-nethsec \
  --project-url=https://github.com/nethserver/python3-nethsec \
  --make-html \
  --html-output=./apidocs \
  --project-base-dir="$(pwd)" \
  --docformat=restructuredtext \
  --intersphinx=https://docs.python.org/3/objects.inv \
  ./src/nethsec
```

Generate doc using pydoc:
```bash
cd src
python3 -m pydoc nethsec.firewall
python3 -m pydoc nethsec.utils
```

## Build

Execute:
```bash
python3 -m pip install --upgrade build
python3 -m pip install wheel
python3 -m build
```

## Tests

Tests run inside a podman container (see `Containerfile`) based on Python 3.13,
with the OpenWrt `libubox`/`ubus`/`uci` C libraries and the test dependencies
baked in.

To start the tests, first make sure to have podman installed. Then, from this
package directory (`packages/python3-nethsec`) execute:
```
./test.sh
```

`test.sh` rebuilds the test image from the `Containerfile` on every run, so no
registry access is needed and a `Containerfile` change is always picked up.
Podman's layer cache keeps the rebuild fast when nothing changed.

## Packaging in NethSecurity

This library is built into the NethSecurity image as the `python3-nethsec`
OpenWrt package. The `nethsec` wheel is built from the local `./src` tree.

When releasing a new version, bump `PKG_VERSION` (and `PKG_RELEASE`) in `Makefile`.
