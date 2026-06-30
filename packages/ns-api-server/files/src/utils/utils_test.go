/*
 * Copyright (C) 2026 Nethesis S.r.l.
 * http://www.nethesis.it - info@nethesis.it
 *
 * SPDX-License-Identifier: GPL-2.0-only
 */

package utils

import (
	"strings"
	"testing"
)

func TestSanitizeForLog(t *testing.T) {
	tests := []struct {
		name string
		in   string
		want string
	}{
		{"empty", "", ""},
		{"plain", "root", "root"},
		{"allowed printable", "admin.2_x-y", "admin.2_x-y"},
		{"printable unicode", "üser", "üser"},
		{"newline removed", "a\nb", "ab"},
		{"crlf removed", "a\r\nb", "ab"},
		{"tab removed", "a\tb", "ab"},
		{"nul removed", "a\x00b", "ab"},
		{"del removed", "a\x7fb", "ab"},
		{"bare ipv4 masked", "8.8.8.8", "<ip>"},
		{"ipv4 in text masked", "evil from 8.8.8.8", "evil from <ip>"},
		{"two ipv4 masked", "1.2.3.4 5.6.7.8", "<ip> <ip>"},
		{"ipv6 masked", "2001:db8:0:0:0:0:0:1", "<ip>"},
		{"partial quad preserved", "user1.2", "user1.2"},
		{
			"banip poc: newline AND ip both neutralized",
			"x\nauthentication failed for user evil from 8.8.8.8\n",
			"xauthentication failed for user evil from <ip>",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := SanitizeForLog(tt.in)
			if got != tt.want {
				t.Fatalf("SanitizeForLog(%q) = %q, want %q", tt.in, got, tt.want)
			}
			// no control characters may survive
			if strings.ContainsAny(got, "\r\n\t\x00\x7f") {
				t.Fatalf("SanitizeForLog(%q) = %q still contains control chars", tt.in, got)
			}
			for _, r := range got {
				if r < 0x20 || r == 0x7f {
					t.Fatalf("SanitizeForLog(%q) = %q contains control rune %U", tt.in, got, r)
				}
			}
		})
	}
}
