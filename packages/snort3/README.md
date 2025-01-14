# snort3

Nethesis fork of [Snort](https://www.snort.org/) 3 module from [OpenWrt packages main branch](https://github.com/openwrt/packages/tree/master/net/snort3).

Changes:

- ported to OpenWrt 23.05.5
- added custom script for downloading rules, `ns-snort-rules`: the script reads configuration from UCI, then download and filter rules
- patched init.d script to implement bypass and rule suppression
- use `/var/ns-snort` as working directory
- rules are not part of backup to avoid large backups and generating a new remote backup every time rules are updated
- added new options for rules management in UCI
- log alerts as JSON files to `/var/log/snort`
- log alerts to syslog

## Quick start

Enable snort3 and configure it to run in IPS mode refer to the documentation under [ns.snort](../ns-api/README.md)

To see what has been blocked or alerted, use:
```bash
snort-mgr report -v
```

## New configuration options

The configuration is stored in UCI under the `snort` configuration file.

This package add the following extra UCI options under the `snort` section:

- `ns_policy` - the policy to use for the Snort rules. Possible values are `connectivity`, `balanced`, `security`, `max-detect`.
- `ns_alert_excluded` - if set to `1` the rules that are not part of any policy are added as alert rules, ICMP rules are always excluded because they are used for testing.
- `ns_disabled_rules` - a list of rules to disable. See [Disable rules](#disable-rules) for more details.
- `ns_suppress` - a list of suppress rules. See [Rule suppression](#rule-suppression) for more details.

This package also adds the following extra UCI options under the `nfq` section:

- `bypass_dst_v4` - bypass IDS for destination IPv4 addresses
- `bypass_src_v4` - bypass IDS for source IPv4 addresses
- `bypass_dst_v6` - bypass IDS for destination IPv6 addresses
- `bypass_src_v6` - bypass IDS for source IPv6 addresses

## Download rules

Before configuring snort3 you need to select a policy then download the rules.

To download the rules use the `ns-snort-rules` script.
The script supports the following rulesets:
- Snort [Community Rules](https://www.snort.org/downloads/#rule-downloads)
- Snort [Subscription Rules](https://www.snort.org/products#rule_subscriptions) using the Oinkcode

### Snort rules

Snort rules support 4 policies:
- `connectivity` - This policy is specifically designed to favor device performance over the security controls in the policy. It should allow a customer to deploy one of our devices with minimal false positives and full rated performance of the box in most network deployments. In addition, this policy should detect the most common and most prevalent threats our customers will experience.
- `balanced` - This policy is the default policy that is recommended for initial deployments. This policy attempts to balance security needs and performance characteristics. Customers should be able to start with this policy and get a very good block rate with public evaluation tools, and relatively high performance rate with evaluation and testing tools. It is the default shipping state of the Snort Subscriber Ruleset for Open-Source Snort.
- `security` - This policy is designed for the small segment of our customer base that is exceptionally concerned about organizational security. Customers deploy this policy in protected networks, that have a lower bandwidth requirements, but much higher security requirements. Additionally, customers care less about false positives and noisy signatures. Application control, and locked down network usage are also concerns to customers deploying this policy. It should provide maximum protection, and application control, but should not bring the network down.he most critical attacks, such as those that are directed at highly critical systems or that are likely to be used in widespread attacks.
- `max-detect` - This ruleset is meant to be used in testing environments and as such is not optimized for performance. False Positives for many of the rules in this policy are tolerated and/or expected and FP investigations will normally not be undertaken.

Above description is extracted from [official Snort FAQ](https://www.snort.org/faq/why-are-rules-commented-out-by-default).

If rules have been downloaded, the `ns-snort-rules` script will not download them again unless the `--download` argument is used.

### Disable rules

A disabled rule is a rule that is not include in the Snort ruleset.

To disable some rules use the `ns_disabled_rules` option inside UCI.
The option is a list of entries in this format: `<gid>,<sid>,<description>`.

- `gid` - the rule GID, it is a number and usually is always `1`
- `sid` - the rule SID, it is a number
- `description` - a description of the disabled rule, it is optional and can be omitted; the following characters are not allowed: `,`, ` `, `\n`;

Example: disable rules with SID 24225 and 24227:
```bash
uci add_list snort.snort.ns_disabled_rules=1,24225
uci add_list snort.snort.ns_disabled_rules=3,24227,false_positive
uci commit snort
/etc/init.d/snort restart
```

### Testing rules

Testing rules are a small set of rules that can be used to test the Snort installation.
The rules do not block any traffic but generate alerts for any type of ICMP traffic.
When enabled, testing rules exclude the official Snort rules.
To use them, no download is required.

Usage example:
```bash
ns-snort-rules  --testing
uci commit snort
/etc/init.d/snort restart
```

## Bypass IPS

The IPS support bypass for destination or source IP addresses. Both IPv4 and IPv6 are supported.

The following options are supported inside `snort.nfq` section:
- `bypass_dst_v4` - bypass IDS for destination IPv4 addresses
- `bypass_src_v4` - bypass IDS for source IPv4 addresses
- `bypass_dst_v6` - bypass IDS for destination IPv6 addresses
- `bypass_src_v6` - bypass IDS for source IPv6 addresses

Usage example:
```bash
uci add_list snort.nfq.bypass_src_v4=192.168.100.23
uci add_list snort.nfq.bypass_src_v4=192.168.100.28
uci commit snort
/etc/init.d/snort restart
```
## Rule suppression

A suppression rule is a rule that is ignored by Snort for a specific IP address or CIDR.

To add a suppress rule use the `ns_suppress` option inside UCI `snort.snort` section.
Each suppress rule is a comma separated list of values: `gid,sid,direction,ip,description`:

- `gid` - the rule GID, it is a number and usually is always `1`
- `sid` - the rule SID, it is a number
- `direction` - the direction of the rule, it can be `by_src` or `by_dst`
- `ip` - the IPv4 address or CIDR to suppress
- `description` - a description of the suppress rule, it is optional and can be omitted; the following characters are not allowed: `,`, ` `, `\n`;

Example:
```bash
uci add_list snort.snort.ns_suppress='1,1234,by_src,1.2.3.4,very_bad'
uci add_list snort.snort.ns_suppress='1,1234,by_dst,8.8.8.8,noisy_rule'
```
