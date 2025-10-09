#!/bin/sh

# shellcheck disable=SC2039

# shellcheck source=/dev/null
. /lib/functions.sh
# shellcheck source=/dev/null
. /lib/functions/keepalived/common.sh
# shellcheck source=/dev/null
. /lib/functions/keepalived/ns.sh

RSYNC_USER="root"
RSYNC_HOME="/usr/share/keepalived/rsync"

utc_timestamp() {
	date -u +%s
}

update_last_sync_time() {
	uci_revert_state keepalived "$1" last_sync_time
	uci_set_state keepalived "$1" last_sync_time "$(utc_timestamp)"
}

update_last_sync_status() {
	local cfg="$1"
	shift
	local status="$*"

	# Raise alert if:
	# - last_sync_time is empty
	# - last sync time is older than 5 minutes
	# - last_sync_status is different from the current status
	config_get last_sync_status "$cfg" last_sync_status
	if [ -z "$last_sync_status" ] || [ "$last_sync_status" != "$status" ]; then
		if [[ "$status" != "Up to Date" && "$status" != "Successful" ]]; then
			send_alert "ha:sync:failed" "FAILURE"
		else
			send_alert "ha:sync:failed" "OK"
		fi
	fi

	uci_revert_state keepalived "$cfg" last_sync_status
	uci_set_state keepalived "$cfg" last_sync_status "$status"
}

ha_sync_send() {
	# The list of files to sync is built from:
	# - the sync_list option in the config keepalived.ha_sync.sync_list
	# - the list of files modified by sysupgrade (sysupgrade -l)
	# The exclude_list option in the config keepalived.ha_sync.exclude_list
	local cfg=$1
	local address ssh_key ssh_port sync_list sync_dir sync_file count exclude_list
	local ssh_options ssh_remote dirs_list files_list
	local restore_list="/tmp/restore_list"

	config_get address "$cfg" address
	[ -z "$address" ] && return 0

	config_get ssh_port "$cfg" ssh_port 22
	config_get sync_dir "$cfg" sync_dir "$RSYNC_HOME"
	[ -z "$sync_dir" ] && return 0
	config_get ssh_key "$cfg" ssh_key "$sync_dir"/.ssh/id_rsa
	# Read list extra files to sync from config
	config_get sync_list "$cfg" sync_list
	config_get exclude_list "$cfg" exclude_list

	for sync_file in $sync_list $(sysupgrade -l); do
		list_contains exclude_list "${sync_file}" && continue
		[ ! -e "$sync_file" ] && continue
		list_contains files_list "${sync_file}" || append files_list "${sync_file}"
	done

	# Save the files_list to restore_list file: the restore list file is used by the
	# backup node
	> "$restore_list"
	for file in $files_list; do
		echo "$file" >> "$restore_list"
	done

	ssh_options="-y -y -i $ssh_key -p $ssh_port"
	ssh_remote="$RSYNC_USER@$address"

	# shellcheck disable=SC2086
	timeout 10 ssh $ssh_options $ssh_remote mkdir -m 755 -p "/tmp" || {
		log_err "Can not connect to $address. check key or connection"
		update_last_sync_time "$cfg"
		update_last_sync_status "$cfg" "SSH Connection Failed"
		return 0
	}

	# shellcheck disable=SC2086
	rsync -a --relative --delete-after ${files_list} ${restore_list} -e "ssh $ssh_options" --rsync-path="rsync" "$ssh_remote":"$sync_dir" || {
		log_err "Configuration sync transfer failed for $address"
		update_last_sync_time "$cfg"
		update_last_sync_status "$cfg" "Rsync Transfer Failed"
		return 0
	}

	log_info "Configuration sync completed for $address"
    # Invoke detached hotplug on the backup node
    ssh $ssh_options $ssh_remote "ACTION=NOTIFY_SYNC /usr/bin/setsid /sbin/hotplug-call keepalived &" &> /dev/null
    update_last_sync_time "$cfg"
    update_last_sync_status "$cfg" "Successful"

}

ha_sync_each_peer() {
	local cfg="$1"
	local c_name="$2"
	local name sync sync_mode

	config_get name "$cfg" name
	[ "$name" != "$c_name" ] && return 0

	config_get sync "$cfg" sync 0
	[ "$sync" = "0" ] && return 0

	config_get sync_mode "$cfg" sync_mode
	[ -z "$sync_mode" ] && return 0

	case "$sync_mode" in
		send) ha_sync_send "$cfg" ;;
		receive) ;;
	esac
}

ha_sync_peers() {
	config_foreach ha_sync_each_peer peer "$1"
}

ha_sync() {
	config_list_foreach "$1" unicast_peer ha_sync_peers
}

main() {
	local lockfile="/var/lock/keepalived-rsync.lock"

	if ! lock -n "$lockfile" > /dev/null 2>&1; then
		log_info "Another process is already running"
		return 1
	fi

	/usr/libexec/ns-ha-export
	config_load keepalived
	config_foreach ha_sync vrrp_instance

	lock -u "$lockfile"

	return 0
}

main "$@"
