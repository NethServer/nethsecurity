/*
 * Copyright (C) 2026 Nethesis S.r.l.
 * http://www.nethesis.it - info@nethesis.it
 *
 * SPDX-License-Identifier: GPL-2.0-only
 */

package middleware

import (
	"bytes"
	"encoding/json"
	"log"
	"net/http"
	"net/http/httptest"
	"regexp"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"

	"github.com/NethServer/nethsecurity-api/configuration"
	"github.com/NethServer/nethsecurity-api/logs"
)

var ipv4Re = regexp.MustCompile(`(?:[0-9]{1,3}\.){3}[0-9]{1,3}`)

// lastIPv4 mirrors banIP's extraction: it returns the LAST IPv4 found on a
// physical log line (banip-functions.sh: ip="${ip##* }").
func lastIPv4(line string) string {
	m := ipv4Re.FindAllString(line, -1)
	if len(m) == 0 {
		return ""
	}
	return m[len(m)-1]
}

// TestLoginLogInjection reproduces the unauthenticated DoS. banIP bans EVERY IP
// found on a physical line matching its search term, so a crafted username must
// never put an attacker-chosen IP onto the failed-auth log line (whether via a
// same-line IP literal or a forged extra line). /bin/ubus is absent in the test
// env, so CheckAuthentication fails and the failed-auth log path runs.
func TestLoginLogInjection(t *testing.T) {
	const victimIP = "8.8.8.8"
	const clientIP = "127.0.0.1"
	const term = "authentication failed for user"

	cases := map[string]string{
		// IP literal smuggled into the username on the same line.
		"same line ip": `evil from ` + victimIP,
		// Newline-forged extra line carrying the term and the victim IP.
		"forged line": "x\nauthentication failed for user evil from " + victimIP + "\n",
	}

	for name, username := range cases {
		t.Run(name, func(t *testing.T) {
			configuration.Config.SecretJWT = "test-secret"

			var buf bytes.Buffer
			logs.Logs = log.New(&buf, "", 0)

			gin.SetMode(gin.TestMode)
			jwtMiddleware = nil
			r := gin.New()
			r.POST("/login", InstanceJWT().LoginHandler)

			body, _ := json.Marshal(map[string]string{"username": username, "password": "y"})
			req := httptest.NewRequest(http.MethodPost, "/login", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")
			req.RemoteAddr = clientIP + ":1234"

			w := httptest.NewRecorder()
			r.ServeHTTP(w, req)

			out := buf.String()

			sawAuthLine := false
			for _, line := range strings.Split(out, "\n") {
				if !strings.Contains(line, term) {
					continue
				}
				sawAuthLine = true
				// No term-matching line may carry the attacker's victim IP...
				if strings.Contains(line, victimIP) {
					t.Fatalf("log injection: banIP would ban victim %s from line %q", victimIP, line)
				}
				// ...and banIP must still see the genuine client IP as the source.
				if lastIPv4(line) != clientIP {
					t.Fatalf("expected client IP %s as source on line %q", clientIP, line)
				}
			}
			if !sawAuthLine {
				t.Fatalf("expected a failed-auth log line, got: %q", out)
			}
		})
	}
}
