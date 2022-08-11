# ns-migration

ns-migration imports the configuration from NethServer 7 (NS7).

Before proceed, make sure to export NS7 configuration using [nethserver-firwall-migration](https://github.com/NethServer/nethserver-firewall-migration/) package. 

## Usage

The main command is `ns-import`:
```
./ns-import [-q] [-m oldmac=newmac] <exported_archive>
```

Usage example:
```
ns-import -m 'ae:12:3b:19:0a:2a=0b:64:31:69:ae:8a' export.tar.gz
```

The `ns-import` will:
- explode the archive inside a temporary directory
- invoke all the scripts inside `/usr/share/firewall-import/` directory
- pass the temporary directory as argument to each script

Scripts can also be invoked manually after extracting the archive.
Example:
```
cd /tmp
tar xvzf export.tar.gz
/usr/share/firewall-import/network /tmp/export
```

The `ns-import` script is verbose by default, use the `-q` option to suppress output to standard output.

### Remapping interfaces

When importing the configuration from an old machine to a new one, you need to remap
network interface hardware addresses.

Usage example:
```
ns-import -m 'ae:12:3b:19:0a:2a=0b:64:31:69:ae:8a' export.tar.gz
```

The `-m` option will be used by migration scripts to move the configuration from the old network
interface (`ae:12:3b:19:0a:2a`) to the new one (`0b:64:31:69:ae:8a`).

## network

Differences since NS7:

- source NAT are connected to `wan` outbound zone and not to a specific interface;
  this configuration can be changed by setting `src` option to `*` and adding `device` option set to the WAN physical ethernet interface
 
## dhcp

- TFTP options are migrated, but not the content of the tftp_root directory. To re-enable the service make sure to setup `tftp_root` option
