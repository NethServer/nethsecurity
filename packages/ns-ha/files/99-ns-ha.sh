#!/bin/bash

# If HA is enabled, set the prompt to show the state of the node

state=$(grep state /tmp/keepalived.conf 2>/dev/null | awk '{print $2}')

if [ "$state" == "MASTER" ]; then
    export PS1='\u@\h [P]:\w\$ '
    state="P"
elif [ "$state" == "BACKUP" ]; then
    export PS1='\u@\h [S]:\w\$ '
    state="B"
fi

case "$TERM" in
	xterm*|rxvt*)
		export PS1='\[\e]0;\u@\h ['$state']: \w\a\]'$PS1
		;;
esac
