/*
Copyright (C) 2026 Nethesis S.r.l.
SPDX-License-Identifier: GPL-2.0-only
*/

package methods

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	jwt "github.com/appleboy/gin-jwt/v2"
	"github.com/gin-gonic/gin"
)

func TestUBusCallUciForbiddenConfigs(t *testing.T) {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.POST("/ubus/call", func(c *gin.Context) {
		c.Set("JWT_PAYLOAD", jwt.MapClaims{"id": "admin"})
		UBusCallAction(c)
	})

	cases := []struct {
		body          string
		wantForbidden bool
	}{
		{`{"path":"uci","method":"get","payload":{"config":"rpcd"}}`, true},
		{`{"path":"uci","method":"set","payload":{"config":"users","section":"x","values":{}}}`, true},
		{`{"path":"uci","method":"get","payload":{"config":"network"}}`, false},
		{`{"path":"uci","method":"revert","payload":{"config":"rpcd"}}`, false},
	}
	for _, tc := range cases {
		w := httptest.NewRecorder()
		req, _ := http.NewRequest(http.MethodPost, "/ubus/call", strings.NewReader(tc.body))
		req.Header.Set("Content-Type", "application/json")
		r.ServeHTTP(w, req)
		if (w.Code == http.StatusForbidden) != tc.wantForbidden {
			t.Errorf("%s: got status %d, want forbidden=%v", tc.body, w.Code, tc.wantForbidden)
		}
	}
}
