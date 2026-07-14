/*
 * Copyright (C) 2026 Nethesis S.r.l.
 * SPDX-License-Identifier: GPL-2.0-only
 */

package methods

import "testing"

func TestSafeFilePath(t *testing.T) {
	base := "/var/run/ns-api-server/downloads"
	cases := []struct {
		name    string
		input   string
		wantOK  bool
		wantOut string
	}{
		{"legit", "upload-abc", true, base + "/upload-abc"},
		{"subdir", "sub/file", true, base + "/sub/file"},
		{"parent", "..", false, ""},
		{"parent slash", "../secret_jwt", false, ""},
		{"deep traversal", "../../../etc/shadow", false, ""},
		{"absolute contained", "/etc/shadow", true, base + "/etc/shadow"},
		{"prefix sibling", "../downloads-evil", false, ""},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			out, ok := safeFilePath(base, tc.input)
			if ok != tc.wantOK {
				t.Fatalf("safeFilePath(%q) ok=%v, want %v (out=%q)", tc.input, ok, tc.wantOK, out)
			}
			if ok && out != tc.wantOut {
				t.Fatalf("safeFilePath(%q) out=%q, want %q", tc.input, out, tc.wantOut)
			}
		})
	}
}
