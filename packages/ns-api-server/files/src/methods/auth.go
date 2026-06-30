/*
 * Copyright (C) 2023 Nethesis S.r.l.
 * http://www.nethesis.it - info@nethesis.it
 *
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * author: Edoardo Spadoni <edoardo.spadoni@nethesis.it>
 */

package methods

import (
	"crypto/rand"
	"encoding/base32"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"strings"

	"github.com/Jeffail/gabs/v2"
	jwt "github.com/appleboy/gin-jwt/v2"
	"github.com/dgryski/dgoogauth"
	"github.com/fatih/structs"
	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
	jwtl "github.com/golang-jwt/jwt"

	"github.com/NethServer/nethsecurity-api/configuration"
	"github.com/NethServer/nethsecurity-api/logs"
	"github.com/NethServer/nethsecurity-api/models"
	"github.com/NethServer/nethsecurity-api/response"
	"github.com/NethServer/nethsecurity-api/utils"
)

func CheckAuthentication(username string, password string) error {
	// define login object
	login := models.UserLogin{
		Username: username,
		Password: password,
		Timeout:  1,
	}
	jsonLogin, _ := json.Marshal(login)

	// execute login command on ubus
	_, err := exec.Command("/bin/ubus", "call", "session", "login", string(jsonLogin)).Output()

	if err != nil {
		return err
	}

	return nil
}

func OTPVerify(c *gin.Context) {
	// get payload
	var jsonOTP models.OTPJson
	if err := c.ShouldBindBodyWith(&jsonOTP, binding.JSON); err != nil {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    400,
			Message: "request fields malformed",
			Data:    err.Error(),
		}))
		return
	}

	// verify JWT
	if !ValidateAuth(jsonOTP.Token, false) {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    400,
			Message: "JWT token invalid",
			Data:    "",
		}))
		return
	}

	// get secret for the user
	secret := GetUserSecret(jsonOTP.Username)

	// check secret
	if len(secret) == 0 {
		c.JSON(http.StatusNotFound, structs.Map(response.StatusNotFound{
			Code:    404,
			Message: "user secret not found",
			Data:    "",
		}))
		return
	}

	// set OTP configuration
	otpc := &dgoogauth.OTPConfig{
		Secret:      secret,
		WindowSize:  3,
		HotpCounter: 0,
	}

	// verifiy OTP
	result, err := otpc.Authenticate(jsonOTP.OTP)
	if err != nil || !result {

		// check if OTP is a recovery code
		recoveryCodes := GetRecoveryCodes(jsonOTP.Username)

		if !utils.Contains(jsonOTP.OTP, recoveryCodes) {
			// compose validation error
			jsonParsed, _ := gabs.ParseJSON([]byte(`{
				"validation": {
				  "errors": [
					{
					  "message": "invalid_otp",
					  "parameter": "otp",
					  "value": ""
					}
				  ]
				}
			}`))

			// return validation error
			c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
				Code:    400,
				Message: "validation_failed",
				Data:    jsonParsed,
			}))
			return
		}

		// remove used recovery OTP
		recoveryCodes = utils.Remove(jsonOTP.OTP, recoveryCodes)

		// update recovery codes file
		if !UpdateRecoveryCodes(jsonOTP.Username, recoveryCodes) {
			c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
				Code:    400,
				Message: "OTP recovery codes not updated",
				Data:    "",
			}))
			return
		}

	}

	// check if 2FA was disabled
	status, _ := os.ReadFile(configuration.Config.SecretsDir + "/" + jsonOTP.Username + "/status")
	statusOld := strings.TrimSpace(string(status[:]))

	// then clean all previous tokens
	if statusOld == "0" || statusOld == "" {
		// open file
		f, _ := os.OpenFile(configuration.Config.TokensDir+"/"+jsonOTP.Username, os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0600)
		defer f.Close()

		// write file with tokens
		_, err := f.WriteString("")

		// check error
		if err != nil {
			c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
				Code:    400,
				Message: "clean previous tokens error",
				Data:    err,
			}))
			return
		}
	}

	// set auth token to valid
	if !SetTokenValidation(jsonOTP.Username, jsonOTP.Token) {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    400,
			Message: "token validation set error",
			Data:    "",
		}))
		return
	}

	// set 2FA to enabled
	f, _ := os.OpenFile(configuration.Config.SecretsDir+"/"+jsonOTP.Username+"/status", os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0600)
	defer f.Close()

	// write file with 2fa status
	_, err = f.WriteString("1")

	// check error
	if err != nil {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    400,
			Message: "status set error",
			Data:    err,
		}))
		return
	}

	// response
	c.JSON(http.StatusOK, structs.Map(response.StatusOK{
		Code:    200,
		Message: "OTP verified",
	}))
}

func QRCode(c *gin.Context) {
	// generate random secret
	secret := make([]byte, 20)
	_, err := rand.Read(secret)
	if err != nil {
		logs.Logs.Println("[ERR][2FA] Failed to generate random secret for QRCode: " + err.Error())
	}

	// convert to string
	secretBase32 := base32.StdEncoding.EncodeToString(secret)

	// get claims from token
	claims := jwt.ExtractClaims(c)

	// define issuer
	account := claims["id"].(string)
	issuer := configuration.Config.Issuer2FA

	// set secret for user
	result, setSecret := SetUserSecret(account, secretBase32)
	if !result {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    400,
			Message: "user secret set error",
			Data:    "",
		}))
		return
	}

	// define URL
	URL, err := url.Parse("otpauth://totp")
	if err != nil {
		logs.Logs.Println("[ERR][2FA] Failed to parse URL for QRCode: " + err.Error())
	}

	// add params
	URL.Path += "/" + issuer + ":" + account
	params := url.Values{}
	params.Add("secret", setSecret)
	params.Add("issuer", issuer)
	params.Add("algorithm", "SHA1")
	params.Add("digits", "6")
	params.Add("period", "30")

	// print url
	URL.RawQuery = params.Encode()

	// response
	c.JSON(http.StatusOK, structs.Map(response.StatusOK{
		Code:    200,
		Message: "QR code string",
		Data:    gin.H{"url": URL.String(), "key": setSecret},
	}))
}

func Get2FAStatus(c *gin.Context) {
	// get claims from token
	claims := jwt.ExtractClaims(c)

	// get status
	twoFaStatus, _ := GetUserStatus(claims["id"].(string))

	// return response
	c.JSON(http.StatusOK, gin.H{"status": twoFaStatus == "1"})
}

func Get2FARecoveryCodes(c *gin.Context) {
	claims := jwt.ExtractClaims(c)

	codes := GetRecoveryCodes(claims["id"].(string))

	c.JSON(http.StatusOK, gin.H{"codes": codes})
}

func Del2FAStatus(c *gin.Context) {
	// get claims from token
	claims := jwt.ExtractClaims(c)

	// revocate secret
	errRevocate := os.Remove(configuration.Config.SecretsDir + "/" + claims["id"].(string) + "/secret")
	if errRevocate != nil {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    403,
			Message: "error in revocate 2FA for user",
			Data:    nil,
		}))
		return
	}

	// revocate recovery codes
	errRevocateCodes := os.Remove(configuration.Config.SecretsDir + "/" + claims["id"].(string) + "/codes")
	if errRevocateCodes != nil {
		// if the file does not exist, it is ok, skip the error
		if !os.IsNotExist(errRevocateCodes) {
			c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
				Code:    403,
				Message: "error in delete 2FA recovery codes",
				Data:    nil,
			}))
			return
		}
	}

	// set 2FA to disabled
	f, _ := os.OpenFile(configuration.Config.SecretsDir+"/"+claims["id"].(string)+"/status", os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0600)
	defer f.Close()

	// write file with tokens
	_, err := f.WriteString("0")

	// check error
	if err != nil {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    400,
			Message: "2FA not revocated",
			Data:    "",
		}))
		return
	}

	// response
	c.JSON(http.StatusOK, structs.Map(response.StatusOK{
		Code:    200,
		Message: "2FA revocate successfully",
		Data:    "",
	}))
}

func GetUserStatus(username string) (string, error) {
	status, err := os.ReadFile(configuration.Config.SecretsDir + "/" + username + "/status")
	statusS := strings.TrimSpace(string(status[:]))

	return statusS, err
}

func GetUserSecret(username string) string {
	// get secret
	secret, err := os.ReadFile(configuration.Config.SecretsDir + "/" + username + "/secret")

	// handle error
	if err != nil {
		return ""
	}

	// return string
	return string(secret[:])
}

func SetUserSecret(username string, secret string) (bool, string) {
	// get secret
	secretB, _ := os.ReadFile(configuration.Config.SecretsDir + "/" + username + "/secret")

	// check error
	if len(string(secretB[:])) == 0 {
		// check if dir exists, otherwise create it
		if _, errD := os.Stat(configuration.Config.SecretsDir + "/" + username); os.IsNotExist(errD) {
			_ = os.MkdirAll(configuration.Config.SecretsDir+"/"+username, 0700)
		}

		// open file
		f, _ := os.OpenFile(configuration.Config.SecretsDir+"/"+username+"/secret", os.O_WRONLY|os.O_CREATE, 0600)
		defer f.Close()

		// write file with secret
		_, err := f.WriteString(secret)

		// check error
		if err != nil {
			return false, ""
		}

		return true, secret
	}

	return true, string(secretB[:])
}

func CheckTokenValidation(username string, token string) bool {
	// read whole file
	secrestListB, err := os.ReadFile(configuration.Config.TokensDir + "/" + username)
	if err != nil {
		return false
	}
	secrestList := string(secrestListB)

	// check whether secret list contains token
	return strings.Contains(secrestList, token)
}

func SetTokenValidation(username string, token string) bool {
	// open file
	f, _ := os.OpenFile(configuration.Config.TokensDir+"/"+username, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0600)
	defer f.Close()

	// write file with tokens
	_, err := f.WriteString(token + "\n")

	// check error
	return err == nil
}

func DelTokenValidation(username string, token string) bool {
	// read whole file
	secrestListB, errR := ioutil.ReadFile(configuration.Config.TokensDir + "/" + username)
	if errR != nil {
		return false
	}
	secrestList := string(secrestListB)

	// match token to remove
	res := strings.Replace(secrestList, token, "", 1)

	// open file
	f, _ := os.OpenFile(configuration.Config.TokensDir+"/"+username, os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0600)
	defer f.Close()

	// write file with tokens
	_, err := f.WriteString(strings.TrimSpace(res) + "\n")

	// check error
	return err == nil
}

func ValidateAuth(tokenString string, ensureTokenExists bool) bool {
	// convert token string and validate it
	if tokenString != "" {
		token, err := jwtl.Parse(tokenString, func(token *jwtl.Token) (interface{}, error) {
			// validate the alg
			if _, ok := token.Method.(*jwtl.SigningMethodHMAC); !ok {
				return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
			}

			// return secret
			return []byte(configuration.Config.SecretJWT), nil
		})

		if err != nil {
			logs.Logs.Println("[ERR][JWT] error in JWT token validation: " + err.Error())
			return false
		}

		if claims, ok := token.Claims.(jwtl.MapClaims); ok && token.Valid {
			if claims["id"] != nil {
				if ensureTokenExists {
					username := claims["id"].(string)

					if !CheckTokenValidation(username, tokenString) {
						logs.Logs.Println("[ERR][JWT] error JWT token not found")
						return false
					}
				}
				return true
			}
		} else {
			logs.Logs.Println("[ERR][JWT] error in JWT token claims")
			return false
		}
	}
	return false
}

func GetRecoveryCodes(username string) []string {
	// create empty array
	var recoveryCodes []string

	// check if recovery codes exists
	codesB, _ := os.ReadFile(configuration.Config.SecretsDir + "/" + username + "/codes")

	// check length
	if len(string(codesB[:])) == 0 {

		// get secret
		secret := GetUserSecret(username)

		// get recovery codes
		if len(string(secret)) > 0 {
			// execute oathtool to get recovery codes
			out, err := exec.Command("/usr/bin/oathtool", "-w", "4", "-b", secret).Output()

			// check errors
			if err != nil {
				return recoveryCodes
			}

			// open file
			f, _ := os.OpenFile(configuration.Config.SecretsDir+"/"+username+"/codes", os.O_WRONLY|os.O_CREATE, 0600)
			defer f.Close()

			// write file with secret
			_, _ = f.WriteString(string(out[:]))

			// assign binary output
			codesB = out
		}

	}

	// parse output
	recoveryCodes = strings.Split(string(codesB[:]), "\n")

	// remove empty element, the last one
	if recoveryCodes[len(recoveryCodes)-1] == "" {
		recoveryCodes = recoveryCodes[:len(recoveryCodes)-1]
	}

	// return codes
	return recoveryCodes
}

func UpdateRecoveryCodes(username string, codes []string) bool {
	// open file
	f, _ := os.OpenFile(configuration.Config.SecretsDir+"/"+username+"/codes", os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0600)
	defer f.Close()

	// write file with secret
	codes = append(codes, "")
	_, err := f.WriteString(strings.Join(codes[:], "\n"))

	// check error
	return err == nil
}

func DeleteExpiredTokens() {
	// create new tokens list
	var validTokens []string

	// read tokens directory
	usernames, err := ioutil.ReadDir(configuration.Config.TokensDir)

	// check read error
	if err != nil {
		logs.Logs.Println("[ERR][JWT] Failed to read tokens dir " + configuration.Config.TokensDir + ". Error: " + err.Error())
	}

	// list usernames
	for _, username := range usernames {
		// read whole file
		tokenstListB, err := ioutil.ReadFile(configuration.Config.TokensDir + "/" + username.Name())

		// check error
		if err != nil {
			logs.Logs.Println("[ERR][JWT] Failed to read tokens file " + configuration.Config.TokensDir + "/" + username.Name() + ". Error: " + err.Error())
		}

		// get string file
		tokensList := string(tokenstListB)

		// convert to array
		tokens := strings.Split(tokensList, "\n")

		// remove empty elem
		if tokens[len(tokens)-1] == "" {
			tokens = tokens[:len(tokens)-1]
		}

		// loop all tokens
		for _, token := range tokens {
			// validate token
			valid := ValidateAuth(token, false)

			// add only valid tokens
			if valid {
				token = strings.TrimSpace(token)
				validTokens = append(validTokens, token)
			}
		}

		// rewrite file with only valid tokens
		f, _ := os.OpenFile(configuration.Config.TokensDir+"/"+username.Name(), os.O_RDWR|os.O_CREATE|os.O_TRUNC, 0600)
		defer f.Close()

		// compose string
		writeTokens := strings.Join(validTokens[:], "\n")

		// write file with tokens
		_, errWrite := f.WriteString(writeTokens + "\n")

		// check error
		if errWrite != nil {
			logs.Logs.Println("[ERR][JWT] Failed to write new tokens file " + configuration.Config.TokensDir + "/" + username.Name() + ". Error: " + errWrite.Error())
		}
	}

}
