/*
 * Copyright (C) 2023 Nethesis S.r.l.
 * http://www.nethesis.it - info@nethesis.it
 *
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * author: Edoardo Spadoni <edoardo.spadoni@nethesis.it>
 */

package middleware

import (
	"bytes"
	"io"
	"regexp"
	"strings"
	"time"

	"github.com/fatih/structs"
	"github.com/gin-gonic/gin"

	jwt "github.com/appleboy/gin-jwt/v2"

	"github.com/NethServer/nethsecurity-api/configuration"
	"github.com/NethServer/nethsecurity-api/logs"
	"github.com/NethServer/nethsecurity-api/methods"
	"github.com/NethServer/nethsecurity-api/models"
	"github.com/NethServer/nethsecurity-api/response"
	"github.com/NethServer/nethsecurity-api/utils"
)

type login struct {
	Username string `form:"username" json:"username" binding:"required"`
	Password string `form:"password" json:"password" binding:"required"`
}

var jwtMiddleware *jwt.GinJWTMiddleware
var identityKey = "id"

func InstanceJWT() *jwt.GinJWTMiddleware {
	if jwtMiddleware == nil {
		jwtMiddleware := InitJWT()
		return jwtMiddleware
	}
	return jwtMiddleware
}

func InitJWT() *jwt.GinJWTMiddleware {
	// define jwt middleware
	authMiddleware, errDefine := jwt.New(&jwt.GinJWTMiddleware{
		Realm:       "nethserver",
		Key:         []byte(configuration.Config.SecretJWT),
		Timeout:     time.Hour * 24, // 1 day
		MaxRefresh:  time.Hour * 24, // 1 day
		IdentityKey: identityKey,
		Authenticator: func(c *gin.Context) (interface{}, error) {
			// check login credentials exists
			var loginVals login
			if err := c.ShouldBind(&loginVals); err != nil {
				return "", jwt.ErrMissingLoginValues
			}

			// set login credentials
			username := loginVals.Username
			password := loginVals.Password

			// check login
			err := methods.CheckAuthentication(username, password)
			if err != nil {
				// login failed, write also the IP address of the client
				logs.Logs.Println("[INFO][AUTH] authentication failed for user " + utils.SanitizeForLog(username) + " from " + c.ClientIP() + ": " + err.Error())

				// return JWT error
				return nil, jwt.ErrFailedAuthentication
			}

			// login ok action
			logs.Logs.Println("[INFO][AUTH] authentication success for user " + utils.SanitizeForLog(username) + " from " + c.ClientIP())

			// return user auth model
			return &models.UserAuthorizations{
				Username: username,
			}, nil

		},
		PayloadFunc: func(data interface{}) jwt.MapClaims {
			// read current user
			if user, ok := data.(*models.UserAuthorizations); ok {
				// check if user require 2fa
				status, _ := methods.GetUserStatus(user.Username)

				if user.SudoRequested {
					// create claims map
					return jwt.MapClaims{
						identityKey: user.Username,
						"role":      "",
						"actions":   []string{},
						"2fa":       status == "1",
						"sudo":      time.Now().Unix(),
					}
				}
				return jwt.MapClaims{
					identityKey: user.Username,
					"role":      "",
					"actions":   []string{},
					"2fa":       status == "1",
				}
			}

			// return claims map
			return jwt.MapClaims{}
		},
		IdentityHandler: func(c *gin.Context) interface{} {
			// handle identity and extract claims
			claims := jwt.ExtractClaims(c)

			// create user object
			user := &models.UserAuthorizations{
				Username: claims[identityKey].(string),
				Role:     "admin",
				Actions:  nil,
			}

			// return user
			return user
		},
		Authorizator: func(data interface{}, c *gin.Context) bool {
			// check token validation
			claims, _ := InstanceJWT().GetClaimsFromJWT(c)
			token, _ := InstanceJWT().ParseToken(c)

			// log request and body
			reqMethod := c.Request.Method
			reqURI := c.Request.RequestURI

			// check if token exists
			if !methods.CheckTokenValidation(claims["id"].(string), token.Raw) {
				// write logs
				logs.Logs.Println("[INFO][AUTH] authorization failed for user " + utils.SanitizeForLog(claims["id"].(string)) + ". " + reqMethod + " " + reqURI)

				// not authorized
				return false
			}

			// extract body
			reqBody := ""
			// if reqURI contains /files path, just replace the body with a static string to avoid logging the file content
			if strings.Contains(reqURI, "/files") {
				reqBody = "<file>"
			}
			if reqBody != "<file>" && (reqMethod == "POST" || reqMethod == "PUT") {
				// extract body
				var buf bytes.Buffer
				tee := io.TeeReader(c.Request.Body, &buf)
				body, _ := io.ReadAll(tee)
				c.Request.Body = io.NopCloser(&buf)

				// get JSON string body
				jsonB := string(body)

				// remove all spaces
				jsonB = strings.ReplaceAll(jsonB, " ", "")

				// create regex for sensitive words
				for _, s := range configuration.Config.SensitiveList {
					// create regex
					r1 := regexp.MustCompile(`"` + s + `":"(.*?)"`) // match "token|password|secret":"<sensitive>"
					r2 := regexp.MustCompile(`"` + s + `","(.*?)"`) // match "token|password|secret","<sensitive>"

					// apply regex
					jsonB = r1.ReplaceAllString(jsonB, `"`+s+`":"XXX"`)
					jsonB = r2.ReplaceAllString(jsonB, `"`+s+`":"XXX"`)
				}

				// compose req body
				reqBody = jsonB
			}

			logs.Logs.Println("[INFO][AUTH] authorization success for user " + utils.SanitizeForLog(claims["id"].(string)) + ". " + reqMethod + " " + reqURI + " " + utils.SanitizeForLog(reqBody))

			// authorized
			return true
		},
		LoginResponse: func(c *gin.Context, code int, token string, t time.Time) {
			//get claims
			tokenObj, _ := InstanceJWT().ParseTokenString(token)
			claims := jwt.ExtractClaimsFromToken(tokenObj)

			// set token to valid, if not 2FA
			if !claims["2fa"].(bool) {
				methods.SetTokenValidation(claims["id"].(string), token)
			}

			// write logs
			logs.Logs.Println("[INFO][AUTH] login response success for user " + utils.SanitizeForLog(claims["id"].(string)))

			// return 200 OK
			c.JSON(200, gin.H{"code": 200, "expire": t, "token": token})
		},
		RefreshResponse: func(c *gin.Context, code int, token string, t time.Time) {
			//get claims
			tokenObj, _ := InstanceJWT().ParseTokenString(token)
			claims := jwt.ExtractClaimsFromToken(tokenObj)

			// set token to valid
			methods.SetTokenValidation(claims["id"].(string), token)

			// write logs
			logs.Logs.Println("[INFO][AUTH] refresh response success for user " + utils.SanitizeForLog(claims["id"].(string)))

			// return 200 OK
			c.JSON(200, gin.H{"code": 200, "expire": t, "token": token})
		},
		LogoutResponse: func(c *gin.Context, code int) {
			//get claims
			tokenObj, _ := InstanceJWT().ParseToken(c)
			claims := jwt.ExtractClaimsFromToken(tokenObj)

			// set token to invalid
			methods.DelTokenValidation(claims["id"].(string), tokenObj.Raw)

			// write logs
			logs.Logs.Println("[INFO][AUTH] logout response success for user " + utils.SanitizeForLog(claims["id"].(string)))

			// reutrn 200 OK
			c.JSON(200, gin.H{"code": 200})
		},
		Unauthorized: func(c *gin.Context, code int, message string) {
			// write logs
			logs.Logs.Println("[INFO][AUTH] unauthorized request: " + utils.SanitizeForLog(message))

			// response not authorized
			c.JSON(code, structs.Map(response.StatusUnauthorized{
				Code:    code,
				Message: message,
				Data:    nil,
			}))
			return
		},
		TokenLookup:   "header: Authorization, token: jwt",
		TokenHeadName: "Bearer",
		TimeFunc:      time.Now,
	})

	// check middleware errors
	if errDefine != nil {
		logs.Logs.Println("[ERR][AUTH] middleware definition error: " + errDefine.Error())
	}

	// init middleware
	errInit := authMiddleware.MiddlewareInit()

	// check error on initialization
	if errInit != nil {
		logs.Logs.Println("[ERR][AUTH] middleware initialization error: " + errInit.Error())
	}

	// return object
	return authMiddleware
}
