/*
 * Copyright (C) 2023 Nethesis S.r.l.
 * http://www.nethesis.it - info@nethesis.it
 *
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * author: Edoardo Spadoni <edoardo.spadoni@nethesis.it>
 */

package models

type UBusCallJSON struct {
	Path    string      `json:"path" structs:"path"`
	Method  string      `json:"method" structs:"method"`
	Payload interface{} `json:"payload" structs:"payload"`
}
