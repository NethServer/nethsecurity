# ns-openvpn

This is a partial porting of [nethserver-openvpn](https://github.com/NethServer/nethserver-openvpn/).


Changes:

- IP reservation is enforced
- support for multiple server instances
- SQLite connection database is volatile

Not supported:

- authentication based on certificate + otp
- authentication based on password + certificate
- authentication based on password
- mail notification about connect/disconnect events
