# High Availability Firewall

This package contains a set of scripts to configure a high-availability firewall.
Configured with keepalived, it will provide a failover mechanism between two nodes.

Requirements:

- Two nodes must have the same network devices
- Nodes must be connected to the same LAN

Limitations:

- LAN name must be 'lan' in both firewalls
- IPv4 only
- VLANs are supported only on physical interfaces
- Extra packages such as NUT are not supported
- rsyslog configuration is not synced: if you need to send logs to a remote server, you must use the controller
- After the first synchronization, the backup node will have the same hostname as the primary node

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
ns-ha-config check-primary-node [lan_interface] [wan_interface]
```

If the `lan_interface` and `wan_interface` are not specified, the script will use the default values:
- `lan` for the LAN interface
- `wan` for the first WAN interface

It will check the following:

- the LAN interface must be configured with a static IP address
- there is at least one WAN interface
- the WAN interface is not configured as a PPPoE connection
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
- there is at least one WAN interface

Note the WAN interface is not checked on the backup node.
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
ns-ha-config init-primary-node <primary_node_ip> <backup_node_ip> <virtual_ip> [lan_interface] [wan_interface]
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

### Configure the WAN interface

The WAN interface must be configured on both nodes.
Use the following command to add a WAN interface:
```
ns-ha-config add-wan-interface <interface> <virtual_ip_address> <gateway>
```

Make sure to:

- enter the virtual IP address in CIDR notation
- enter the gateway IP address of the WAN interface

The script will:

- create the network interface and devices in the backup node
- configure the interface on both nodes by using fake IP addresses from the fake network `169.254.X.0/16`
- configure the virtual IP address on both nodes

Example:
```
ns-ha-config add-wan-interface wan 192.168.122.49/24 192.168.122.1
```

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
ns-ha-config remove-interface wan
```

The script will:
- check if the given interface is already configured as HA interface
- remove the interface from keepalived configuration
- remove all virtual routes, if present
- remove the interface from the backup node
- move the virtual IP address to the original interface

### Configue an alias

Aliases are special configurations that must explicitly set on the primary node.
First, add the alias to the network interface using the web interface.
Then, you can add the alias to the HA configuration.

To add an alias, use the following command:
```
ns-ha-config add-alias <interface> <alias> <ip_address> [<gateway>]
```

If the alias is for a WAN interface, you must enter also the gateway IP address.

The script will:

- check if the given interface is already configured as HA interface
- add the alias to keepalived configuration

Example:
```
ns-ha-config add-alias lan 192.168.100.66/24
```

Example for WAN interface:
```
ns-ha-config add-alias wan 192.168.122.66/24 192.168.122.1
```

**NOTE**: the alias will not appear in the network configuration of the backup node.

### Remove an alias

To remove an alias, use the following command:
```
ns-ha-config remove-alias <interface> <alias>
```

The script will:
- remove the alias from keepalived configuration
- remove all virtual routes, if present

Example:
```
ns-ha-config remove-alias wan 192.168.122.66/24
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

Aliases:
  Interface: wan, IP: 192.168.122.66/24
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
Last Sync Status: Up to Date
Last Sync Time: Fri Apr 18 13:09:08 UTC 2025
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

The HA cluster consists of two nodes: one is the primary and the other is the backup.
All configurations must be always done on the primary node.
The configuration is then automatically synchronized to the backup node.

Keepalived runs a specially crafted rsync script (`/etc/keepalived/scripts/ns-rsync.sh`) on the primary node to:
- export WireGuard interfaces, IPsec interfaces, routes and hotspot mac address to `/etc/ha`
- synchronize all files listed by `sysupgrade -l` and custom files added with the `add_sync_file` option from scripts inside `/etc/hotplug.d/keepalived` directory;
  files are synchronized to the backup node inside the directory `/usr/share/keepalived/rsync/`

The hotplug `keepalived` event is used to inform the system about changes in the keepalived status.

The event is triggered with an `ACTION` parameter that can be:

- `NOTIFY_SYNC`: the script is executed on the backup node after a sync has been done and a listed file is changed
  During this phase, all directories (like `/etc/openvpn` and `/etc/ha`) are synched to the original position.
  Also WireGuard interfaces, IPsec interfaces and routes are imported from the `/etc/ha` directory but in disabled state.

- `NOTIFY_MASTER`: the script can be executed both on the primary and on the backup node:
   - on the primary node, after keepalived is started: this is the normal startup state
   - on the backup node, after a switchover has been done: this is the failover state; 
     all WireGuard interfaces, IPsec interfaces and routes previously imported from the `/etc/ha` are enabled if they were enabled on the primary node

- `NOTIFY_BACKUP`: the script is executed on the backup node, after keepalived is started or if the primary returns up after a downtime
  All non-required services are disabled, including WireGuard interfaces, IPsec interfaces and routes.

The backup node keeps the configuration in sync with the primary node, but most services, including crontabs, are disabled.
The following cronjobs are disabled on the backup node and enabled on the primary node:

- subscription heartbeat
- subscription inventory
- phonehome
- remote reports to the controller
- remote backup

### Network configuration fundamentals

Each network interface managed by the High Availability (HA) system must have a static IP address.
WAN interfaces and LAN interfacres are configured in different ways:
- a WAN interface is configured automatically, it will be assigned an IP address in the `169.254.X.0/24` range.
  For every WAN interface, a new `169.254.X.0` network will be allocated.
  The primary node will get the IP address `169.254.X.1` and the backup node will get the IP address `169.254.X.2`.
  This imposes a theoretical limit of 254 WAN interfaces that can be managed by the HA system.
- a LAN interfaces do not use the 169.254.X.0/24 network. It must be configured manually with a static IP address on both nodes,
  then it will be assigned a Virtual IP address.
  The virtual IP must be in the same subnet as the LAN interface IP address.
  The static configuration is required to ensure that dnsmasq can start correctly: it requires a static IP address on the interface in the
  range of DHCP range, this is a limitation of OpenWrt implementation.
  The network interface will then be accessible using the Virtual IP address configured in the HA system.
  All clients must use the Virtual IP address to access the firewall services.

Note that the backup node does not have access to Internet so:
- it will not be able to resolve DNS names
- it will not be able to reach the Controller nor Nethesis portals
- it will not receive updates
