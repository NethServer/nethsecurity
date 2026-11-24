# ns-storage

As default, logs are written inside a volatile in-memory directory to prevent errors
on the root file system in case of failure.

The `ns-storage` package configures an extra data local storage, like a USB stick, where services keep
their persistent data. Persistent logs are stored there by victoria-logs.

Features:

- device initialization and mounting
- dnsmasq DHCP lease persistence on mounted storage
- customizable cron job to sync data once a day

## Add a data storage

It is possible to use either a partition on the main disk where the operating system is installed or a new disk as additional storage.

The procedure is divided into two parts:

- configure the disk or partition
- mount the device and setup the system

### New disk

Before starting the configuration, attach a disk device to the machine.
You can find the attached device name inside `/var/log/messages`, let's assume the device is named `/dev/sdb`.

To prepare the disk, execute:
```
/usr/libexec/ns-storage-setup-disk /dev/sdb
```

The script will prepare the device by:

- erasing all partitions and existing data on the device
- creating a single partition using the ext4 filesystem

### Parition on existing disk

If the disk where the operating system is installed has unallocated space, it is possible to utilize this space as data storage.

To check if the disk has free space, execute:
```
/usr/libexec/ns-storage-has-free-space
```

The script must exit with 0 and return the available space like:
```
{"name": "vda", "path": "/dev/vda", "size": 968899584}
```

In this case, proceed with the setup:
```
/usr/libexec/ns-storage-setup-partition
```

The data partition starts 100 MiB after the end of the root partition.

Image layout:

| Partition | Size | Start | End |
|---|---|---|---|
| boot | 16 MiB | 0.25 MiB | 16.25 MiB |
| root | 399 MiB (`CONFIG_TARGET_ROOTFS_PARTSIZE` in `config/partsize.conf`) | 16.25 MiB | 415.25 MiB |
| data, created by images with the 300 MB root | rest of the disk | 416 MiB | end of disk |

- The root partition must not grow past 399 MB, or it overwrites the data partition of existing installs.
- Sysupgrade with an image whose partition table differs from the disk writes the image partition table: the data partition entry disappears, its data stays on disk.
- `/etc/uci-defaults/29-ns-storage-restore-partition` runs at first boot, before the fstab mount: if `fstab.ns_data` is set and no `ns_data` filesystem is visible, it scans the boot disk after the root partition, on MiB boundaries up to 256 MiB, for an ext4 superblock with label `fstab.ns_data.label` or UUID `fstab.ns_data.uuid`, then recreates the partition entry with parted up to the end of the disk. On failure it exits with an error and runs again at next boot.
- Downgrading to an image with the 300 MB root drops the entry again, older images have no restore script; upgrading again restores it.

### Use the device

Execute the `add-storage` script on the prepared device, like:
```
add-storage /dev/sda
```

The script will mount the storage at `/mnt/data` and configure
the system as follow:

- victoria-logs will store logs inside `/mnt/data/victoria-logs-data`, see the victoria-logs README for retention
- dnsmasq will store DHCP leases inside `/mnt/data/dnsmasq/dhcp.leases`; `/tmp/dhcp.leases` remains available as a compatibility symlink while the storage is mounted

### Storage status alert

The storage health check is exported to Telegraf by `/usr/libexec/telegraf-storage-status` and evaluated by vmalert as `StorageStatus`.

## Data sync customization

Every night the cron will run a script named `sync-data` to sync data from in-memory
filesystems to persistent storage.
The `sync-data` script will call all executables files inside `/usr/libexec/sync-data` directory.

You can add your own script inside the above directory.
Remember also to add the script istelf to the backup:
```
echo /usr/libexec/sync-data/myscript >> /etc/sysupgrade.conf
```

## Remove the data storage

To remove the data storage and restore in-memory log retention only, execute:
```
remove-storage
```

The `remove-storage` script switches dnsmasq back to `/tmp/dhcp.leases` before
unmounting `/mnt/data`.
