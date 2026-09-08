/*
Copyright (C) 2026 Nethesis S.r.l.
SPDX-License-Identifier: GPL-2.0-only
*/

package methods

import (
	"io"
	"log"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/NethServer/nethsecurity-api/logs"
	"github.com/gin-gonic/gin"
)

// proxy.go logs backend errors; logs.Logs is otherwise only set up in main().
func TestMain(m *testing.M) {
	logs.Logs = log.New(os.Stderr, "test ", 0)
	os.Exit(m.Run())
}

// httputil.ReverseProxy needs a real ResponseWriter (CloseNotifier/Flusher),
// which httptest.NewRecorder doesn't implement.
func startTestServer(t *testing.T, r *gin.Engine) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(r)
	t.Cleanup(srv.Close)
	return srv
}

func TestProxyToForwardsRequest(t *testing.T) {
	gin.SetMode(gin.TestMode)

	var gotPath, gotQuery, gotAuth, gotCookie string
	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		gotQuery = r.URL.RawQuery
		gotAuth = r.Header.Get("Authorization")
		gotCookie = r.Header.Get("Cookie")
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"success"}`))
	}))
	defer backend.Close()

	r := gin.New()
	r.GET("/x", ProxyTo(NewReverseProxy(backend.URL), "/api/v1/query"))
	srv := startTestServer(t, r)

	req, _ := http.NewRequest(http.MethodGet, srv.URL+"/x?query=up", nil)
	req.Header.Set("Authorization", "Bearer secret-jwt")
	req.Header.Set("Cookie", "session=abc")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)

	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status = %d, want %d", resp.StatusCode, http.StatusOK)
	}
	if string(body) != `{"status":"success"}` {
		t.Fatalf("body = %q, want backend body passed through", string(body))
	}
	if resp.Header.Get("Content-Type") != "application/json" {
		t.Fatalf("Content-Type = %q, want application/json", resp.Header.Get("Content-Type"))
	}
	if gotPath != "/api/v1/query" {
		t.Fatalf("backend received path = %q, want /api/v1/query", gotPath)
	}
	if gotQuery != "query=up" {
		t.Fatalf("backend received query = %q, want query=up", gotQuery)
	}
	if gotAuth != "" {
		t.Fatalf("backend received Authorization header %q, want it stripped", gotAuth)
	}
	if gotCookie != "" {
		t.Fatalf("backend received Cookie header %q, want it stripped", gotCookie)
	}
}

func TestProxyToBackendUnreachable(t *testing.T) {
	gin.SetMode(gin.TestMode)

	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {}))
	backendURL := backend.URL
	backend.Close() // nothing is listening on this address anymore

	r := gin.New()
	r.GET("/x", ProxyTo(NewReverseProxy(backendURL), "/api/v1/query"))
	srv := startTestServer(t, r)

	resp, err := http.Get(srv.URL + "/x")
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusBadGateway {
		t.Fatalf("status = %d, want %d", resp.StatusCode, http.StatusBadGateway)
	}
	if resp.Header.Get("Content-Type") != "application/json" {
		t.Fatalf("Content-Type = %q, want application/json", resp.Header.Get("Content-Type"))
	}
}

func TestNewReverseProxyResponseHeaderTimeout(t *testing.T) {
	proxy := NewReverseProxy("http://127.0.0.1:8428")

	transport, ok := proxy.Transport.(*http.Transport)
	if !ok {
		t.Fatalf("Transport = %T, want *http.Transport", proxy.Transport)
	}
	if transport.ResponseHeaderTimeout != 10*time.Second {
		t.Fatalf("ResponseHeaderTimeout = %s, want 10s", transport.ResponseHeaderTimeout)
	}
}

// Mirrors main.go's route table: any method is forwarded on the three registered
// paths, everything else 404s regardless of method.
func TestMinimalRouteTableRejectsEverythingElse(t *testing.T) {
	gin.SetMode(gin.TestMode)

	backend := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer backend.Close()

	victoriaMetricsProxy := NewReverseProxy(backend.URL)
	r := gin.New()
	r.Any("/metrics/query", ProxyTo(victoriaMetricsProxy, "/api/v1/query"))
	r.Any("/metrics/query_range", ProxyTo(victoriaMetricsProxy, "/api/v1/query_range"))
	r.Any("/alerts/alerts", ProxyTo(NewReverseProxy(backend.URL), "/api/v1/alerts"))
	srv := startTestServer(t, r)

	allowed := []struct {
		method string
		path   string
	}{
		{http.MethodGet, "/metrics/query"},
		{http.MethodPost, "/metrics/query"},
		{http.MethodPut, "/metrics/query"},
		{http.MethodGet, "/metrics/query_range"},
		{http.MethodPost, "/metrics/query_range"},
		{http.MethodGet, "/alerts/alerts"},
		{http.MethodPost, "/alerts/alerts"},
	}
	for _, tc := range allowed {
		req, _ := http.NewRequest(tc.method, srv.URL+tc.path, nil)
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			t.Fatalf("%s %s: request failed: %v", tc.method, tc.path, err)
		}
		resp.Body.Close()
		if resp.StatusCode != http.StatusOK {
			t.Fatalf("%s %s: status = %d, want %d", tc.method, tc.path, resp.StatusCode, http.StatusOK)
		}
	}

	rejected := []struct {
		method string
		path   string
	}{
		{http.MethodGet, "/metrics/admin/tsdb/delete_series"},
		{http.MethodGet, "/metrics/admin/tsdb/snapshot"},
		{http.MethodPost, "/metrics/admin/tsdb/delete_series"},
		{http.MethodGet, "/alerts/-/reload"},
		{http.MethodGet, "/bogus"},
		{http.MethodPost, "/bogus"},
	}
	for _, tc := range rejected {
		req, _ := http.NewRequest(tc.method, srv.URL+tc.path, nil)
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			t.Fatalf("%s %s: request failed: %v", tc.method, tc.path, err)
		}
		resp.Body.Close()
		if resp.StatusCode != http.StatusNotFound {
			t.Fatalf("%s %s: status = %d, want %d", tc.method, tc.path, resp.StatusCode, http.StatusNotFound)
		}
	}
}
