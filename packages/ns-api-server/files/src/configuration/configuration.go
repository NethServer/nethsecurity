/*
 * Copyright (C) 2024 Nethesis S.r.l.
 * http://www.nethesis.it - info@nethesis.it
 *
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * author: Edoardo Spadoni <edoardo.spadoni@nethesis.it>
 */

package configuration

import (
	"os"
	"strconv"
	"strings"

	"github.com/NethServer/nethsecurity-api/logs"
)

type Configuration struct {
	ListenAddress string `json:"listen_address"`

	SecretJWT  string `json:"secret_jwt"`
	Issuer2FA  string `json:"issuer_2fa"`
	SecretsDir string `json:"secrets_dir"`
	TokensDir  string `json:"tokens_dir"`

	SensitiveList []string `json:"sensitive_list"`

	UploadFileMaxSize int64  `json:"upload_file_max_size"`
	UploadFilePath    string `json:"upload_file_path"`
	DownloadFilePath  string `json:"download_file_path"`
}

var Config = Configuration{}

func Init() {
	// read configuration from ENV
	if os.Getenv("LISTEN_ADDRESS") != "" {
		Config.ListenAddress = os.Getenv("LISTEN_ADDRESS")
	} else {
		Config.ListenAddress = "127.0.0.1:8080"
	}

	if os.Getenv("SECRET_JWT") != "" {
		Config.SecretJWT = os.Getenv("SECRET_JWT")
	} else {
		logs.Logs.Println("[CRITICAL][ENV] SECRET_JWT variable is empty")
		os.Exit(1)
	}

	if os.Getenv("ISSUER_2FA") != "" {
		Config.Issuer2FA = os.Getenv("ISSUER_2FA")
	} else {
		Config.Issuer2FA = "NethServer"
	}

	if os.Getenv("SECRETS_DIR") != "" {
		Config.SecretsDir = os.Getenv("SECRETS_DIR")
	} else {
		logs.Logs.Println("[CRITICAL][ENV] SECRETS_DIR variable is empty")
		os.Exit(1)
	}

	if os.Getenv("TOKENS_DIR") != "" {
		Config.TokensDir = os.Getenv("TOKENS_DIR")
	} else {
		logs.Logs.Println("[CRITICAL][ENV] TOKENS_DIR variable is empty")
		os.Exit(1)
	}

	if os.Getenv("SENSITIVE_LIST") != "" {
		Config.SensitiveList = strings.Split(os.Getenv("SENSITIVE_LIST"), ",")
	} else {
		Config.SensitiveList = []string{"password", "secret", "token"}
	}

	if os.Getenv("DOWNLOAD_FILE_PATH") != "" {
		Config.DownloadFilePath = os.Getenv("DOWNLOAD_FILE_PATH")
	} else {
		Config.DownloadFilePath = "/var/run/ns-api-server/downloads"
	}
	if os.Getenv("UPLOAD_FILE_PATH") != "" {
		Config.UploadFilePath = os.Getenv("UPLOAD_FILE_PATH")
	} else {
		Config.UploadFilePath = "/var/run/ns-api-server/uploads"
	}

	if os.Getenv("UPLOAD_FILE_MAX_SIZE") != "" {
		Config.UploadFileMaxSize, _ = strconv.ParseInt(os.Getenv("UPLOAD_FILE_MAX_SIZE"), 10, 64)
	} else {
		Config.UploadFileMaxSize = 32
	}
}
