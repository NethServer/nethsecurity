# High Availability Firewall

This package is a set of scripts to configure a high availability firewall.
Configured with keepalived, it will provide a failover mechanism between two nodes.

Requirements:
- nodes must be connected to the same LAN
- nodes must have a dedicated interface for the HA configuration
- nodes must have only one WAN interface configured with DHCP

In this example:
- `main` is the primary node, with LAN IP `192.168.100.238` and HA IP `10.12.12.1`
- `secondary` is the secondary node, with LAN IP `192.168.100.237` and HA IP `10.12.12.2`
- the virtual IP is `192.168.100.240`

1. On the primary node:
  - Name the primary firewall `main`
  - Set `eth0` (LAN) to static IP: `192.168.100.238/24`
  - Set `eth1` (WAN) to DHCP (no PPPoE)
  - Create a zone `HA`:
    - No forwarding from/to other zones
    - Traffic to WAN: disabled
    - Traffic to firewall: enabled
    - Traffic within the same zone: reject
  - Create an interface `eth2` named `ha`, with static IP `10.12.12.1/24`
  - Execute:
    ```sh
    ./keepalived-config main br-lan eth2 192.168.100.240 10.12.12.1 10.12.12.2
    /etc/init.d/keepalived restart
    ```

2. On the secondary node:
  - Name the secondary firewall `secondary`
  - Set `eth0` (LAN) to static IP: `192.168.100.237/24`
  - Set `eth1` (WAN) to DHCP (no PPPoE)
  - Create a zone `HA`:
    - No forwarding from/to other zones
    - Traffic to WAN: disabled
    - Traffic to firewall: enabled
    - Traffic within the same zone: reject
  - Create an interface `eth2` named `ha`, with static IP `10.12.12.2/24`
  - Execute:
    ```sh
    ./keepalived-config secondary br-lan eth2 192.168.100.240 10.12.12.1 10.12.12.2
    /etc/init.d/keepalived restart
    ```
