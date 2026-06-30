/*
 * Copyright (C) 2023 Nethesis S.r.l.
 * http://www.nethesis.it - info@nethesis.it
 *
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * author: Edoardo Spadoni <edoardo.spadoni@nethesis.it>
 */

package utils

import (
	"regexp"
	"strconv"
	"strings"
	"time"
)

// The patterns are deliberately a superset of banIP's own detection regexes that can be found here:
// https://github.com/NethServer/nethsecurity/blob/main/packages/banip/files/banip-functions.sh
var (
	logIPv4Regex = regexp.MustCompile(`(?:[0-9]{1,3}\.){3}[0-9]{1,3}`)
	logIPv6Regex = regexp.MustCompile(`(?:[A-Fa-f0-9]{1,4}:{1,2}){3,7}[A-Fa-f0-9]{1,4}`)
)

func SanitizeForLog(s string) string {
	s = strings.Map(func(r rune) rune {
		if r < 0x20 || r == 0x7f {
			return -1
		}
		return r
	}, s)
	s = logIPv6Regex.ReplaceAllString(s, "<ip>")
	s = logIPv4Regex.ReplaceAllString(s, "<ip>")
	return s
}

func Contains(a string, values []string) bool {
	for _, b := range values {
		if b == a {
			return true
		}
	}
	return false
}

func Remove(a string, values []string) []string {
	for i, v := range values {
		if v == a {
			return append(values[:i], values[i+1:]...)
		}
	}
	return values
}

func EpochToHumanDate(epochTime int) string {
	i, err := strconv.ParseInt(strconv.Itoa(epochTime), 10, 64)
	if err != nil {
		return "-"
	}
	tm := time.Unix(i, 0)
	return tm.Format("2006-01-02 15:04:05")
}
