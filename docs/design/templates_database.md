---
layout: default
title: Templates database
parent: Design
---

# Templates database

## Introduction

The templates database can be used to implement the following scenarios.

Installation templates: It involves creating configuration templates for firewalls that can be easily replicated in similar scenarios.

Automatic configuration of known services.
Currently, the known services include:
- OpenVPN RoadWarrior: this action allows changing the listening port or adding a new instance
- OpenVPN tunnel: this action allows changing the listening port or adding a new instance
- Wireguard: this action allows changing the listening port or adding a new instance
- Dedalo hotspot: enable/disable the service
- Nginx: change management UI port

Configuration wizards:
- Run a first configuration with 3 zones (lan, wan, and guest): this wizard automatically creates the zone for guest.
- Run a first configuration with strict mode (where all traffic is closed from lan to wan): enable access to a list of well-known services.

## Record types

The `templates` database contains some special sections which can be used as template to generate new sections inside the real UCI configuration files. This is a list of currently supported files.

### Service groups
        
Record type: `template_service_group`

Description: this section defines service groups, which are collections of multiple network services. Each service group has a name and includes various services with their corresponding ports and protocols. It generates a rule for each protocol (`udp` or `tcp`) where all services are grouped.

Options:
- option `name`: specifies the name or description of the service group, it can be used inside the UI
- list `services`: represents a list of network services included in the service group. 
      Each service is defined with a string in the form `<port>/<protocol>/<name>' like `80/tcp/HTTP`

Example:
```
config template_service_group 'ns_web_secure'
	option name 'Secure web navigation'
	list services '80/tcp/HTTP'
	list services '443/tcp/HTTP Secure'
	list services '53/udp/DNS'
```

### Zones

Record type: `template_zone`

Description: this section defines network zones, each with a distinct purpose and network policies. Zones specify how traffic is handled, such as allowing or dropping incoming and outgoing packets.

Contains all options from UCI `zone`, plus the following:
- list `forwardings`: a list of forwardings to create for this zone, see below
- option `ns_description`

Example:
```
config template_zone 'ns_guest'
	option name 'guest'
	option forward 'DROP'
	option input 'DROP'
	option output 'ACCEPT'
	option ns_description 'Guest network with Internet access'
	list forwardings 'ns_guest2wan'

config template_forwarding 'ns_guest2wan'
	option src 'guest'
	option dest 'wan'
```

### Forwarding rules

Record types: `template_forwarding`

Description: this section defines forwarding rules that determine how traffic is forwarded between different zones. Each forwarding rule specifies a source zone and a destination zone.

See zones for an example.

### Rules

Record type: `template_rule`

Description: this section defines a template rule that applies to specific traffic between zones. The rule sets conditions for packet acceptance or rejection based on the source and destination zones, ports, and protocols. The placeholders `__PORT__` and `__PROTO__` are intended to be replaced with actual port numbers and protocols.

Example:
```
config template_rule 'ns_test_rule'
	option name 'Test-rule'
	option src 'wan'
	option dest 'blue'
	option dest_port '__PORT__'
	option proto '__PROTO__'
	option target 'ACCEPT'
	option enabled '1'
```
