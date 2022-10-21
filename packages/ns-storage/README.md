# ns-storage

As default, logs only are written inside a voltatile in-memory directory to prevent errors
on the root file system in case of failure.

The `ns-storage` package configures the system to save a copy of the logs inside an extra local storage,
like a USB stick,

## Add an extra storage

Before starting the configuration, attach a disk device to machine.
You can fine the attached device name inside `/var/log/messages`.

To prepare the disk, execute:
```
add-storage <device>
```

The script will prepare the device by:

- erasing all partitions and existing data on the device
- creating a single partition with EXT4 filesystem
- mounting the storage at `/mnt/extra`

Then, the system will be reconfigure as follow:

- rsyslog will write logs also inside `/mnt/extra/logs/messages` file
- logrotate will rotate `/mnt/extra/logs/messages` once a week (see `/etc/logrotate/extra.conf` for more info)

## Remove the extra storage

To remove the extra storage and restore only in-memory log retention, execute:
```
remove-storage
```
