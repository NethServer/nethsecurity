# netify-plugin-stats

The stats plugins is disabled by default.
To enable it, execute:
```bash
if [ -f /usr/lib/libnetify-plugin-stats.so.0.0.0 ] && ! grep -q np-stats /etc/netifyd.conf; then
    (
        echo
        echo "[plugin_stats]"
        echo "np-stats = /usr/lib/libnetify-plugin-stats.so.0.0.0"
    ) >> /etc/netifyd.conf
fi
service netifyd restart
```
