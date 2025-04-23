# High Availability Firewall

This package contains a set of scripts to configure a high-availability firewall.
Configured with keepalived, it will provide a failover mechanism between two nodes.

Requirements:

- Two nodes must have the same network devices
- Nodes must be connected to the same LAN

Limitations:

- IPv4 only
- VLANs are supported only on physical interfaces
- Extra packages such as NUT are not supported
- rsyslog configuration is not synced: if you need to send logs to a remote server, you must use the controller
- Hotspot is not supported since it requires a new registration when the main node goes down because the MAC address associated with the hotspot interface will be different
- After the first synchronization, the backup node will have the same hostname as the main node

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

## Configuration

The setup process configures the following:
- check if requirements are met both on the main and backup nodes
- configures HA traffic on lan interface
- sets up keepalived with the virtual IP, a random password and a public key for the synchronization
- configures dropbear to listen on port `65022`: this is used to sync data between the nodes using rsync, only
  key-based authentication is allowed
- configures conntrackd to sync the connection tracking table

In this example:
- `main_node_ip` is the main node, with LAN IP `192.168.100.238`
- `backup_node_ip` is the backup node, with LAN IP `192.168.100.239`
- the virtual IP is `192.168.100.240`

Before starting, follow these steps:

- power on the backup node, access the web interface and set a static LAN IP address, in this example `192.168.100.239`:
- then, power on the main node, access the web interface and set a static LAN IP address, in this example `192.168.100.238`

These IP addresses are used to access the nodes directly, even if the HA cluster is disabled.
You can consider these IP addresses as management IP addresses.

When the HA cluster is enabled, all the configuration will be automatically synchronized to the backup node, except for the network configuration.
If you need to change the network configuration, do it on the main node then follow the instructions below to adapt the HA configuration to the new network configuration.

The package provides a script to ease the configuration of the HA cluster, without accessing directly the APIs.
The script is named `ns-ha-config`. Usage syntax is:
```
ns-ha-config <action> [<option1> <option2>]
```

### Check local requirements

First, check the status of the main node:
```
ns-ha-config check-main-node
```

It will check the following:

- the LAN interface must be configured with a static IP address
- there is at least one WAN interface
- the WAN interface is not configured as a PPPoE connection
- if a DHCP server is running
  - the `Force DHCP server start` option must be enabled
  - the option `router` must be set: remember to set it to the virtual IP of the interface
- Hotspot must be disabled

### Check remote requirements

Then, check the status of the backup node:
```
ns-ha-config check-backup-node <backup_node_ip>
```

It will check the following:

- the backup node must be reachable via SSH on port 22 with root user
- the LAN interface must be configured with a static IP address
- there is at least one WAN interface
- the WAN interface is not configured as a PPPoE connection

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

### Initlialize the main node

If the requirements are met, you can initialize the main node:
```
ns-ha-config init-main-node <main_node_ip> <backup_node_ip> <virtual_ip>
```

The script will:

- initialize keepalived with the virtual IP
- configure conntrackd
- generate a random password and public key for the synchronization
- configure dropbear to listen on port `65022` and allow only key-based authentication

Example:
```
ns-ha-config init-main-node 192.168.100.238 192.168.100.239 192.168.100.240/24
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

At this point, the main node and the backup node are configured to talk to each other
using the LAN interface.
The virtual IP of the LAN will switch between the two nodes in case of failure.

It's now time to configure additional interfaces, starting at least with the WAN interface.

### Configure the WAN interface

The WAN interface must be configured on both nodes.
Use the following command to add a WAN interface:
```
ns-ha-config add-interface <interface> <virtual_ip_address> <gateway>
```

Make sure to:

- enter the virtual IP address in CIDR notation
- enter the gateway IP address of the WAN interface

The script will:

- create the network interface and devices in the backup node
- configure the interface on both nodes by using fake IP addresses from the fake network 169.254.0.0/16
- configure the virtual IP address on both nodes


Example:
```
ns-ha-config add-interface wan 192.168.122.49/24 192.168.122.1
```

### Configure extra interfaces

You can add extra interfaces using the same command:
```
ns-ha-config add-interface <interface> <virtual_ip_address> [<gateway>]
```

As the WAN interface, you must enter the virtual IP address in CIDR notation.
Usually, on non-WAN interfaces, the gateway is not required.

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

Please note that the interface will not be removed from the network configuration of the backup node.

### Configue an alias

Aliases are special configurations that must explicitly set on the main node.
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
Role: main
Current State: master
Last Sync Status: SSH Connection Failed
Last Sync Time: Fri Apr 18 13:07:08 UTC 2025
```

The first synchronization will take up to 10 minutes and will be done in the background.
After few minutes, the status should be like this:
```
Status: enabled
Role: main
Current State: master
Last Sync Status: Up to Date
Last Sync Time: Fri Apr 18 13:09:08 UTC 2025
```

## Troubleshooting and logs

A normal configuration synchronization will look like this on the backup node:
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

The ns-ha configuration script is a shell script that can be debugged using the `-x` option.
Example:
```
bash -x ns-ha-config <action> [<option1> <option2>]
```


### Maintenance

The HA cluster can be disabled at any time.
But be careful: if you disable the main node first, the backup node will take over the virtual IP address.

The static LAN IPs configured at the beginning can be considered management IPs.
These IPs are always accessible and can be used to manage the nodes directly, regardless of the HA cluster status.

#### Maintance of the backup node

To disable the HA cluster, use the following command on the **backup** node:
```
/etc/init.d/keepalived stop
```

Proceed with the maintenance of the backup node, then re-enable the HA cluster:
```
/etc/init.d/keepalived start
```

#### Maintenance of the main node

When the main node is disabled, the backup node will take over the virtual IP address.
To disable the HA cluster, use the following command on the **main** node:
```
/etc/init.d/keepalived stop
```

Proceed with the maintenance of the main node, then re-enable the HA cluster:
```
/etc/init.d/keepalived start
```

The main node will take over the virtual IP address again.


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

The HA cluster consists of two nodes: one is the main and the other is the backup.
All configurations must be always done on the main node.
The configuration is then automatically synchronized to the backup node.

Keepalived runs a specially crafted rsync script (`/etc/keepalived/scripts/ns-rsync.sh`) on the main node to:
- export WireGuard interfaces, IPsec interfaces, and routes to `/etc/ha`
- synchronize all files listed by `sysupgrade -l` and custom files added with the `add_sync_file` option from scripts inside `/etc/hotplug.d/keepalived` directory;
  files are synchronized to the backup node inside the directory `/usr/share/keepalived/rsync/`

The hotplug `keepalived` event is used to inform the system about changes in the keepalived status.

The event is triggered with an `ACTION` parameter that can be:

- `NOTIFY_SYNC`: the script is executed on the backup node after a sync has been done and a listed file is changed
  During this phase, all directories (like `/etc/openvpn` and `/etc/ha`) are synched to the original position.
  Also WireGuard interfaces, IPsec interfaces and routes are imported from the `/etc/ha` directory but in disabled state.

- `NOTIFY_MASTER`: the script can be executed both on the main and on the backup node:
   - on the main node, after keepalived is started: this is the normal startup state
   - on the backup node, after a switchover has been done: this is the failover state; 
     all WireGuard interfaces, IPsec interfaces and routes previously imported from the `/etc/ha` are enabled if they were enabled on the main node

- `NOTIFY_BACKUP`: the script is executed on the backup node, after keepalived is started or if the main returns up after a downtime
  All non-required services are disabled, including WireGuard interfaces, IPsec interfaces and routes.

The backup node keeps the configuration in sync with the main node, but most services, including crontabs, are disabled.
The following cronjobs are disabled on the backup node and enabled on the main node:

- subscription heartbeat
- subscription inventory
- phonehome
- remote reports to the controller
- remote backup

### Network configuration fundamentals

Each network interface managed by the High Availability (HA) system must have a static IP address.
If an interface is configured automatically, it will be assigned an IP address in the 169.254.0.0/24 range.
For every interface, two IP addresses are allocated: one for the main node and one for the backup node.
This imposes a theoretical limit of 127 network interfaces that can be managed by the HA system.
The network interface will then be accessible using the Virtual IP address configured in the HA system.
All clients must use the Virtual IP address to access the firewall services.

Note that the backup node does not have access to Internet so:
- it will not be able to resolve DNS names
- it will not be able to reach the Controller nor Nethesis portals
- it will not receive updates