/*
 * Copyright (C) 2023 Nethesis S.r.l.
 * http://www.nethesis.it - info@nethesis.it
 *
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * author: Edoardo Spadoni <edoardo.spadoni@nethesis.it>
 */

package models

type UserAuthorizations struct {
	Username      string   `json:"username" structs:"username"`
	Role          string   `json:"role" structs:"role"`
	Actions       []string `json:"actions" structs:"actions"`
	SudoRequested bool     `json:"sudo_requested" structs:"sudo_requested"`
}

type OTPJson struct {
	Username string `json:"username" structs:"username"`
	Token    string `json:"token" structs:"token"`
	OTP      string `json:"otp" structs:"otp"`
}

type Status2FA struct {
	Status bool `json:"status" structs:"status"`
}

type UserLogin struct {
	Username string `json:"username" structs:"username"`
	Password string `json:"password" structs:"password"`
	Timeout  int    `json:"timeout" structs:"timeout"`
}
