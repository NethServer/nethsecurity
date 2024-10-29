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
  - Set `br-lan` (LAN) to static IP: `192.168.100.238/24`
  - Set `eth1` (WAN) to DHCP (no PPPoE)
  - The `eth2` interface will be used for the HA configuration
  - Setup the configuration that will create the `ha` zone and setupt keepalived:
    ```sh
    echo '{"role": "main", "lan_interface": "br-lan", "ha_interface": "eth2", "virtual_ip": "192.168.100.240", "ha_main_ipaddress": "10.12.12.1", "ha_secondary_ipaddress": "10.12.12.2"}' | /usr/libexec/rpcd/ns.ha call setup
    ```
    The command will output something like:
    ```json
    {"password": "5aeab1d8", "pubkey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDF7MYY8vfgE/JgJT8mOejwIhB4UYKS4g/QSA7fwntCbN0LQ3nTA6LO3AzqhUCHd6LBS5P9aefTqDcG+cJQiGbXReqX1z4trQGs7QkBLbjlXb2Vock17UIGbm5ao8jyPsD4ADNdMF8p0S2xDvnfsOh7MXLy5N7QZGp1G3ISB6JVw0mdCn3GXYg1X9XB7Pqu0OJm7+n2SJvA1KXn9fKUDX92U1fGQcid05C3yRBS5QXB7VAAP55KKYp4RmQMCOcJDhDoHGB6Ia/fTxfhnLdXJcAHU2MTtyaEY7NWoPjKZ3769GIu4KLLDPB8aH9emg23Mej+eiMRIg0vFXsaJWVPuZzj root@primary"}
    ```
    The `password` and `pubkey` fields must be used in the secondary node configuration.
  - Apply the configuration:
    ```
    uci commit
    /etc/init.d/keepalived restart
    ```

2. On the secondary node:
  - Name the secondary firewall `secondary`
  - Set `eth0` (LAN) to static IP: `192.168.100.237/24`
  - Set `eth1` (WAN) to DHCP (no PPPoE)
  - The `eth2` interface will be used for the HA configuration

  - Create a zone `HA`:
    - No forwarding from/to other zones
    - Traffic to WAN: disabled
    - Traffic to firewall: enabled
    - Traffic within the same zone: reject
  - Create an interface `eth2` named `ha`, with static IP `10.12.12.2/24`
  - Execute:
    ```sh
    echo '{"role": "main", "lan_interface": "br-lan", "ha_interface": "eth2", "virtual_ip": "192.168.100.240", "ha_main_ipaddress": "10.12.12.1", "ha_secondary_ipaddress": "10.12.12.2", "password": "5aeab1d8", "pubkey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDF7MYY8vfgE/JgJT8mOejwIhB4UYKS4g/QSA7fwntCbN0LQ3nTA6LO3AzqhUCHd6LBS5P9aefTqDcG+cJQiGbXReqX1z4trQGs7QkBLbjlXb2Vock17UIGbm5ao8jyPsD4ADNdMF8p0S2xDvnfsOh7MXLy5N7QZGp1G3ISB6JVw0mdCn3GXYg1X9XB7Pqu0OJm7+n2SJvA1KXn9fKUDX92U1fGQcid05C3yRBS5QXB7VAAP55KKYp4RmQMCOcJDhDoHGB6Ia/fTxfhnLdXJcAHU2MTtyaEY7NWoPjKZ3769GIu4KLLDPB8aH9emg23Mej+eiMRIg0vFXsaJWVPuZzj root@primary"}' | /usr/libexec/rpcd/ns.ha call setup
    uci commit
    ./keepalived-config secondary br-lan eth2 192.168.100.240 10.12.12.1 10.12.12.2
    /etc/init.d/keepalived restart
    ```
