/*
Copyright (C) 2026 Nethesis S.r.l.
SPDX-License-Identifier: GPL-2.0-only
*/

package middleware

import (
	"net/http"
	"sync"
	"time"

	"github.com/fatih/structs"
	"github.com/gin-gonic/gin"
	"golang.org/x/time/rate"

	"github.com/NethServer/nethsecurity-api/logs"
	"github.com/NethServer/nethsecurity-api/response"
)

// BodyLimit rejects requests whose body exceeds maxBytes before any downstream
// binding reads it, so unauthenticated or semi-trusted routes cannot be used
// to exhaust memory with oversized payloads.
func BodyLimit(maxBytes int64) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Request.Body = http.MaxBytesReader(c.Writer, c.Request.Body, maxBytes)
		c.Next()
	}
}

const rateLimiterStaleAfter = 3 * time.Minute
const rateLimiterCleanupInterval = time.Minute

type rateLimiterVisitor struct {
	limiter  *rate.Limiter
	lastSeen time.Time
}

// RateLimiter throttles requests per client IP with a token-bucket limiter,
// so an unauthenticated route cannot be flooded with enough concurrent
// requests to exhaust memory before BodyLimit's per-request cap can help
// (BodyLimit bounds one request's body, not how many requests run at once).
// rps is the sustained rate and burst the number of requests allowed instantly.
func RateLimiter(rps rate.Limit, burst int) gin.HandlerFunc {
	visitors := make(map[string]*rateLimiterVisitor)
	var mu sync.Mutex

	go func() {
		for {
			time.Sleep(rateLimiterCleanupInterval)
			mu.Lock()
			for ip, v := range visitors {
				if time.Since(v.lastSeen) > rateLimiterStaleAfter {
					delete(visitors, ip)
				}
			}
			mu.Unlock()
		}
	}()

	return func(c *gin.Context) {
		ip := c.ClientIP()

		mu.Lock()
		v, exists := visitors[ip]
		if !exists {
			v = &rateLimiterVisitor{limiter: rate.NewLimiter(rps, burst)}
			visitors[ip] = v
		}
		v.lastSeen = time.Now()
		limiter := v.limiter
		mu.Unlock()

		if !limiter.Allow() {
			logs.Logs.Println("[INFO][AUTH] rate limit exceeded for " + ip + " on " + c.Request.URL.Path)
			c.JSON(http.StatusTooManyRequests, structs.Map(response.StatusTooManyRequests{
				Code:    http.StatusTooManyRequests,
				Message: "too many requests",
				Data:    nil,
			}))
			c.Abort()
			return
		}

		c.Next()
	}
}
