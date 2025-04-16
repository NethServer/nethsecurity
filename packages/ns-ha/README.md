# High Availability Firewall

This package contains a set of scripts to configure a high-availability firewall.
Configured with keepalived, it will provide a failover mechanism between two nodes.

Requirements:

- Two nodes with similar hardware
- Nodes must be connected to the same LAN
- Nodes must have only one WAN interface configured with DHCP

Limitations:

- WAN must be configured with DHCP
- Extra packages such as NUT are not supported
- rsyslog configuration is not synced: if you need to send logs to a remote server, you must use the controller
- Hotspot is not supported since it requires a new registration when the primary node goes down because the MAC address associated with the hotspot interface will be different

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
- Active connections tracking (conntrackd) - NOT tested

## Configuration

The setup process configures the following:
- Configures HA traffic on lan interface
- Sets up keepalived with the virtual IP, a random password and a public key for the synchronization
- Configures dropbear to listen on port `65022`: this is used to sync data between the nodes using rsync, only
  key-based authentication is allowed
- Configures conntrackd to sync the connection tracking table

In this example:
- `main` is the primary node, with LAN IP `192.168.100.238` and HA IP `10.12.12.1`
- `backup` is the backup node, with LAN IP `192.168.100.237` and HA IP `10.12.12.2`
- the virtual IP is `192.168.100.240`

1. On the primary node:
  - Name the primary firewall `main`
  - Set `br-lan` (LAN) to static IP: `192.168.100.238/24`
  - Set `eth1` (WAN) to DHCP (no PPPoE)
  - Reserve `eth2` for HA configuration (it must not configured in the network settings)
  - Setup the configuration that will: create the `ha` zone, configure the IP for the HA interface, setup keepalived:
    ```sh
    echo '{"role": "main", "main_node_ip": "192.168.100.238", "backup_node_ip": "192.168.100.239", "virtual_ip": "192.168.100.240/24"}' | /usr/libexec/rpcd/ns.ha call setup
    ```
    The command will output something like:
    ```json
    {"password": "5aeab1d8", "pubkey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDF7MYY8vfgE/JgJT8mOejwIhB4UYKS4g/QSA7fwntCbN0LQ3nTA6LO3AzqhUCHd6LBS5P9aefTqDcG+cJQiGbXReqX1z4trQGs7QkBLbjlXb2Vock17UIGbm5ao8jyPsD4ADNdMF8p0S2xDvnfsOh7MXLy5N7QZGp1G3ISB6JVw0mdCn3GXYg1X9XB7Pqu0OJm7+n2SJvA1KXn9fKUDX92U1fGQcid05C3yRBS5QXB7VAAP55KKYp4RmQMCOcJDhDoHGB6Ia/fTxfhnLdXJcAHU2MTtyaEY7NWoPjKZ3769GIu4KLLDPB8aH9emg23Mej+eiMRIg0vFXsaJWVPuZzj root@primary"}
    ```
    The `password` and `pubkey` fields must be used in the backup node configuration.
  - Apply the configuration:
    ```
    uci commit
    /etc/init.d/network restart
    /etc/init.d/firewall restart
    /etc/init.d/keepalived restart
    ```

2. On the backup node:
  - Name the backup firewall `backup`
  - Set `eth0` (LAN) to static IP: `192.168.100.237/24`
  - Set `eth1` (WAN) to DHCP (no PPPoE)
  - The `eth2` interface will be used for the HA configuration
  - Setup the configuration that will: create the `ha` zone, configure the IP for the HA interface, setup keepalived. Use the `password` and `pubkey` from the primary node:
    ```sh
    echo '{"role": "backup", "main_node_ip": "192.168.100.238", "backup_node_ip": "192.168.100.239", "virtual_ip": "192.168.100.240/24", "password": "5aeab1d8", "pubkey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDF7MYY8vfgE/JgJT8mOejwIhB4UYKS4g/QSA7fwntCbN0LQ3nTA6LO3AzqhUCHd6LBS5P9aefTqDcG+cJQiGbXReqX1z4trQGs7QkBLbjlXb2Vock17UIGbm5ao8jyPsD4ADNdMF8p0S2xDvnfsOh7MXLy5N7QZGp1G3ISB6JVw0mdCn3GXYg1X9XB7Pqu0OJm7+n2SJvA1KXn9fKUDX92U1fGQcid05C3yRBS5QXB7VAAP55KKYp4RmQMCOcJDhDoHGB6Ia/fTxfhnLdXJcAHU2MTtyaEY7NWoPjKZ3769GIu4KLLDPB8aH9emg23Mej+eiMRIg0vFXsaJWVPuZzj root@primary"}' | /usr/libexec/rpcd/ns.ha call setup
    uci commit
    /etc/init.d/network restart
    /etc/init.d/firewall restart
    /etc/init.d/keepalived restart
    ```

## How it works

The HA cluster consists of two nodes: one is the primary and the other is the backup.
All configurations must be always done on the primary node.
The configuration is then automatically synchronized to the backup node.

Keepalived runs a specially crafted rsync script (`/etc/keepalived/scripts/ns-rsync.sh`) on the primary node to:
- export WireGuard interfaces, IPsec interfaces, and routes to `/etc/ha`
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
