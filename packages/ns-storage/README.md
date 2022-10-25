# ns-storage

As default, logs only are written inside a voltatile in-memory directory to prevent errors
on the root file system in case of failure.

The `ns-storage` package configures the system to save a copy of the logs inside an extra data local storage,
like a USB stick.

Features:

- device initialization and mounting
- rsyslog configuration
- logrotate for extra log files
- customizable cron job to sync data once a day

## Add a data storage

Before starting the configuration, attach a disk device to the machine.
You can find the attached device name inside `/var/log/messages`.

To prepare the disk, execute:
```
add-storage <device>
```

The script will prepare the device by:

- erasing all partitions and existing data on the device
- creating a single partition using the ext4 filesystem
- mounting the storage at `/mnt/data`

Then, the system will be reconfigured as follow:

- rsyslog will write logs also inside `/mnt/data/logs/messages` file
- logrotate will rotate `/mnt/data/logs/messages` once a week (see `/etc/logrotate/data.conf` for more info)

### Data sync customization

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
