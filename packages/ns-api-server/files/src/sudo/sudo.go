/*
Copyright (C) 2025 Nethesis S.r.l.
SPDX-License-Identifier: GPL-2.0-only
*/

package sudo

import (
	"github.com/NethServer/nethsecurity-api/methods"
	"github.com/NethServer/nethsecurity-api/middleware"
	"github.com/NethServer/nethsecurity-api/models"
	"github.com/NethServer/nethsecurity-api/response"
	jwt "github.com/appleboy/gin-jwt/v2"
	"github.com/fatih/structs"
	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
	"net/http"
)

type ValidationEntry struct {
	Message   string `json:"message" structs:"message"`
	Value     string `json:"value" structs:"value"`
	Parameter string `json:"parameter" structs:"parameter"`
}

type ValidationBag struct {
	Errors []ValidationEntry `json:"errors" structs:"errors"`
}

type ValidationResponse struct {
	Validation ValidationBag `json:"validation" structs:"validation"`
}

// EnableSudo Function to be called in an authenticated route, returns a JWT token with sudo privileges
func EnableSudo(c *gin.Context) {
	// Extract claims from JWT
	claims := jwt.ExtractClaims(c)
	// Get username and 2FA status from claims
	username := claims["id"].(string)

	// Check if password sent is valid
	var jsonRequest struct {
		Password string `json:"password" structs:"password"`
	}
	err := c.ShouldBindWith(&jsonRequest, binding.JSON)
	if err != nil {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Message: "validation_failed",
		}))
		c.Abort()
		return
	}
	fail := methods.CheckAuthentication(username, jsonRequest.Password)
	if fail != nil {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    http.StatusBadRequest,
			Message: "validation_failed",
			Data: ValidationResponse{
				ValidationBag{
					Errors: []ValidationEntry{
						{
							Message:   "invalid_password",
							Parameter: "password",
							Value:     "",
						},
					},
				},
			},
		}))
		c.Abort()
		return
	}
	token, _, err := middleware.InstanceJWT().TokenGenerator(&models.UserAuthorizations{
		Username:      username,
		SudoRequested: true,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, structs.Map(response.StatusInternalServerError{
			Code:    http.StatusInternalServerError,
			Message: "Impossible to generate token",
		}))
		c.Abort()
		return
	}
	methods.SetTokenValidation(username, token)
	c.JSON(http.StatusOK, structs.Map(response.StatusOK{
		Message: "sudo_enabled",
		Data: struct {
			Token string `structs:"token"`
		}{
			Token: token,
		},
	}))
}
