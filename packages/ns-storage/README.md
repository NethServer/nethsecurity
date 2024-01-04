# ns-storage

As default, logs are written inside a volatile in-memory directory to prevent errors
on the root file system in case of failure.

The `ns-storage` package configures the system to save a copy of the logs inside an extra data local storage,
like a USB stick.

Features:

- device initialization and mounting
- rsyslog configuration
- logrotate for extra log files
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

### Use the device

Execute the `add-storage` script on the prepared device, like:
```
add-storage /dev/sda
```

The script will mount the storage at `/mnt/data` and configure
the system as follow:

- rsyslog will write logs also inside `/mnt/data/logs/messages` file
- logrotate will rotate `/mnt/data/logs/messages` once a week (see `/etc/logrotate/data.conf` for more info)

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
