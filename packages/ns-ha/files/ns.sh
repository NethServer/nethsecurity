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

# Function to send alerts
# Alerts are sent only when the status changes
send_alert() {
    local lk=$(uci -q get ns-plug.config.system_id)
    local secret=$(uci -q get ns-plug.config.secret)
    local url=$(uci -q get ns-plug.config.alerts_url)"alerts/store"

    # Do not send alert if system_id or secret is not set
    if [ -z "$lk" ] || [ -z "$secret" ]; then
        return
    fi

    local alert_id=$1
    # This status variable must be marked as local otherwise will overwrite the global status used inside ns-rsync.sh
    local status=$2

    logger -t ns-ha-alert "Sending alert ${alert_id} with status ${status}"

    # Prepare payload
    local payload='{"lk": "'$lk'", "alert_id": "'$alert_id'", "status": "'$status'"}'

    # Send alert
    /usr/bin/curl -m 30 --retry 3 -L -s \
        --header "Authorization: token ${secret}" \
        --header "Content-Type: application/json" \
        --header "Accept: application/json" \
        --data-raw "${payload}" ${url} > /dev/null
}

# Send alert on cluster state change
# The backup node will send the failure alert if it becomes the master
# The primary node will send the resolution alert if it becomes the master
cluster_alert() {
    local state=$1

    if uci -q get keepalived.primary >/dev/null; then
        # Primary node
        if [ "$state" == "master" ]; then
            send_alert "ha:primary:failed" "OK"
        fi
    else
        # Backup node
        if [ "$state" == "master" ]; then
            send_alert "ha:primary:failed" "FAILURE"
        fi
    fi
}
