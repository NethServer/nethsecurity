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
	"github.com/NethServer/nethsecurity-api/sudo"
	"io"
	"net/http"

	"github.com/fatih/structs"
	"github.com/gin-contrib/cors"
	"github.com/gin-contrib/gzip"
	"github.com/gin-gonic/gin"
	"github.com/robfig/cron/v3"

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

	// add default compression
	router.Use(gzip.Gzip(gzip.DefaultCompression))

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

	// define login and logout endpoint
	api.POST("/login", middleware.InstanceJWT().LoginHandler)
	api.POST("/logout", middleware.InstanceJWT().LogoutHandler)

	// 2FA APIs
	api.POST("/2fa/otp-verify", methods.OTPVerify)

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
