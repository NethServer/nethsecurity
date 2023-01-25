#!/bin/sh

[ "$(uci -q get system.@system[0].ttylogin)" = 1 ] || exec /bin/ash --login

[ -f /etc/keymap ] && /sbin/loadkmap < /usr/share/keymaps/$(/bin/cat /etc/keymap).map.bin 2>/dev/null

exec /bin/login
