/*
 * Copyright (C) 2024 Nethesis S.r.l.
 * http://www.nethesis.it - info@nethesis.it
 *
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * author: Edoardo Spadoni <edoardo.spadoni@nethesis.it>
 */

package main

import (
	"io"
	"net/http"

	"github.com/NethServer/nethsecurity-api/sudo"

	"github.com/fatih/structs"
	"github.com/gin-contrib/cors"
	"github.com/gin-contrib/gzip"
	"github.com/gin-gonic/gin"
	"github.com/robfig/cron/v3"
	"golang.org/x/time/rate"

	"github.com/NethServer/nethsecurity-api/configuration"
	"github.com/NethServer/nethsecurity-api/logs"
	"github.com/NethServer/nethsecurity-api/methods"
	"github.com/NethServer/nethsecurity-api/middleware"
	"github.com/NethServer/nethsecurity-api/response"
)

// @title NethSecurity StandAlone API Server
// @version 1.0
// @description NethSecurity StandAlone API Server is used to create manage stand-alone NethSecurity instance
// @termsOfService https://nethserver.org/terms/

// @contact.name NethServer Developer Team
// @contact.url https://nethserver.org/support

// @license.name GNU GENERAL PUBLIC LICENSE

// @host localhost:8080
// @schemes http
// @BasePath /api

func main() {
	// init logs with syslog
	logs.Init("nethsecurity_api")

	// init configuration
	configuration.Init()

	// disable log to stdout when running in release mode
	if gin.Mode() == gin.ReleaseMode {
		gin.DefaultWriter = io.Discard
	}

	// init routers
	router := gin.Default()

	// add default compression, excluding file downloads/uploads: DownloadFile
	// sets Content-Length manually and gzip re-encoding an already-compressed
	// archive on top of it causes a Content-Length mismatch on the client
	router.Use(gzip.Gzip(gzip.DefaultCompression, gzip.WithExcludedPaths([]string{"/api/files"})))

	// accept headers only from localhost
	router.SetTrustedProxies([]string{"127.0.0.1", "::1"})

	// Generous global per-IP rate limit as a coarse safety net across all
	// routes (a looser second layer behind the tighter per-route body limits
	// on the pre-auth routes below). Set GLOBAL_RATE_LIMIT_AVERAGE=0 to disable.
	if configuration.Config.GlobalRateLimitAverage > 0 {
		router.Use(middleware.RateLimiter(
			rate.Limit(configuration.Config.GlobalRateLimitAverage),
			configuration.Config.GlobalRateLimitBurst,
		))
	}

	// cors configuration only in debug mode GIN_MODE=debug (default)
	if gin.Mode() == gin.DebugMode {
		// gin gonic cors conf
		corsConf := cors.DefaultConfig()
		corsConf.AllowHeaders = []string{"Authorization", "Content-Type", "Accept"}
		corsConf.AllowAllOrigins = true
		router.Use(cors.New(corsConf))
	}

	// define api group
	api := router.Group("/api")

	// define login and logout endpoint. BodyLimit caps each request's size;
	// the global per-IP rate limiter (see above) bounds request frequency
	// across every route, including these pre-authentication ones.
	api.POST("/login", middleware.BodyLimit(32<<10), middleware.InstanceJWT().LoginHandler)
	api.POST("/logout", middleware.BodyLimit(1<<10), middleware.InstanceJWT().LogoutHandler)

	// 2FA APIs
	api.POST("/2fa/otp-verify", middleware.BodyLimit(32<<10), methods.OTPVerify)

	// define JWT middleware
	authGroup := api.Group("/", middleware.InstanceJWT().MiddlewareFunc())
	// allow user to request sudo mode
	authGroup.POST("/sudo", sudo.EnableSudo)
	// refresh handler
	authGroup.GET("/refresh", middleware.InstanceJWT().RefreshHandler)

	// ubus wrapper
	authGroup.POST("/ubus/call", middleware.SudoUbusCallsMiddleware(), methods.UBusCallAction)

	// 2FA APIs
	authGroup.GET("/2fa", methods.Get2FAStatus)
	authGroup.DELETE("/2fa", middleware.SudoModeMiddleware(), methods.Del2FAStatus)
	authGroup.GET("/2fa/recovery-codes", middleware.SudoModeMiddleware(), methods.Get2FARecoveryCodes)
	authGroup.GET("/2fa/qr-code", middleware.SudoModeMiddleware(), methods.QRCode)

	// files handler
	authGroup.GET("/files/:filename", methods.DownloadFile)
	authGroup.POST("/files", methods.UploadFile)
	authGroup.DELETE("/files/:filename", methods.DeleteFile)

	// reverse proxies to VictoriaMetrics/vmalert
	victoriaMetricsProxy := methods.NewReverseProxy(configuration.Config.VictoriaMetricsURL)
	authGroup.Any("/metrics/query", methods.ProxyTo(victoriaMetricsProxy, "/api/v1/query"))
	authGroup.Any("/metrics/query_range", methods.ProxyTo(victoriaMetricsProxy, "/api/v1/query_range"))
	authGroup.Any("/alerts/alerts", methods.ProxyTo(methods.NewReverseProxy(configuration.Config.VMAlertURL), "/api/v1/alerts"))

	// handle missing endpoint
	router.NoRoute(func(c *gin.Context) {
		c.JSON(http.StatusNotFound, structs.Map(response.StatusNotFound{
			Code:    404,
			Message: "API not found",
			Data:    nil,
		}))
	})

	// run expired token cleanup, on startup
	methods.DeleteExpiredTokens()

	// create cron to run daily
	c := cron.New()
	c.AddFunc("@daily", methods.DeleteExpiredTokens)
	c.Start()

	// run server
	router.Run(configuration.Config.ListenAddress)
}
