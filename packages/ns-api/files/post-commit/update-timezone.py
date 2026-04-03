#!/usr/bin/python3

#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

import subprocess

if 'system' in changes:
    system_changes = changes['system']
    timezone_value = None
    zonename_value = None
    
    # extract timezone and zonename values from changes
    for change in system_changes:
        if len(change) >= 4:
            if change[2] == 'timezone':
                timezone_value = change[3]
            elif change[2] == 'zonename':
                zonename_value = change[3]
    
    # update symlink and TZ variable if changed
    if zonename_value:
        # replace spaces with underscores like /etc/init.d/system does
        zonename_normalized = zonename_value.replace(' ', '_')
        subprocess.run(["/bin/ln", "-sf", f"/usr/share/zoneinfo/{zonename_normalized}", "/etc/localtime"], check=True, capture_output=True)
    
    if timezone_value:
        subprocess.run(["/bin/sh", "-c", f"echo '{timezone_value}' > /tmp/TZ"], check=True, capture_output=True)