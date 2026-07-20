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

	VictoriaMetricsURL string `json:"victoria_metrics_url"`
	VMAlertURL         string `json:"vmalert_url"`

	// Generous global per-IP rate limit applied to every API route as a coarse
	// safety net; 0 disables it
	GlobalRateLimitAverage int `json:"global_rate_limit_average"`
	GlobalRateLimitBurst   int `json:"global_rate_limit_burst"`
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

	if os.Getenv("VICTORIA_METRICS_URL") != "" {
		Config.VictoriaMetricsURL = os.Getenv("VICTORIA_METRICS_URL")
	} else {
		Config.VictoriaMetricsURL = "http://127.0.0.1:8428"
	}

	if os.Getenv("VMALERT_URL") != "" {
		Config.VMAlertURL = os.Getenv("VMALERT_URL")
	} else {
		Config.VMAlertURL = "http://127.0.0.1:8082"
	}

	if v, err := strconv.Atoi(os.Getenv("GLOBAL_RATE_LIMIT_AVERAGE")); err == nil {
		Config.GlobalRateLimitAverage = v
	} else {
		Config.GlobalRateLimitAverage = 25
	}

	if v, err := strconv.Atoi(os.Getenv("GLOBAL_RATE_LIMIT_BURST")); err == nil {
		Config.GlobalRateLimitBurst = v
	} else {
		Config.GlobalRateLimitBurst = 100
	}
}
