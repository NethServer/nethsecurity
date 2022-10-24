# ns-storage

As default, logs only are written inside a voltatile in-memory directory to prevent errors
on the root file system in case of failure.

The `ns-storage` package configures the system to save a copy of the logs inside an extra data local storage,
like a USB stick,

## Add a data storage

Before starting the configuration, attach a disk device to machine.
You can fine the attached device name inside `/var/log/messages`.

To prepare the disk, execute:
```
add-storage <device>
```

The script will prepare the device by:

- erasing all partitions and existing data on the device
- creating a single partition with EXT4 filesystem
- mounting the storage at `/mnt/data`

Then, the system will be reconfigure as follow:

- rsyslog will write logs also inside `/mnt/data/logs/messages` file
- logrotate will rotate `/mnt/data/logs/messages` once a week (see `/etc/logrotate/data.conf` for more info)

## Remove the data storage

To remove the data storage and restore only in-memory log retention, execute:
```
remove-storage
```
