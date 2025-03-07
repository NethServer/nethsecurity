# ns-binding

This package provides a way to create IP/MAC bindings in DHCP-managed networks.

## Usage

Once configured a DHCP server through the UI, you can create bindings for the interface setting a `ns_binding` option
in the DHCP server configuration. The IP/MAC bindings will be created off the static leases defined in the
configuration.

For instance, if the DHCP server is named `GREEN_1`, to add the necessary rules for the interface you must:

```bash
uci set dhcp.GREEN_1.ns_binding='1'
uci commit dhcp
reload_config
```

| Binding value | Description                                                                                   |
|---------------|-----------------------------------------------------------------------------------------------|
| `0`           | Disables the binding                                                                          |
| `1`           | Enables the soft binding, enforces the block only if the IP/MAC in the static leases mismatch |
| `2`           | Enables the hard binding, enforces block if the client is not registered in the static leases |

This will create the necessary rules to bind the IP/MAC addresses in the network based off the static leases.

From now on, the IP/MAC bindings will be automatically generated and updated whenever the `dhcp` configuration is
changed.

To disable the binding you can either remove the `ns_binding` option or set it to `0`.

```bash
uci set dhcp.GREEN_1.ns_binding='0' # or uci delete dhcp.GREEN_1.ns_binding
uci commit dhcp
reload_config
```
