# High Availability Firewall

This package contains a set of scripts to configure a high-availability firewall.
Configured with keepalived, it will provide a failover mechanism between two nodes.

Requirements:

- Two nodes must have the same network devices
- Nodes must be connected to the same LAN

Limitations:

- Primary LAN interface must be named 'lan' in both firewalls
- On LAN interfaces, only static IPv4 addresses are supported
- Extra packages such as NUT are not supported
- rsyslog configuration is not synced: if you need to send logs to a remote server, you must use the controller
- After the first synchronization, the backup node will have the same hostname as the primary node

Supported WAN configurations:

- static IPv4 and IPv6
- DHCP IPv4
- physical interfaces
- bond interfaces over physical interfaces
- bridges over physical interfaces
- VLANs over physical interfaces
- VLANs over bond interfaces
- VLANs over bridges
- PPPoE over physical interfaces
- PPPoE over VLANs

The following features are supported:

- Firewall rules, including port forwarding
- DHCP and DNS server
- SSH server (dropbear)
- OpenVPN RoadWarrior and tunnels
- IPsec tunnels (strongwan)
- WireGuard tunnels
- Static routes
- QoS (qosify)
- Multi-WAN (mwan3)
- DPI rules
- Netifyd informatics configuration
- Threat shield IP (banip)
- Threat shield DNS (adblock)
- Reverse proxy (nginx)
- ACME certificates
- Users and objects database
- Netmap
- Flashstart
- SNMP server (snmpd)
- NAT helpers
- Dynamic DNS (ddns)
- SMTP client (msmtp)
- Backup encryption password
- Controller connection and subscription (ns-plug)
- Active connections tracking (conntrackd)
- Dedalo hotspot

## Configuration

The setup process configures the following:
- check if requirements are met both on the primary and backup nodes
- configures HA traffic on lan interface
- sets up keepalived with the virtual IP, a random password and a public key for the synchronization
- configures dropbear to listen on port `65022`: this is used to sync data between the nodes using rsync, only
  key-based authentication is allowed
- configures conntrackd to sync the connection tracking table

In this example:
- `primary_node_ip` is the primary node, with LAN IP `192.168.100.238`
- `backup_node_ip` is the backup node, with LAN IP `192.168.100.239`
- the virtual IP is `192.168.100.240`

Before starting, follow these steps:

- power on the backup node, access the web interface and set a static LAN IP address, in this example `192.168.100.239`:
- then, power on the primary node, access the web interface and set a static LAN IP address, in this example `192.168.100.238`

These IP addresses are used to access the nodes directly, even if the HA cluster is disabled.
You can consider these IP addresses as management IP addresses.

When the HA cluster is enabled, all the configuration will be automatically synchronized to the backup node, except for the network configuration.
If you need to change the network configuration, do it on the primary node then follow the instructions below to adapt the HA configuration to the new network configuration.

The package provides a script to ease the configuration of the HA cluster, without accessing directly the APIs.
The script is named `ns-ha-config`. Usage syntax is:
```
ns-ha-config <action> [<option1> <option2>]
```

### Check local requirements

First, check the status of the primary node:
```
ns-ha-config check-primary-node [lan_interface]
```

If the `lan_interface` is not specified, the script will use the default value `lan`.

It will check the following:

- the LAN interface must be configured with a static IP address
- if a DHCP server is running
  - the `Force DHCP server start` option must be enabled
  - the DHCP option `3: router` must be set and configured with the virtual IP address (e.g. `192.168.100.240`)
  - the DHCP option `6: DNS server` must be set; you can set it to the virtual IP address or to the DNS server of your choice:
    just make sure that the DNS server is reachable from the clients even if the primary node is down

Hotspot is supported, but with the following requirements:
- the backup node must have the exact same network devices as the primary node
  As an example, if the primary node has a VLAN interface named `vlan10`, the backup node must have the same VLAN interface with the same name.
  Otherwise, the hotspot will not work after a switchover.
- the hostspot can run only on a physical interface or on a VLAN interface

To ensure hotspot functionality, the MAC address of the interface on the master node where the hotspot is configured will be copied to the corresponding
interface on the backup node during failover.
Also note that active sessions, which are saved in RAM, will be lost during a switchover, so the clients will need to re-authenticate if auto-login is disabled.

### Check remote requirements

Then, check the status of the backup node:
```
ns-ha-config check-backup-node <backup_node_ip> [lan_interface]
```

It will check the following:

- the backup node must be reachable via SSH on port 22 with root user
- the LAN interface must be configured with a static IP address

In case of a switchover, the backup node will take over the WAN interface of the primary node but
if there is no WAN interface configured on the backup node with the same name, the UI will
show an unknown device.

Execute:
```
ns-ha-config check-backup-node <backup_node_ip>
```

The script will require to enter the password of the root user for the backup node.

You can also pass the SSH directly to standard input:
```
echo "password" | ns-ha-config check-backup-node <backup_node_ip>
```

Example with interactive password:
```
ns-ha-config check-backup-node 192.168.100.239
```

Example with password on standard input:
```
echo Nethesis,1234 | ns-ha-config check-backup-node 192.168.100.239
```

### Initlialize the primary node

If the requirements are met, you can initialize the primary node, please note that the Virtual IP (only) must be written in CIDR notation.
```
ns-ha-config init-primary-node <primary_node_ip> <backup_node_ip> <virtual_ip> [lan_interface]
```

The script will:

- initialize keepalived with the virtual IP
- configure conntrackd
- generate a random password and public key for the synchronization
- configure dropbear to listen on port `65022` and allow only key-based authentication

Example:
```
ns-ha-config init-primary-node 192.168.100.238 192.168.100.239 192.168.100.240/24
```

### Initialize the backup node

If the requirements are met, you can initialize the backup node:
```
ns-ha-config init-backup-node
```
The script will ask for the password of the root user for the backup node.

You can also pass the SSH directly to standard input:
```
echo "password" | ns-ha-config init-backup-node
```

Example with password on standard input:
```
echo Nethesis,1234 | ns-ha-config init-backup-node
```

At this point, the primary node and the backup node are configured to talk to each other
using the LAN interface.
The virtual IP of the LAN will switch between the two nodes in case of failure.

It's now time to configure additional interfaces, starting at least with the WAN interface.

### Configure the WAN interfaces

The system does not require any special configuration for the WAN interfaces.
Just configure them inside the `Interfaces and devices` page and they will be automatically managed
by the HA scripts.

### Configure LAN interfaces

Extra LAN interfaces can be added to the HA configuration
only if they are already configured both on the primary and backup nodes with static IP addresses.
Just like the main LAN interface.

Use this command also to add other local interfaces, such as guest ot DMZ interfaces.

You can add extra interfaces using the same command:
```
ns-ha-config add-lan-interface <primary_node_ip> <backup_node_ip> <virtual_ip_address>
```

When adding a LAN interface, the following requirements must be met:
- the LAN interface must be configured with a static IP address on both nodes
- if a DHCP server is running
  - the `Force DHCP server start` option must be enabled
  - the DHCP option `3: router` must be set and configured with the virtual IP address (e.g. `192.168.100.240`)
  - the DHCP option `6: DNS server` must be set; you can set it to the virtual IP address or to the DNS server of your choice:
    just make sure that the DNS server is reachable from the clients even if the primary node is down

Example:
```
ns-ha-config add-lan-interface 192.168.200.185 192.168.200.186 192.168.200.190/24
```

### Remove an interface

To remove an interface from the HA configuration, use the following command:
```
ns-ha-config remove-interface <interface>
```

Example:
```
ns-ha-config remove-interface lan2
```

The script will:
- check if the given interface is already configured as HA interface
- remove the interface from keepalived configuration
- remove all virtual routes, if present
- remove the interface from the backup node
- move the virtual IP address to the original interface

### Configure a VIP (alias) on a LAN interface

Aliases are extra virtual IP addresses that can be added to an interface.
When an alias is added to a WAN interface, no special configuration is required:
the alias will be automatically kept in sync between the two nodes.

When an alias is added to a LAN interface, it's a bit different:

- if the alias must be kept in sync between the two nodes, it must be added to the HA configuration as
  VIP (Virtual IP) and not as a traditional alias
- if the alias must be bound to a node and does not need to be kept in sync,
  it must be configured normally using UCI or the web interface (not recommended)

To add an alias, use the following command:
```
ns-ha-config add-vip <interface> <vip_address>
```

Example:
```
ns-ha-config add-vip lan 192.168.100.66/24
```


The VIP will appear in the network configuration of the backup node only when the node
becomes primary.

### Remove a VIP (alias) from a LAN interface

To remove a VIP (alias), use the following command:
```
ns-ha-config remove-vip <interface> <alias>
```

The script will remove the VIP from keepalived configuration.

Example:
```
ns-ha-config remove-vip lan2 192.168.122.66/24
```

## Show current configuration

You can show the current configuration of the HA cluster:
```
ns-ha-config show-config
```

It will output something like this:
```
Current configuration

Interfaces:
  Interface: lan, Device: br-lan, Virtual IP: 192.168.100.240/24

Aliases:
  Interface: lan, Virtual Alias IP: 192.168.100.66/24

-----------------------------------------------------------------

Not configured

Interfaces:
  Interface: wan, Device: eth1 
```

## Check the status

You can check the status of the HA cluster at any time.
Just execute:
```
ns-ha-config status
```

Just after the initialization, the script will return something like this:
```
Status: enabled
Role: primary
Current State: master
Last Sync Status: SSH Connection Failed
Last Sync Time: Fri Apr 18 13:07:08 UTC 2025
```

The first synchronization will take up to 10 minutes and will be done in the background.
After few minutes, the status should be like this:
```
Status: enabled
Role: primary
Current State: master
Last Sync Status: Successful
Last Sync Time: Mon Jun  9 07:21:15 UTC 2025

Virtual IPs:
  lan_ipaddress: 192.168.100.240/24 (br-lan)

Keepalived Statistics:
  advert_rcvd: 0
  advert_sent: 1730
  become_master: 1
  release_master: 0
  packet_len_err: 0
  advert_interval_err: 0
  ip_ttl_err: 0
  invalid_type_rcvd: 0
  addr_list_err: 0
  invalid_authtype: 0
  authtype_mismatch: 0
  auth_failure: 0
  pri_zero_rcvd: 0
  pri_zero_sent: 0

```

## Alerting

The cluster sends alerts **only** if the machine has a valid subscription.

Available alerts are:

- `ha:sync:failed`: raised if the file synchronization fails; it usyally means that the backup node is not reachable.
  This alerts is raised only on the primary node.
- `ha:primary:failed`: raised if the primary node is down; it means that there was a switchover.
  This alerts is raised with FAILURE state on the backup node when it takes over the virtual IP address; 
  the alert is raised with OK state on the primary node when it comes back online.

## Connecting to the backup node

Since the backup node does not have access to the Internet, you have 2 different ways to connect to it:

- directly using the static LAN IP address configured at the beginning
- from the primary node using SSH

To connect to the backup node from the primary, use the following command:
```
ns-ha-config ssh-remote
```

The scripts uses special SSH port 65022 and keepalived SSH private key: it is meant to be used on the primary node when the HA cluster
is already configured.

## Upgrading the backup node

The backup node does not have access to the Internet, so you need to upgrade it manually using an image file.

From the primary node, use the following command:
```
ns-ha-config upgrade-remote [<image>]
```

If `image` is not specified, the script will download the latest image and install it on the backup node.
If `image` is specified, the script will use the given image file to upgrade the backup node.

## Troubleshooting and logs

Since the name of the backup host is replaced with the name of the primary host, it's hard to distinguish between the two nodes
when connecting via SSH.
To avoid confusion, when the HA cluster is enabled, the bash prompt will show the keepalived status using:
- `P` for primary node
- `S` for secondary (or backup) node

Prompt example for primary node:
```
root@NethSec [P]:~#
```

Prompt example for secondary node:
```
root@NethSec [S]:~#
```

A normal configuration synchronization will look like this on the secondary node:
```
Apr 23 09:48:49 NethSec dropbear[8098]: Child connection from 192.168.100.238:37350
Apr 23 09:48:49 NethSec dropbear[8098]: Pubkey auth succeeded for 'root' with ssh-rsa key SHA256:LDIBFC6gFHmIAUqdEWVi62ca/EUxZI7/08m2d76/hcQ from 192.168.100.238:37350
Apr 23 09:48:49 NethSec dropbear[8098]: Exit (root) from <192.168.100.238:37350>: Exited normally
Apr 23 09:48:49 NethSec dropbear[8100]: Child connection from 192.168.100.238:37356
Apr 23 09:48:49 NethSec dropbear[8100]: Pubkey auth succeeded for 'root' with ssh-rsa key SHA256:LDIBFC6gFHmIAUqdEWVi62ca/EUxZI7/08m2d76/hcQ from 192.168.100.238:37356
Apr 23 09:48:49 NethSec sudo:     root : PWD=/root ; USER=root ; COMMAND=/usr/bin/rsync --server -nlogDtprRe.iLfxCIvu --log-format=X . /usr/share/keepalived/rsync
Apr 23 09:48:49 NethSec dropbear[8100]: Exit (root) from <192.168.100.238:37356>: Exited normally
```

All sync events are logged in the `/var/log/messages` file, you can filter them using the following command:
```
grep ns-rsync.sh /var/log/messages
```

When a new interface has been added to the HA configuration, the backup node will log it inside `/var/log/messages` file.
The log will look like this:
```
Apr 23 06:51:38 NethSec ns-ha: Importing network configuration: {"device": "eth1", "proto": "dhcp", "record_type": "interface", "record_id": "wan"}
```

To see active keepalived configuration, execute:
```
cat /tmp/keepalived.conf
```

### Debugging

The ns-ha configuration script is a shell script that can be debugged using the `-x` option.
Example:
```
bash -x ns-ha-config <action> [<option1> <option2>]
```

It's also possible to enable debugging for the keepalived service.
To enable it, execute on the primary node:
```
uci set keepalived.primary.debug=1
uci commit keepalived
reload_config
```

Then, search for `Keepalived_vrrp` in the `/var/log/messages` file.

## Maintenance

The HA cluster can be disabled at any time.
But be careful: if you disable the primary node first, the backup node will take over the virtual IP address.

The static LAN IPs configured at the beginning can be considered management IPs.
These IPs are always accessible and can be used to manage the nodes directly, regardless of the HA cluster status.

### Maintance of the backup node

To disable the HA cluster, use the following command on the **backup** node:
```
/etc/init.d/keepalived stop
```

Proceed with the primarytenance of the backup node, then re-enable the HA cluster:
```
/etc/init.d/keepalived start
```

### Maintenance of the primary node

When the primary node is disabled, the backup node will take over the virtual IP address.
To disable the HA cluster, use the following command on the **primary** node:
```
/etc/init.d/keepalived stop
```

Proceed with the primarytenance of the primary node, then re-enable the HA cluster:
```
/etc/init.d/keepalived start
```

The primary node will take over the virtual IP address again.

## Disable and enable the HA cluster

After the configuration, the HA is enabled by default.

To disable the HA cluster, use the following command on the **primary** node:
```
ns-ha-config disable
```

The script will:
- connect to the backup node and disable keepalived
- disable keepalived on the primary node

To enable again the HA cluster, use the following command on the **primary** node:
```
ns-ha-config enable
```

## Reset the configuration

To reset the configuration, use the following command:
```
ns-ha-config reset
```

The script will:
- stop and disable keepalived
- stop and disable conntrackd
- remove the configuration files
- cleanup dropbear configuration including the SSH keys

The script will not change the network configuration of the nodes.
You can access them using the static LAN IP addresses configured at the beginning and manage them as standalone nodes.

## How it works

### Overview

The High Availability system creates an active-passive cluster with two nodes: a primary (master) node that handles all traffic and configuration, and a backup node that remains synchronized but inactive until failover occurs. The system uses three main components:

- **Keepalived**: Manages virtual IP addresses and handles failover between nodes using VRRP protocol
- **Conntrackd**: Synchronizes active connection tracking tables to maintain session continuity during failover
- **File Synchronization**: Uses rsync over SSH to keep configuration files synchronized between nodes

All configuration changes must be performed on the primary node, which automatically propagates them to the backup node. In case of primary node failure, the backup node takes over the virtual IP addresses and becomes the active node, ensuring service continuity.

### File synchronization and restoration

The synchronization system operates through two distinct phases: file transfer and hotplug event to restore files.

#### File transfer phase (rsync): from primary to backup

The primary node runs a specialized rsync script (`/etc/keepalived/scripts/ns-rsync.sh`) that:
- Exports network configurations (WireGuard interfaces, IPsec interfaces, routes, and hotspot MAC addresses) to `/etc/ha` using `/usr/libexec/ns-ha-export` script
- Lists all files to synchronize, which includes:
  - All files listed by `sysupgrade -l`
  - Custom files added via the `keepalived.ha_peer.sync_list` UCI option
  - Excludes files listed in the `keepalived.ha_peer.exclude_list` UCI option
  The list is saved inside the file `/tmp/restore_list`
- Copies files to the backup node's staging area at `/usr/share/keepalived/rsync/`
- Triggers a hotplug event on the backup node to notify that synchronization is complete

#### Restore phase (hotplug): on the backup node

The backup node doesn't automatically apply all transferred files. Instead, it uses a hotplug event fired
by the primary node at the end of the rsync process.
All files and directories inside `/usr/share/keepalived/rsync/tmp/restore_list` are copied to the original locations using `rsync`. For directories, `rsync` is invoked with `--delete` option to ensure exact mirroring.

#### Adding new files to synchronization

To synchronize custom files:

1. Register the file path in the peer sync_list:
```
uci add_list keepalived.ha_peer.sync_list=/tmp/debug
uci commit keepalived
/etc/init.d/keepalived restart
```

### Keepalived event system

The hotplug `keepalived` event system informs the nodes about cluster state changes through different actions:

#### NOTIFY_SYNC

Triggered on the backup node after file synchronization completes and a monitored file changes.
- Synchronizes files and directories
- Imports network configurations (WireGuard, IPsec, routes) from `/etc/ha` in disabled state using `/usr/libexec/ns-ha-import` script

Example hotplug invocation:
```
ACTION=NOTIFY_SYNC /sbin/hotplug-call keepalived
```

#### NOTIFY_MASTER

Executed when a node becomes the active (master) node:
- **On primary node**: Normal startup state after keepalived starts, execute also `/usr/libexec/ns-ha-enable`
  script that activates all network interfaces
- **On backup node**: Failover state after switchover occurs
  - Enables all network interfaces and services that were active on the failed primary using `/usr/libexec/ns-ha-enable` script
  - Activates WireGuard interfaces, IPsec tunnels, and routes imported from `/etc/ha`

#### NOTIFY_BACKUP

Executed on the backup node during normal operation or when the primary node recovers:
- Disables non-essential services to prevent conflicts with the primary
- Keeps WireGuard interfaces, IPsec interfaces, and routes in disabled state
- Disables cron jobs including subscription heartbeat, inventory, phonehome, remote reports, and backups

### Network Interface Management

The HA system handles different types of network interfaces with distinct approaches:

#### WAN Interfaces

WAN interfaces are automatically configured by the HA system including aliases.
The configuration is synchronized from the primary to the backup node:
- the `ns-ha-export` creates the file `/etc/ha/wan_interfaces` with the WAN configuration
- during NOTIFY_SYNC, the `ns-ha-import` backup node imports the WAN configuration and creates the devices (like VLAN, bond, bridges, etc) and interfaces in disabled state
- the `ns-ha-enable` script activates the WAN interfaces during NOTIFY_MASTER event

#### LAN Interfaces

LAN interfaces require manual static IP configuration on both nodes:
- Must be configured with static IP addresses before adding to HA
- Virtual IP must be in the same subnet as the interface IP addresses
- Static configuration ensures dnsmasq can start properly (OpenWrt requirement)
- Clients must use the Virtual IP address to access firewall services

### Service Management

The backup node maintains synchronized configuration but keeps most services disabled to prevent conflicts:

**Disabled services on backup:**
- DHCP and DNS server (dnsmasq)
- Threat shield (banip, adblock)
- OpenVPN server and tunnels
- MAC binding
- Multi-WAN (mwan3)
- Snort
- Hotspot (dedalo)
- Netifyd
- DDNS
- SNMP server (snmpd)
- IPsec tunnels (strongSwan)
- Subscription heartbeat and inventory
- Phone home functionality
- Remote reports to controller
- Remote backup operations
- WireGuard VPNs
- Custom routes (until failover)

**Network limitations for backup node:**
- No Internet access (cannot resolve DNS or reach external services)
- Cannot connect to Controller or Nethesis portals
- Does not receive automatic updates

During failover, the backup node activates all necessary services and takes over the virtual IP addresses, ensuring seamless service continuity.
