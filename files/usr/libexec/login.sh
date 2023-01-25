#!/bin/sh

[ "$(uci -q get system.@system[0].ttylogin)" = 1 ] || exec /bin/ash --login

[ -f /etc/keymap ] && /sbin/loadkmap < $(/bin/cat /etc/keymap)

exec /bin/login
