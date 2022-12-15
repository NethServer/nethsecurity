# ns-don

This is a lean implementation of [Don client](https://github.com/nethesis/windmill/tree/master/don).

The configuration is saved inside the `/etc/config/don` UCI database.
Available options:

- `system_id`: system identifier, if empty don will use `system_id` from `ns-plug` configuration
- `ca`: X509 certificate of VPN CA, default is '/etc/don/nethesis.pem'
- `server`: hostname of the Windmill server, default is 'sos.nethesis.it'
- `ssh_key`: SSH public key allowed to connect, default is '/etc/don/nethesis.pub'

Before starting don, make sure the system has a configured `system_id`.
To start don, execute:
```
don start
```

If you need a JSON output, use:
```
don start -j
```

To retrieve don status:
```
don status
```

To stop don, execute:
```
don stop
```
