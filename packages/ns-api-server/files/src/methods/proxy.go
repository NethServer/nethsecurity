/*
Copyright (C) 2026 Nethesis S.r.l.
SPDX-License-Identifier: GPL-2.0-only
*/

package methods

import (
	"encoding/json"
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"
	"time"

	"github.com/NethServer/nethsecurity-api/logs"
	"github.com/NethServer/nethsecurity-api/response"
	"github.com/fatih/structs"
	"github.com/gin-gonic/gin"
)

// NewReverseProxy builds a reverse proxy to a local, unauthenticated backend
func NewReverseProxy(rawBaseURL string) *httputil.ReverseProxy {
	target, err := url.Parse(rawBaseURL)
	if err != nil {
		logs.Logs.Println("[CRITICAL][PROXY] invalid backend URL:", rawBaseURL, err.Error())
	}

	proxy := httputil.NewSingleHostReverseProxy(target)
	proxy.Transport = &http.Transport{
		ResponseHeaderTimeout: 10 * time.Second,
	}
	proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		logs.Logs.Println("[ERROR][PROXY] backend unreachable:", err.Error())
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadGateway)
		json.NewEncoder(w).Encode(structs.Map(response.StatusBadGateway{
			Code:    502,
			Message: "bad gateway",
			Data:    nil,
		}))
	}

	// The API server owns CORS (see main.go)
	// strip any CORS headers the backend sets (e.g. VictoriaMetrics adds Access-Control-Allow-Origin) 
	// so they don't duplicate and trigger a browser "multiple values" CORS error
	proxy.ModifyResponse = func(resp *http.Response) error {
		for key := range resp.Header {
			if strings.HasPrefix(http.CanonicalHeaderKey(key), "Access-Control-") {
				resp.Header.Del(key)
			}
		}
		return nil
	}

	return proxy
}

// ProxyTo returns a handler that forwards the request to proxy at the given
// fixed backendPath, passing the query string through unchanged. It is meant
// to be registered against a single hardcoded path (e.g. authGroup.GET
// ("/metrics/query", ProxyTo(...))) - it does not accept caller-controlled
// path segments.
func ProxyTo(proxy *httputil.ReverseProxy, backendPath string) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Request.Header.Del("Authorization")
		c.Request.Header.Del("Cookie")
		// Let the API server's gzip middleware be the single compression layer.
		// Without this the backend (VictoriaMetrics) would compress too, and the
		// middleware would compress again, yielding a double-gzipped body.
		c.Request.Header.Del("Accept-Encoding")
		c.Request.URL.Path = backendPath
		proxy.ServeHTTP(c.Writer, c.Request)
	}
}
