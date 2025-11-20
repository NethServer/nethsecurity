# Netify Agent Utility Functions
# Copyright (C) 2016-2024 eGloo Incorporated
#
# This is free software, licensed under the GNU General Public License v3.

SYSCONFDIR="${NETIFYD_DESTDIR}/etc"

[ -f ${SYSCONFDIR}/conf.d/netifyd ] && . ${SYSCONFDIR}/conf.d/netifyd
[ -f ${SYSCONFDIR}/default/netifyd ] && . ${SYSCONFDIR}/default/netifyd
[ -f ${SYSCONFDIR}/sysconfig/netifyd ] && . ${SYSCONFDIR}/sysconfig/netifyd

# Load defaults for RedHat/CentOS/Ubuntu/Debian
load_defaults()
{
    local options=""

    options=$NETIFYD_EXTRA_OPTS

    for entry in $NETIFYD_INTNET; do
        if [ "$entry" = "${entry/,/}" ]; then
            options="$options -I $entry"
            continue
        fi
        for net in ${entry//,/ }; do
            if [ "$net" = "${entry/,*/}" ]; then
                options="$options -I $net"
            else
                options="$options -A $net"
            fi
        done
    done

    for entry in $NETIFYD_EXTNET; do
        if [ "$entry" = "${entry/,/}" ]; then
            options="$options -E $entry"
            continue
        fi
        for ifn in ${entry//,/ }; do
            if [ "$ifn" = "${entry/,*/}" ]; then
                options="$options -E $ifn"
            else
                options="$options -N $ifn"
            fi
        done
    done

    options=$(echo "$options" |\
        sed -e 's/^[[:space:]]*//g' -e 's/[[:space:]]*$$//g')

    echo "$options"
}

# NethServer
# - Dynamically add all configured LAN/WAN interfaces.
load_nethserver()
{
    local options=""
    local ifcfg_sw="${SYSCONFDIR}/shorewall/interfaces"

    if [ -f "$ifcfg_sw" ]; then
        for ifn in $(grep -E '^loc[[:space:]]' $ifcfg_sw | awk '{ print $2 }'); do
            [ -z "$ifn" ] && break
            options="$options -I $ifn"
        done

        for ifn in $(grep -E "^blue[[:space:]]" $ifcfg_sw | awk '{ print $2 }'); do
            [ -z "$ifn" ] && break
            options="$options -I $ifn"
        done

        for ifn in $(grep -E "^orang[[:space:]]" $ifcfg_sw | awk '{ print $2 }'); do
            [ -z "$ifn" ] && break
            options="$options -I $ifn"
        done

        for ifn in $(grep -E '^net[[:space:]]' $ifcfg_sw | awk '{ print $2 }'); do
            [ -z "$ifn" ] && break
            [ -f "${SYSCONFDIR}/sysconfig/network-scripts/ifcfg-${ifn}" ] &&
                . "${SYSCONFDIR}/sysconfig/network-scripts/ifcfg-${ifn}"
            if [ ! -z "$ETH" ]; then
                options="$options -E $ETH -N $ifn"
                unset ETH
            else
                options="$options -E $ifn"
            fi
        done
    fi

    options=$(echo "$options" |\
        sed -e 's/^[[:space:]]*//g' -e 's/[[:space:]]*$$//g')

    echo "$options"
}

# OpenWrt:
# - Dynamically add all configured LAN/WAN interfaces.
load_openwrt()
{
    local options="-I br-lan"

    # Obtain interface on 21.02
    ifn=$(uci get network.wan.device 2>/dev/null)

    # If getting interface name failed try 19.07 and earlier approach
    [ -z "$ifn" ] && ifn=$(uci get network.wan.ifname 2>/dev/null)
    [ ! -z "$ifn" ] && options="$options -E $ifn"

    options=$(echo "$options" |\
        sed -e 's/^[[:space:]]*//g' -e 's/[[:space:]]*$$//g')

    echo "$options"
}

load_modules()
{
    modprobe nfnetlink >/dev/null 2>&1
    modprobe nf_conntrack_netlink >/dev/null 2>&1
}

detect_os()
{
    if [ -f /etc/issue ]; then
        if grep -E -q '^Ubuntu' /etc/issue; then
            echo "ubuntu"
            return
        fi
    fi

    if [ -f /etc/release ]; then
        if grep -E -q '^Endian ' /etc/release; then
            echo "endian"
            return
        fi
    fi

    if [ -f /etc/nethserver-release ]; then
        echo "nethserver"
    elif [ -f /etc/gentoo-release ]; then
        echo "gentoo"
    elif [ -f /etc/openwrt_release ]; then
        echo "openwrt"
    elif [ -x /bin/freebsd-version ]; then
        echo "freebsd"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/centos-release ]; then
        echo "centos"
    elif [ -f /etc/redhat-release ]; then
        echo "redhat"
    elif [ -f /etc/lxc-release ]; then
        echo "lxc"
    else
        echo "unknown"
    fi
}

auto_detect_options()
{
    local options=""

    options=$(load_defaults)

    if [ "$NETIFYD_AUTODETECT" = "yes" ]; then
        case "$(detect_os)" in
            nethserver)
                options=$(load_nethserver)
            ;;
            openwrt)
                options=$(load_openwrt)
            ;;
        esac
    fi

    echo "$options"
}

restart_netifyd()
{
    local CMD="restart"
    local FMT="${SYSCONFDIR}/init.d/netifyd %s"

    case "$(detect_os)" in
        centos|nethserver|ubuntu)
            if [ "x$1" = "xtrue" ]; then
                CMD="try-restart"
            fi
            FMT="systemctl %s netifyd"
        ;;
        freebsd)
            FMT="${SYSCONFDIR}/rc.d/netifyd %s"
        ;;
        openwrt)
            if [ "x$1" = "xtrue" ]; then
                ${SYSCONFDIR}/init.d/netifyd running || exit 0
            fi
        ;;
    esac

    exec $(printf "$FMT" "$CMD")
}

config_enable_informatics()
{
    if grep -E -i -q '^auto_informatics = (no|0|false)' $1; then
        sed -i -e 's/^auto_informatics.*/auto_informatics = yes/' $1
    fi
}

config_disable_informatics()
{
    if grep -E -i -q '^auto_informatics = (yes|1|true)' $1; then
        sed -i -e 's/^auto_informatics.*/auto_informatics = no/' $1
    fi
}

config_enable_plugin()
{
    if grep -E -i -q '^enable = (no|0|false)' $1; then
        sed -i -e 's/^enable.*/enable = yes/' $1
    fi
}

config_disable_plugin()
{
    if grep -E -i -q '^enable = (yes|1|true)' $1; then
        sed -i -e 's/^enable.*/enable = no/' $1
    fi
}

# vi: expandtab shiftwidth=4 softtabstop=4 tabstop=4 syntax=sh
