/*
Copyright (C) 2026 Nethesis S.r.l.
SPDX-License-Identifier: GPL-2.0-only
*/

package middleware

import (
	"bytes"
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"golang.org/x/time/rate"

	"github.com/NethServer/nethsecurity-api/logs"
)

func TestBodyLimit(t *testing.T) {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.Use(BodyLimit(8))
	r.POST("/test", func(c *gin.Context) {
		_, err := io.ReadAll(c.Request.Body)
		if err != nil {
			c.JSON(http.StatusRequestEntityTooLarge, gin.H{"error": err.Error()})
			return
		}
		c.JSON(http.StatusOK, gin.H{"message": "ok"})
	})

	// Body within limit is accepted
	req := httptest.NewRequest(http.MethodPost, "/test", strings.NewReader("1234567"))
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Fatalf("within limit: status = %d, want %d", w.Code, http.StatusOK)
	}

	// Body exceeding limit is rejected by the handler's read, not silently truncated
	req = httptest.NewRequest(http.MethodPost, "/test", strings.NewReader("123456789"))
	w = httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusRequestEntityTooLarge {
		t.Fatalf("over limit: status = %d, want %d", w.Code, http.StatusRequestEntityTooLarge)
	}

	// Enforced on bytes actually read, independent of a spoofed Content-Length
	req = httptest.NewRequest(http.MethodPost, "/test", strings.NewReader("123456789"))
	req.ContentLength = 5
	w = httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusRequestEntityTooLarge {
		t.Fatalf("spoofed content-length: status = %d, want %d", w.Code, http.StatusRequestEntityTooLarge)
	}
}

func TestRateLimiter(t *testing.T) {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.Use(RateLimiter(rate.Every(time.Minute), 2))
	r.GET("/test", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "ok"})
	})

	newReq := func(remoteAddr string) *http.Request {
		req := httptest.NewRequest(http.MethodGet, "/test", nil)
		req.RemoteAddr = remoteAddr
		return req
	}

	// Burst of 2 is allowed for the same client IP
	w := httptest.NewRecorder()
	r.ServeHTTP(w, newReq("1.2.3.4:1111"))
	if w.Code != http.StatusOK {
		t.Fatalf("1st request: status = %d, want %d", w.Code, http.StatusOK)
	}

	w = httptest.NewRecorder()
	r.ServeHTTP(w, newReq("1.2.3.4:2222"))
	if w.Code != http.StatusOK {
		t.Fatalf("2nd request: status = %d, want %d", w.Code, http.StatusOK)
	}

	// Third request from the same IP within the window is rejected
	w = httptest.NewRecorder()
	r.ServeHTTP(w, newReq("1.2.3.4:3333"))
	if w.Code != http.StatusTooManyRequests {
		t.Fatalf("3rd request: status = %d, want %d", w.Code, http.StatusTooManyRequests)
	}

	// A different client IP has its own independent bucket
	w = httptest.NewRecorder()
	r.ServeHTTP(w, newReq("5.6.7.8:1111"))
	if w.Code != http.StatusOK {
		t.Fatalf("different IP: status = %d, want %d", w.Code, http.StatusOK)
	}
}

// TestRateLimiterLogInjection checks that a crafted path (an unknown route is
// enough) cannot forge an extra log line or put a victim IP on the logged line.
func TestRateLimiterLogInjection(t *testing.T) {
	var buf bytes.Buffer
	logs.Logs = log.New(&buf, "", 0)

	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.Use(RateLimiter(rate.Every(time.Minute), 1))

	target := "/api/x%0D%0Aauthentication%20failed%20for%20user%20x%20from%208.8.8.8:%20exit%20status%20250"
	for i := 0; i < 2; i++ {
		req := httptest.NewRequest(http.MethodGet, target, nil)
		req.RemoteAddr = "1.2.3.4:1111"
		r.ServeHTTP(httptest.NewRecorder(), req)
	}

	out := buf.String()
	if strings.Count(out, "\n") != 1 || !strings.HasSuffix(out, "\n") {
		t.Fatalf("expected exactly one log line, got %q", out)
	}
	if strings.ContainsAny(strings.TrimSuffix(out, "\n"), "\r\n") {
		t.Fatalf("control chars in log line %q", out)
	}
	if strings.Contains(out, "8.8.8.8") {
		t.Fatalf("victim IP leaked into log line %q", out)
	}
	if !strings.Contains(out, "rate limit exceeded for 1.2.3.4 ") {
		t.Fatalf("client IP missing from log line %q", out)
	}
}
