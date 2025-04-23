#!/bin/bash

state=$(grep state /tmp/keepalived.conf 2>/dev/null | awk '{print $2}')

if [ "$state" == "MASTER" ]; then
    export PS1='\u@\h [P]:\w\$ '
elif [ "$state" == "BACKUP" ]; then
    export PS1='\u@\h [S]:\w\$ '
fi
