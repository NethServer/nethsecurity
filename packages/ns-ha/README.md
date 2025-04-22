# High Availability Firewall

This package contains a set of scripts to configure a high-availability firewall.
Configured with keepalived, it will provide a failover mechanism between two nodes.

Requirements:

- Two nodes must have the same network devices
- Nodes must be connected to the same LAN

Limitations:

- Aliases are not supported
- IPv4 only
- VLANs are supported only on physical interfaces
- Extra packages such as NUT are not supported
- rsyslog configuration is not synced: if you need to send logs to a remote server, you must use the controller
- Hotspot is not supported since it requires a new registration when the main node goes down because the MAC address associated with the hotspot interface will be different

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
- Check if requirements are met both on the main and backup nodes
- Configures HA traffic on lan interface
- Sets up keepalived with the virtual IP, a random password and a public key for the synchronization
- Configures dropbear to listen on port `65022`: this is used to sync data between the nodes using rsync, only
  key-based authentication is allowed
- Configures conntrackd to sync the connection tracking table

In this example:
- `main_node_ip` is the main node, with LAN IP `192.168.100.238` and HA IP `10.12.12.1`
- `backup_node_ip` is the backup node, with LAN IP `192.168.100.239` and HA IP `10.12.12.2`
- the virtual IP is `192.168.100.240`

### Automatic configuration

The package provides a script to configure the HA cluster automatically:
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

### Check the status

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
