# netify-flow-actions

A Multi-Action to Multi-Target Flow Detection Plugin for The Netify DPI Agent.

The [code](https://gitlab.com/netify.ai/private/nethesis/netify-flow-actions) of this plugin is closed-source,
but it has been be made available to the community thanks to [Netify](https://www.netify.ai/).

## Overview

The Flow Actions Plugin for the Netify DPI Agent applies user-defined criteria to new flow detections in near real-time.  Matching flows are passed to one or more Action Targets for further processing.

The main purpose of the Flow Actions plugin is to provide a high-speed interface to other Operating System components that can empower policy enforcement, traffic control, and/or network auditing/logging applications.

The plugin provides a modular design where target types can be disabled at compile time to provide the smallest footprint possible.

The Actions, Targets, and global settings are configured by a JSON file which can be reloaded at any time by sending a reload (`HUP`) signal to the main Netify Agent process.

Action criteria are configured using either a simple or advanced syntax.  Simple syntax selects flows by application, protocol, or category IDs or tags only. Advanced syntax executes user-defined [Flow Criteria](#Flow%20Criteria) expressions.  These expressions can operate over all available flow metadata to precisely control how individual flows are evaluated.

## Actions

Actions set the criteria that will be evaluated against each flow detection.  The evaluation happens after the DPI processing of the flow has completed, and subsequently again if the flow's metadata has been updated.  If the action's criteria matches, the specified action targets are called.

Each action must reference at least one target.  There is no limit to the number of targets an action can reference.

### Action Properties

- Property: `enabled`
  Type: `boolean`
  Default: `true`
  
  Action's can be individually enabled or disabled.

- Property: `interface`
  Type: `string`
  Default: `*`
  
  Filter flows by interface or interface role.  Specify an interface name, such as: `eth0`, or the interface's role, which can be either `lan` or `wan`.

- Property: `criteria`
  Type: `string`
  
  The criteria property is mandatory and defines either the application, protocol, or category ID/tag to filter on, or a full expression which can evaluate a flow using any of the available metadata.  See the [Flow Criteria](#Flow%20Criteria) section below for more details.

- Property: `exemptions`
  Type: `string`
  
  Exemptions are optional and can be thought of as the inverse of `criteria`.  Usually they are employed to filter out certain hosts by `address`, however they can also be configured with an `expression` for more advanced exemption filtering.  See the [Exemptions](#Exemptions) section below for more details.

- Property: `targets`
  Type: `array`
  
  An array of one or more target names to call when a flow matches the action criteria.

### Example

A single action, "`games`", operating on flows originating or destined for all `lan` interfaces.  Flows must be identified as belonging to the `games` category.  Flows that have a source or destination address of `192.168.1.1` are exempt, as are flows that have been identified with an application tag of `netify.playstation`.  The action will pass matching flows to four `targets` (not defined here).

```json
    "actions": {
        "games": {
            "enabled": true,
            "interface": "lan",
            "criteria": "category == 'games';",
            "targets": [
                "log.games",
                "ipset.games",
                "ctlabel.games",
                "nftset.games"
            ],
            "exemptions": [
                "192.168.1.1",
                "app == 'netify.playstation';"
            ]
        }
    },
```

## Targets

Targets are called by actions when a given flow matches the specified criteria.  Any number of actions can reference any other number of targets.  Targets perform the tasks that their type implements, such as adding an address to an IP set or adding  matching flow metadata to a log file.

There are currently four distinct action target types.  **Note**: only a subset of these may be available, depending on licensing options and/or platform capabilities.

- **log**
  The log target will write periodic JSON-formatted log files ~~containing a user-defined list of flow metadata fields~~.

- **ipset**
  The ipset target adds to or updates user-defined ipsets that can then be referenced by various third-party firewall, QoS/QoE, and routing applications.

- **nftset**
  As with the ipset action target, the nftset target provides the same capabilities but using the native nftables `set` interface.

- **ctlabel**
  The ctlabel action target can be configured to apply user-defined Netfilter conntrack labels to matching flows.

### Target Properties: log

- Property: `interval`
  Type: `unsigned`
  Default: `60`
  
  The interval of time, in seconds, between log writes.  A new file is created for each interval only if new flow data was collected (empty log files will not be created).

- Property: `path`
  Type: `string`
  Default: `/tmp`
  
  The full path of the desired log directory.  New log files will be created here.

- Property: `prefix`
  Type: `prefix`
  Default: `netify-flow-actions`
  
  The log filename prefix.  New log files will begin with this identifier.

- Property: `suffix`
  Type: `string`
  Default: `.json`
  
  The log filename suffix and/or extension.  New log files will end with this identifier.

#### Example

```json
        "log.games": {
            "target_type": "log",
            "target_enabled": false,
            "prefix": "netify-games",
            "interval": 60
        },
```

### Target Properties: ipset

IP Sets are high-speed Linux kernel tables that are used to store lists of network addresses.  More information about IP Sets can be found on the project website,[^ipset_ref1]  or from the `ipset` man page.[^ipset_ref2]

- Property: `set_name`
  Type: `string`
  
  The IP set name.

- Property: `set_family`
  Type: `string`
  Default: `*`
  
  The IP family of the set.  Values: `ipv4`, `ipv6`, or `*` for both.  An IP family suffix will automatically be appended to the set's name.  For example: `social-media.v4`

- Property: `type`
  Type: `string`
  Default: `hash:ip`
  
  The IP set type.  IP set types are comprised of a storage method and a datatype. Valid storage methods are: ~~`bitmap`~~, `hash`, and ~~`list`~~.  The currently supported list of types are: `ip`, `ip,port`, `ip,port,ip`, and `mac`.

- Property: `max_elements`
  Type: `unsigned`
  Default: `65536`
  
  The maximum number of elements that can be stored in the sets.

- Property: `ttl`
  Type: `unsigned`
  Default: `0`
  
  The Agent will automatically notify the Plugin when a flow expires.  The Plugin will then attempt to remove the matching element.  However, elements can be set to auto-expire after a specified number of seconds by configuring the `ttl` property.  Generally it is recommended to always set a `ttl`, to a fairly high value, such as `900` (15 minutes), to ensure the set doesn't grow too large. Setting the `ttl` to `0` will disable auto-expiry.

- Property: `skb_mark`
  Type: `string`
  
  Firewall mark as a hexadecimal string.  When any of the `skb_*` options are set, and an appropriate firewall rule is present (a `SET` netfilter target with the `--map-set` argument), packets that match this IP set will have their corresponding socket buffer options set.

- Property: `skb_mask`
  Type: `string`
  
  Corresponding mask to a specified `skb_mark`, as a hexadecimal string.  If `skb_mark` is set, without a mask, the default value is: `0xffffffff`

- Property: `skb_prio`
  Type: `string`
  
  Traffic control `tc` class.  The option has the format of: `MAJOR:MINOR`.

- Property: `skb_queue`
  Type: `unsigned`
  
  Hardware queue ID, unsigned integer.
  
- Property: `managed`
  Type: `boolean`
  Default: `false`
  
  When `managed` mode is enabled, the plugin will attempt to create the IP set if it doesn't exist.  **NOTE**: If you change the plugin's configuration, and existing sets are present, you must manually destroy them in order for any new settings to take effect.

- Property: `flush_on_create`
  Type: `boolean`
  Default: `false`
  
  When `managed` mode is enabled and `flush_on_create` is enabled, the IP set will be flushed (cleared), on start-up if it exists.

- Property: `flush_on_destroy`
  Type: `boolean`
  Default: `false`
  
  When enabled, `flush_on_destroy` will flush (clear) the IP set on shutdown.  This option does not depend on `managed` mode being enabled.

#### Example

```json
        "ipset.games": {
            "target_type": "ipset",
            "set_name": "nfa.games",
            "set_family": "ipv4",
            "type": "hash:ip,port,ip",
            "ttl": 60,
            "flush_on_destroy": true
        },
```
  
[^ipset_ref1]: IP Set website: https://ipset.netfilter.org/
[^ipset_ref2]: IP Set man page: https://ipset.netfilter.org/ipset.man.html

### Target Properties: nftset

The plugin supports nftables sets (NFT sets).  The implementation generally follows the same configuration as the ipset plugin, with a few additions/differences.  For more information, refer to the nftables website,[^nfset_ref1] and the nftables Sets wiki.[^nfset_ref2]

- Property: `table_name`
  Type: `string`
  Default: `nfa`
  
  The table name that the NFT set is a member of.

- Property: `table_family`
  Type: `string`
  Default: `inet`
  
  The family of the table.

- Property: `set_name`
  Type: `string`
  
  The mandatory name of the NFT set.

- Property: `set_family`
  Type: `string`
  Default: `*`
  
  The IP family of the set.  Valid values are `ipv4`, `ipv6`, or `*` for both.

- Property: `type`
  Type: `array`
  
  The set type is defined as an array of flow metadata fields.  Rules that reference the NFT set must do so using the same field order that are defined here.  The supported fields are:
  
  - `local_mac`
  - `other_mac`
  - `local_addr`
  - `other_addr`
  - `local_port`
  - `other_port`
  - `mark`
  - `interface`

- Property: `max_elements`
  Type: `unsigned`
  Default: `65536`
  
  The maximum number of elements that can be stored in the NFT set.

- Property: `ttl`
  Type: `unsigned`
  Default: `0`
  
  The Agent will automatically notify the Plugin when a flow expires.  The Plugin will then attempt to remove the matching element.  However, elements can be set to auto-expire after a specified number of seconds by configuring the `ttl` property.  Generally it is recommended to always set a `ttl`, to a fairly high value, such as `900` (15 minutes), to ensure the set doesn't grow too large. Setting the `ttl` to `0` will disable auto-expiry.
  
- Property: `managed`
  Type: `boolean`
  Default: `false`
  
  When `managed` mode is enabled, the plugin will attempt to create the NFT set if it doesn't exist.  **NOTE**: If you change the plugin's configuration, and existing sets are this present, you must manually destroy them in order for any new settings to take effect.

- Property: `flush_on_create`
  Type: `boolean`
  Default: `false`
  
  When `managed` mode is enabled and `flush_on_create` is enabled, the NFT set will be flushed (cleared), on start-up if it exists.

- Property: `flush_on_destroy`
  Type: `boolean`
  Default: `false`
  
  When enabled, `flush_on_destroy` will flush (clear) the NFT set on shutdown.  This option does not depend on `managed` mode being enabled.

#### Example

```json
        "nftset.games": {
            "target_type": "nftset",
            "set_name": "nfa.games",
            "set_family": "ipv4",
            "type": [
                "local_addr",
                "ip_proto",
                "other_port",
                "other_addr"
            ],
            "ttl": 60,
            "flush_on_create": true
        },
```

[^nfset_ref1]: nftables website: https://netfilter.org/projects/nftables/
[^nfset_ref2]: nftables Sets wifi: https://wiki.nftables.org/wiki-nftables/index.php/Sets

### Target Properties: ctlabel

The Netfilter Conntrack API provides an interface module for applying user-defined labels (bits) on a per-flow basis.

Flow labels can be examined using the `conntrack` command from the `conntrack-tools` package.  For example: `conntrack -L -o labels`

- Property: `labels`
  Type: `array`
  
  The `labels` array contains one or more label bits or label names.  All `labels` will be applied to all flows that reach the target.

- Property: `auto_label`
  Type: `boolean`
  
  The target has the ability to parse prefixed label names from `connlabels.conf` which, when enabled, will automatically apply them to matching flows.
  
  The syntax for the label names is:
  
  `<type>-<application/protocol>`
  
  The `<type>` prefix can be either `a` for application, or `p` for protocol.  A hyphen delimits the `<type>` from the `<protocol/application>` name.  **NOTE**: The application and protocol names must have all forward-slashes replaced by hyphens.  An example translation:
  
  `Google/Meet/Duo -> a-google-meet-duo`

- Property: `log_errors`
  Type: `boolean`
  
  By default, errors are not logged to reduce processing overhead.  When the Agent is in debug mode and `log_errors` is enabled, error messages will be displayed for flows that could not be labelled.

#### Initialization of CT Labels

Before CT labels can be applied to flows, rules must exist which reference the `connlabel/ct label` extension.

If this isn’t done, any user-space application that attempts to label a CT flow will fail with the `ENOSPC` (Error No Space) error code.  

There is almost no documentation regarding this requirement, other than a commit message from 2012:

"The extension is enabled at run-time once '-m connlabel' netfilter rules are added." [^connlabel_init]

Therefore, it is required to insert a set of “dummy rules” on firewall initialization.  Once these “dummy rules” have been loaded, the appropriate kernel space is allocated for connection tracking labels.

[^connlabel_init]: CT Labels initialization requirement: https://lwn.net/Articles/524593/

Example iptables rules:
```shell
modprobe xt_connlabel

for c in INPUT OUTPUT FORWARD; do \
  iptables -t mangle -A $c -m connlabel --label dpi-complete \
    -m comment --comment "Dummy; init CT labels";\
done
```

#### Example

```json
        "ctlabel.games": {
            "target_type": "ctlabel",
            "labels": [
                "netify-games"
            ]
        },
```

### Default Target Properties

Almost all target properties can have their default values overridden in the `target_defaults` section of the configuration file.  For example, the default values for the `prefix`, `suffix`, and `interval` properties of the `log` target could be overridden with an entry such as:

```json
    "target_defaults": {
        "log": {
            "path": "/var/log",
            "suffix": ".json",
            "interval": 3600
        }
    },
```

### Global Target Properties

Some target types have global properties that can be set to override their default values.  The global properties are set in the `target_globals` section of the configuration file.  For example:

```json
    "target_globals": {
        "ctlabel": {
            "max_bits": 127,
            "connlabel_conf": "/etc/xtables/connlabel.conf"
        }
    },
```

###### ctlabel

The `ctlabel` target type has two global properties:

- Property: `max_bits`
  Type: `unsigned`
  Default: `127`
  
  The number of label bits supported by the Netfilter Conntrack labels module.  There is a hard limit of 127 label bits that can be set.  This limit can be raised by adjusting the `XT_CONNLABEL_MAXBIT` constant in the `nf_conntrack_labels.h` kernel header file.  If the limit has been changed, set `max_bits` to match the new value.

- Property: `connlabel_conf`
  Type: `string`
  Default: `/etc/xtables/connlabel.conf`
  
  The connlabel "map" file assigns label bits to human-readable label names.  Label names are alphanumeric strings that may also contain spaces and hyphens.  The file format is one label bit followed by white-space and the label name per line.  For example:
  
  `1 nfa-games`
  
## Flow Criteria

Flow Criteria is specified using the `criteria` key.  The criteria can be defined using a simple or advanced syntax.

If creating an action where all flows pass the criteria filter is needed, the `criteria` key can also be set to the "all" wildcard asterisk:

`criteria: "*"`

An interface filter and/or exemptions can still be used to filter out flows when using a wildcard for the Flow Criteria.

### Simple Syntax

Simple Flow Criteria begin with a type prefix followed by either an application or protocol ID.  Simple expressions can also be inverted using the NOT operator: `!`

For example, to match Facebook as an application by tags or ID:

- Criteria: `ai:facebook`
- Criteria: `ai:netify.facebook`
- Criteria: `ai:119`

You can also use numeric IDs.  For example, to match all flows that are NOT DNS:

- Criteria: `!pi:5`

Valid prefixes include:

- Prefix: `ai`: Application tag or ID.
- Prefix: `ac`: Application category.
- Prefix: `pi`: Protocol tag or ID.
- Prefix: `pc`: Protocol category.

### Advanced Syntax (Expressions)

Expressions are syntactically similar to C-based programming languages.  They operate on flow criteria, for example: `local_ip`, `remote_port`, `protocol`, `application_category`, and so on.

Expressions must be terminated by a semicolon and all `string` types must be enclosed within single-quotes: `'...'`

#### Comparison Operators

- Equal to: `==`
- Not equal to: `!=`
- Greater than: `>`
- Greater than or equal to: `>=`
- Less than: `<`
- Less than or equal to: `<=`

#### Boolean Operators

- NOT: `! <expression>`
- AND: `&&`, `and`
- OR: `||`, `or`

#### Precedence

- Group expressions to control evaluation precedence.  Compare groups with boolean operators: `(<expressions>)`

#### Flow Criteria

- Criteria: `ip_version`
  Type: `unsigned`
  
  IP version.  Valid values are `4` for IPv4, and `6` for IPv6.

- Criteria: `ip_protocol`
  Type: `unsigned`
  
  Internet protocol ID.  Example, `6` for TCP. [^ip_protocols]

- Criteria: `ip_nat`
  Type: `boolean`
  
  When supported (Linux-only) and for external (WAN) interfaces only.  The NAT flag is set if the flow was found in the connection tracking table.

- Criteria: `vlan_id`
  Type: `unsigned`
  
  Virtual LAN (VLAN) ID. [^vlan]

- Criteria: `other_type`
  Type: `constant`
  
  The "other" address constants are:
  
  `other_local`: The address is a local address.
  `other_remote`: The address is from a remote (WAN) network.
  `other_multicast`: The "other" address is a multicast address.
  `other_broadcast`: The "other" address is a broadcast address.
  `other_unknown`: The address type could not be determined.
  `other_unsupported`: The method to determine the address type is unsupported.
  `other_error`: An error occurred while trying to determine the "other" address type.

- Criteria: `local_mac`, `other_mac`
  Type: `string`
  
  Local or other MAC address in the format: `01:02:03:ab:cd:ef`

- Criteria: `local_ip`, `other_ip`
  Type: `string`
  
  Local or other IP address in either IPv4 or IPv6 format depending on `ip_version`.

- Criteria: `local_port`, `other_port`
  Type: `unsigned`
  
  Local or other port address when applicable, depending on `ip_protocol`.

- Criteria: `origin`
  Type: `constant`
  
  The `origin` end-point of the flow (which side, local or other, initiated the packet flow).  Possible values:
  
  `origin_local`: The "local" end-point initiated the flow.
  `origin_remote`: The "other" end-point initiated the flow.
  `origin_unknown`: The origin could not be reliably determined.

- Criteria: `tunnel_type`
  Type: `constant`
  
  If the flow contains encapsulated data which could be identified and extracted (not encrypted), such as GTP, the `tunnel_type` will be set according to the following values:
  
  `tunnel_none`: No encapsulation detected.
  `tunnel_gtp`: GTP encapsulation detected (GPRS).[^gprs]

- Criteria: `fwmark`
  Type: `unsigned`
  
  When available and on supported platforms (Linux-only), the connection tracking mark value.

- Criteria: `detection_guessed`
  Type: `boolean`
  
  If the protocol could not be determined via packet analysis, an attempt to "guess" the protocol is made using various methods such as the port address(es).

- Criteria: `app`, `application`
  Type: `string`
  
  The detected application tag.[^netify_applications] The list of installed application signatures can be viewed locally using the following command:
  
  `# netifyd --dump-apps`

- Criteria: `app_id`, `application_id`
  Type: `unsigned`
  
  The detected application can also be referenced by numeric ID.  The full list of local application signature IDs can be found using the same command above.

- Criteria: `app_category`, `application_category`
  Type: `string`
  
  The detected application category.  The full list of possible categories can be viewed using the following command:
  
  `# netifyd --dump-category application`

- Criteria: `proto`, `protocol`
  Type: `string`
  
  The detected protocol name.[^netify_protocols]  The comparison is case-insensitive.  The list of currently supported protocols can be viewed using the following command:
  
  `# netifyd --dump-protocols`

- Criteria: `proto_id`, `protocol_id`
  Type: `unsigned`
  
  The detected protocol ID.  The list of valid protocol IDs can be viewed using the same command above.

- Criteria: `proto_category`, `protocol_category`
  Type: `string`
  
  The detected protocol category.  The full list of possible categories can be viewed using the following command:
  
  `# netifyd --dump-category protocol`

- Criteria: `dom_category`, `domain_category`
  Type: `string`
  
  If one or more custom domain category lists have been configured, matches from them can be explicitly tested for using `domain_category`.

- Criteria: `cat`, `category`
  Type: `string`
  
  The `category` criteria is a hybrid evaluation where both the `application_category` and the `domain_category` are tested, eliminating the need to write two statements.

- Criteria: `risks`
  Type: `string`
  
  Test if the risk name was detected in the flow's list of `risks`.  Repeat for multiple risks.  The full list of risks can be viewed using the following command:
  
  `# netifyd --dump-risks`

- Criteria: `ndpi_risk_score`
  Type: `unsigned`
  
  The risk score as detected by the nDPI library. [^ndpi_risks]

- Criteria: `ndpi_risk_client`, `ndpi_risk_server`
  Type: `unsigned`
  
  The individual nDPI risk score for the client-side and server-side, respectively.

- Criteria: `detected_hostname`
  Type: `string`
  
  The detected hostname, which can be extracted from a variety of protocols.  For example, TLS SNI. [^tls_sni]
  
  It is also possible to specify an extended regular expression[^regex] here, when supported.  To use a regular expression, add the `rx:` prefix.  For example, to match all domains that end with `google.com`:
  
  `rx:.*google.com`

- Criteria: `ssl_version`, `ssl_cipher`
  Type: `unsigned`
  
  For detected TLS flows, the SSL/TLS version and negotiated cipher can be tested.  The values are usually represented using hexadecimal values, for example TLS v1.3 would be: `0x0303`[^ssl_tls]

[^ip_protocols]: IP Protocols: https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
[^vlan]: Virtual LAN: https://en.wikipedia.org/wiki/VLAN
[^gprs]: GPRS: https://en.wikipedia.org/wiki/GPRS_Tunnelling_Protocol
[^netify_applications]: Netify Applications: https://www.netify.ai/resources/applications
[^netify_protocols]: Netify Protocols: https://www.netify.ai/resources/protocols
[^ndpi_risks]: nDPI Risks: https://gitlab.com/netify.ai/public/netify-agent-libs/ndpi/-/blob/master/doc/flow_risks.rst
[^ssl_tls]: SSL/TLS: https://en.wikipedia.org/wiki/Transport_Layer_Security
[^tls_sni]: TLS Server Name Indication (SNI): https://en.wikipedia.org/wiki/Server_Name_Indication
[^regex]: Extended Regular Expressions: https://en.wikipedia.org/wiki/Regular_expression#Standards

#### Example Expressions

1. Unclassified applications and protocols:
   
   `app_id == 0 || proto_id == 0;`

2. All HTTP/S traffic to a remote server:
   
   `protocol == 'http/s' && other_type == other_remote;`

3. All internal VoIP traffic by category:
   
   `other_type == other_local && (app_category == 'voip' || protocol_category == 'voip');`
   
## Exemptions

It is often desirable to exclude some network addresses such as the gateway or other critical infrastructure, especially when there may be a block or drop policy in place.  Exemptions can also simplify advanced criteria expressions by pre-filtering flows that are of the wrong protocol or are otherwise not candidates for the action target(s).

Exemptions can simply be an address (IPv4 or IPv6), or they can be a Flow Criteria Expression described above.

### Action Exemptions

Action Exemptions operate within the context of an action.  To use them, add an `exemptions` section with of an `array` of exemption expressions (addresses or flow criteria).

### Global Exemptions

Global Exemptions are specified and operate the same way as Action Exemptions, but their scope is global.  To use them, add an `exemptions` section to the top-level of the JSON configuration.  The Global Exemptions `array` is the ideal location to filter critical infrastructure and traffic from entering policy controls, like matching a `DROP` target.

The following example would prevent the gateway (`192.168.1.1`) and any `DNS` detected traffic flows from being considered:

```json
    "exemptions": [
        "192.168.1.1",
        "protocol == 'dns';"
    ]
```

## Example Configuration

```json
{
    "version": 1,
    "targets": {
        "log.games": {
            "target_type": "log",
            "target_enabled": false,
            "prefix": "netify-games",
            "interval": 60
        },
        "ipset.games": {
            "target_type": "ipset",
            "set_name": "nfa.games",
            "set_family": "ipv4",
            "type": "hash:ip,port,ip",
            "ttl": 60,
            "flush_on_destroy": true
        },
        "ctlabel.games": {
            "target_type": "ctlabel",
            "labels": [
                "netify-games"
            ]
        },
        "nftset.games": {
            "target_type": "nftset",
            "set_name": "nfa.games",
            "set_family": "ipv4",
            "type": [
                "local_addr",
                "ip_proto",
                "other_port",
                "other_addr"
            ],
            "ttl": 60,
            "flush_on_create": true
        }
    },
    "target_defaults": {
        "log": {
            "path": "/tmp",
            "prefix": "netify-flow-actions",
            "suffix": ".json",
            "interval": 300
        },
        "ipset": {
            "set_family": "*",
            "ttl": 600
        },
        "nftset": {
            "table_name": "netify",
            "table_family": "inet",
            "size":  65535,
            "ttl": 300,
            "managed": true,
            "flush_on_destroy": true
        }
    },
    "target_globals": {
        "ctlabel": {
            "max_bits": 127,
            "connlabel_conf": "/etc/xtables/connlabel.conf"
        }
    },
    "actions": {
        "games": {
            "enabled": true,
            "interface": "*",
            "criteria": "category == 'games';",
            "targets": [
                "log.games",
                "ipset.games",
                "ctlabel.games",
                "nftset.games"
            ],
            "exemptions": [
                "127.0.0.1",
                "app == 'netify.playstation';"
            ]
        }
    },
    "exemptions": [
        "192.168.1.1",
        "protocol == 'dns';"
    ]
}
```

## References

