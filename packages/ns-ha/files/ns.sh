#!/bin/sh

# Function to update crontab entries based on action (disable or enable)
update_cron() {
    local action="$1"
    local commands="$2"
    local sed_command

    # Determine the appropriate sed command based on the action
    if [ "$action" = "disable" ]; then
        sed_command='s/^\([^#]\)/#\1/'
    elif [ "$action" = "enable" ]; then
        sed_command='s/^#//'
    else
        echo "Invalid action: $action"
        return 1
    fi

    # Create a temporary file to store modified crontab
    temp_crontab=$(mktemp)
    crontab -l > "$temp_crontab"

    # Loop through each command and apply the sed transformation
    for cmd in $commands; do
        sed -i "/$cmd/$sed_command" "$temp_crontab"
    done

    # Update the crontab with the modified content
    crontab "$temp_crontab"
    rm "$temp_crontab"
}
