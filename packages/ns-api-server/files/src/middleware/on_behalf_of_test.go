/*
 * Copyright (C) 2026 Nethesis S.r.l.
 * http://www.nethesis.it - info@nethesis.it
 *
 * SPDX-License-Identifier: GPL-2.0-only
 */

package middleware

import (
	"bytes"
	"log"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	jwt "github.com/appleboy/gin-jwt/v2"
	"github.com/gin-gonic/gin"

	"github.com/NethServer/nethsecurity-api/configuration"
	"github.com/NethServer/nethsecurity-api/logs"
	"github.com/NethServer/nethsecurity-api/models"
)

const controllerUser = "3f2a1b0c9d8e7f6a5b4c3d2e"

func stubControllerUsername(t *testing.T, username string) {
	t.Helper()
	original := getControllerUsername
	getControllerUsername = func() string { return username }
	t.Cleanup(func() { getControllerUsername = original })
}

// TestCheckOnBehalfOf: only the controller machine account can act on behalf of
// somebody else, and only with a sane value.
func TestCheckOnBehalfOf(t *testing.T) {
	cases := []struct {
		name       string
		controller string
		username   string
		onBehalfOf string
		expected   string
	}{
		{"controller delegates", controllerUser, controllerUser, "alice", "alice"},
		{"value is trimmed", controllerUser, controllerUser, "  alice  ", "alice"},
		{"another user cannot delegate", controllerUser, "root", "alice", ""},
		{"unregistered unit", "", "root", "alice", ""},
		{"no delegation requested", controllerUser, controllerUser, "", ""},
		{"delegation to itself", controllerUser, controllerUser, controllerUser, ""},
		{"value too long", controllerUser, controllerUser, strings.Repeat("a", onBehalfOfMaxLen+1), ""},
		{"forged log line", controllerUser, controllerUser, "alice\nauthentication failed for user evil from 8.8.8.8", ""},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			stubControllerUsername(t, tc.controller)

			got := checkOnBehalfOf(tc.onBehalfOf, tc.username)
			if got != tc.expected {
				t.Fatalf("expected %q, got %q", tc.expected, got)
			}
		})
	}
}

// TestOnBehalfOfClaim: the claim is stored only when set, so tokens of regular
// logins are unchanged.
func TestOnBehalfOfClaim(t *testing.T) {
	cases := map[string]string{
		"delegated login": "alice",
		"regular login":   "",
	}

	for name, onBehalfOf := range cases {
		t.Run(name, func(t *testing.T) {
			configuration.Config.SecretJWT = "test-secret"
			gin.SetMode(gin.TestMode)
			jwtMiddleware = nil

			token, _, err := InstanceJWT().TokenGenerator(&models.UserAuthorizations{
				Username:   controllerUser,
				OnBehalfOf: onBehalfOf,
			})
			if err != nil {
				t.Fatalf("cannot generate token: %v", err)
			}

			parsed, err := InstanceJWT().ParseTokenString(token)
			if err != nil {
				t.Fatalf("cannot parse token: %v", err)
			}
			claims := jwt.ExtractClaimsFromToken(parsed)

			if claims["id"] != controllerUser {
				t.Fatalf("expected identity %q, got %q", controllerUser, claims["id"])
			}

			value, present := claims[onBehalfOfKey]
			if onBehalfOf == "" {
				if present {
					t.Fatalf("expected no %s claim, got %q", onBehalfOfKey, value)
				}
				return
			}
			if value != onBehalfOf {
				t.Fatalf("expected %s claim %q, got %q", onBehalfOfKey, onBehalfOf, value)
			}
		})
	}
}

// TestOnBehalfOfLogSuffix: the operator is reported next to the machine
// account, and the client IP stays the last IPv4 so banIP bans the right source.
func TestOnBehalfOfLogSuffix(t *testing.T) {
	const clientIP = "192.168.1.10"

	configuration.Config.SecretJWT = "test-secret"
	configuration.Config.TokensDir = t.TempDir()
	configuration.Config.SecretsDir = t.TempDir()
	gin.SetMode(gin.TestMode)
	jwtMiddleware = nil

	var buf bytes.Buffer
	logs.Logs = log.New(&buf, "", 0)

	token, _, err := InstanceJWT().TokenGenerator(&models.UserAuthorizations{
		Username:   controllerUser,
		OnBehalfOf: "alice",
	})
	if err != nil {
		t.Fatalf("cannot generate token: %v", err)
	}

	c, _ := gin.CreateTestContext(httptest.NewRecorder())
	InstanceJWT().LoginResponse(c, 200, token, time.Now())

	line := strings.TrimSpace(buf.String())
	if !strings.Contains(line, "for user "+controllerUser+" on behalf of alice") {
		t.Fatalf("expected the operator next to the machine account, got %q", line)
	}

	authLine := "[INFO][AUTH] authentication success for user " + controllerUser + logSuffixOnBehalfOf("alice") + " from " + clientIP
	if lastIPv4(authLine) != clientIP {
		t.Fatalf("expected client IP %s as source on line %q", clientIP, authLine)
	}
}
