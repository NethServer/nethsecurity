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
	"encoding/json"
	"io"
	"net/http"
	"os/exec"
	"fmt"

	"github.com/NethServer/nethsecurity-api/models"
	"github.com/NethServer/nethsecurity-api/response"
	"github.com/NethServer/nethsecurity-api/logs"
	"github.com/Jeffail/gabs/v2"
	"github.com/fatih/structs"
	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
)

func UBusCallAction(c *gin.Context) {
	// parse request fields
	var jsonUBusCall models.UBusCallJSON
	var cmd *exec.Cmd
	if err := c.ShouldBindBodyWith(&jsonUBusCall, binding.JSON); err != nil {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    400,
			Message: "request fields malformed",
			Data:    err.Error(),
		}))
		return
	}

	// convert payload to JSON
	jsonPayload, _ := json.Marshal(jsonUBusCall.Payload)

	// check if path starts with ns.
	if jsonUBusCall.Path[:3] == "ns." {
		// force base path to avoid calling other system binaries
		jsonUBusCall.Path = "/usr/libexec/rpcd/" + jsonUBusCall.Path
		cmd = exec.Command(jsonUBusCall.Path, "call", jsonUBusCall.Method)

		// execute direct script call
		stdin, err := cmd.StdinPipe()
		if err != nil {
			// log full response for debugging if ubus call fails
			logs.Logs.Println("[ERROR][UBUS][STDIN] ubus stdin pipe error:", err.Error())
			c.JSON(http.StatusInternalServerError, structs.Map(response.StatusBadRequest{
				Code:    500,
				Message: "ubus call action failed",
				Data:    err.Error(),
			}))
			return
		}

		io.WriteString(stdin, string(jsonPayload))
		stdin.Close()
	} else {
		// check if path is authorized
		var authorizedPaths = map[string][]string{
			"uci":               {"get", "set", "changes", "revert"},
			"luci":              {"getTimezones", "setInitAction"},
			"system":            {"info", "board"},
			"network.interface": {"dump"},
		}
		var forbidden = true
		if authorizedPaths[jsonUBusCall.Path] != nil {
			for _, method := range authorizedPaths[jsonUBusCall.Path] {
				if method == jsonUBusCall.Method {
					forbidden = false
					break
				}
			}
		}
		if forbidden {
			c.AbortWithStatusJSON(http.StatusForbidden, structs.Map(response.StatusBadRequest{
				Code:    403,
				Message: "ubus call action forbidden",
				Data:    "method not allowed",
			}))
			return
		}

		// fallback to rpcd
		cmd = exec.Command("/bin/ubus", "-S", "-t", "300", "call", jsonUBusCall.Path, jsonUBusCall.Method, string(jsonPayload[:]))
	}

	// check errors
	out, err := cmd.CombinedOutput()
	if err != nil {
		// log full response for debugging if ubus call fails
		logs.Logs.Println("[ERROR][UBUS][PROCESS] ubus execution error:", err.Error())
		logs.Logs.Println("[ERROR][UBUS][OUTPUT] ubus execution output:", string(out))
		c.JSON(http.StatusInternalServerError, structs.Map(response.StatusBadRequest{
			Code:    500,
			Message: "ubus call action failed",
			Data:    err.Error(),
		}))
		return
	}

	// parse output in a valid JSON
	jsonParsed, _ := gabs.ParseJSON(out)

	// check errors in response
	errorMessage, errFound := jsonParsed.Path("error").Data().(string)
	if errFound {
		// log full response for debugging if we find {"error": ...} in response
		logs.Logs.Println(fmt.Sprintf(
			"[ERROR][UBUS][RESPONSE] ubus application error: Message='%s', Data='%s'",
			errorMessage,
			jsonParsed.String(),
		))
		c.JSON(http.StatusInternalServerError, structs.Map(response.StatusBadRequest{
			Code:    500,
			Message: errorMessage,
			Data:    jsonParsed,
		}))
		return
	}

	// check validation error in response
	validationFound := jsonParsed.Exists("validation")
	if validationFound {
		c.JSON(http.StatusBadRequest, structs.Map(response.StatusBadRequest{
			Code:    400,
			Message: "validation_failed",
			Data:    jsonParsed,
		}))
		return
	}

	// return 200 OK with data
	c.JSON(http.StatusOK, structs.Map(response.StatusOK{
		Code:    200,
		Message: "ubus call action success",
		Data:    jsonParsed,
	}))
}
