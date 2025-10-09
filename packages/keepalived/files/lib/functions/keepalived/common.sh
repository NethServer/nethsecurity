#!/bin/sh

# shellcheck disable=SC2039

__FILE__="$(basename "$0")"

__function__() {
	type "$1" > /dev/null 2>&1
}

log() {
	local facility=$1
	shift
	logger -t "ns-ha" -p "$facility" "$*"
}

log_info() {
	log info "$*"
}

log_notice() {
	log notice "$*"
}

log_warn() {
	log warn "$*"
}

log_err() {
	log err "$*"
}
