# snort3

Nethesis fork of [Snort](https://www.snort.org/) 3 module from [OpenWrt packages main branch](https://github.com/openwrt/packages/tree/master/net/snort3).

Changes:

- ported to OpenWrt 23.05.5
- added custom script for downloading rules
- small patch to init.d script to make sure that snort3 is started even if no rules are present
- use `/var/ns-snort` as working directory
- rules are not part of backup to avoid large backups and generating a new remote backup every time rules are updated

## Quick start

Enable snort3 and configure it to run in IPS mode, use only a limited number of rules from the official Snort ruleset and download them:
```bash
echo '{"enabled": true, "set_home_net": true, "include_vpn": false}' | /usr/libexec/rpcd/ns.snort call setup
ns-snort-rules --official-download --official-policy connectivity
uci commit snort
/etc/init.d/snort restart
```

To disable snort3:
```bash
echo '{"enabled": false}' | /usr/libexec/rpcd/ns.snort call setup
uci commit snort
/etc/init.d/snort stop
```

To see what has been blocked or alerted, use:
```bash
snort-mgr report -v
```

## Download rules

Before configuring snort3 you need to download the rules.

To download the rules use the `ns-snort-rules` script.
The script supports the following rulesets:
- Snort [Community Rules](https://www.snort.org/downloads/#rule-downloads)
- Snort Registered Rules using the Oinkcode
- [Emerging Threats rules](https://rules.emergingthreats.net/)


### Snort rules

Snort rules support 3 policies:
- `connectivity` - This policy is specifically designed to favor device performance over the security controls in the policy. It should allow a customer to deploy one of our devices with minimal false positives and full rated performance of the box in most network deployments. In addition, this policy should detect the most common and most prevalent threats our customers will experience.
- `balanced` - This policy is the default policy that is recommended for initial deployments. This policy attempts to balance security needs and performance characteristics. Customers should be able to start with this policy and get a very good block rate with public evaluation tools, and relatively high performance rate with evaluation and testing tools. It is the default shipping state of the Snort Subscriber Ruleset for Open-Source Snort.
- `security` - This policy is designed for the small segment of our customer base that is exceptionally concerned about organizational security. Customers deploy this policy in protected networks, that have a lower bandwidth requirements, but much higher security requirements. Additionally, customers care less about false positives and noisy signatures. Application control, and locked down network usage are also concerns to customers deploying this policy. It should provide maximum protection, and application control, but should not bring the network down.he most critical attacks, such as those that are directed at highly critical systems or that are likely to be used in widespread attacks.

Above description is extracted from [official Snort FAQ](https://www.snort.org/faq/why-are-rules-commented-out-by-default).

When downloading the ules you must specify the policy to use.

Example: download official Snort rules, and setup the policy to `connectivity`:

```bash
ns-snort-rules --official-download --official-policy connectivity
```

### Emerging Threats rules

Emerging Threats rules come with multiple rulesets.
For more info on available ruleset see the [official documentation](https://tools.emergingthreats.net/docs/ETPro%20Rule%20Categories.pdf).

Example: download Emerging Threats rules, and setup the alert and block policy to `default`:
```bash
ns-snort-rules --et-download --et-alert=default --et-block=default
```

The `et-alert` and `et-block` takes a comma separated list of rulesets.
Both arguments are optional, if none of them is specified no rules will be enabled.
Categories specified in `et-alert` will be enabled as alert rules, and categories specified in `et-block` will be enabled as block rules.
The special value `default` will enable a safe set of rules for the specified policy.

To list all available rulesets in the Emerging Threats rules use `--et-list` argument.

Accordingly to ET [metadata guidelines](https://community.emergingthreats.net/t/signature-metadata/96), only rules with
metadata `deployment Perimeter` and `signature_severity Critical` are enabled as block rules.
Other block rules are disabled.

### Disable rules

To disable some rules use the `--disable-rules` argument.
The argument takes a comma separated list of SIDs to disable.

Example: disable rules with SID 1 and 2:
```bash
ns-snort-rules --official-download --official-policy connectivity --disable-rules 1,2
```

### Download rules examples

Download both Snort and Emerging Threats rules.
Set the policy for Snort rules to `connectivity` and enable only the default Emerging Threats rules:
```bash
ns-snort-rules --official-download --official-policy balanced --et-download --et-block=default
```

Download only Snort rules with `security` policy:
```bash
ns-snort-rules --official-download --official-policy security
```

Download only Emerging Threats rules with all default rules for alert and block:
```bash
ns-snort-rules --et-download --et-alert=default --et-block=default
```

Download only Emerging Threats rules, block just `emerging-ciarmy` category, disable all alert rules:
```bash
ns-snort-rules --et-download --et-block=emerging-ciarmy
```

At the end of the download, always restart the snort service:
```bash
/etc/init.d/snort restart
```

Use only the testing rules, just alert for all ICMP traffic:
```bash
ns-snort-rules --testing
```