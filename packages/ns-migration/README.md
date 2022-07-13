# ns-migration

ns-migration imports the configuration from NethServer 7.

Usage example:
```
ns-import export.tar.gz
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
