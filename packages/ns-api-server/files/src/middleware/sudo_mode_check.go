/*
Copyright (C) 2025 Nethesis S.r.l.
SPDX-License-Identifier: GPL-2.0-only
*/

package middleware

import (
	"github.com/NethServer/nethsecurity-api/response"
	jwt "github.com/appleboy/gin-jwt/v2"
	"github.com/fatih/structs"
	"github.com/gin-gonic/gin"
	"net/http"
	"time"
)

// SudoModeMiddleware is used by general API endpoints to check for superuser token
func SudoModeMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		SudoCheckToken(c)
	}
}

// SudoCheckToken checks if the `sudo` claim is present and less than 5 minutes ago
func SudoCheckToken(c *gin.Context) {
	// Get JWT claims
	claims := jwt.ExtractClaims(c)
	// Check if `sudo` was less than 5 minutes ago or `sudo` is not present
	if claims["sudo"] == nil || time.Now().Unix()-int64(claims["sudo"].(float64)) > 300 {
		c.JSON(http.StatusForbidden, structs.Map(response.StatusForbidden{
			Message: "sudo mode required",
		}))
		c.Abort()
		return
	}
	// Else, continue
	c.Next()
}
