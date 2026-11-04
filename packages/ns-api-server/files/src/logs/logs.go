/*
 * Copyright (C) 2023 Nethesis S.r.l.
 * http://www.nethesis.it - info@nethesis.it
 *
 * SPDX-License-Identifier: GPL-2.0-only
 *
 * author: Edoardo Spadoni <edoardo.spadoni@nethesis.it>
 */

package logs

import (
	"fmt"
	"io"
	"log/syslog"
	"os"
)

var writer *syslog.Writer

// Output receives the log lines when syslog isn't available
var Output io.Writer = os.Stderr

func Init(name string) {
	w, err := syslog.New(syslog.LOG_DAEMON|syslog.LOG_INFO, name)
	if err != nil {
		fmt.Fprintln(Output, "[ERR][LOGS] cannot connect to syslog: "+err.Error())
		return
	}
	writer = w
}

func Info(msg string) {
	if writer == nil {
		fmt.Fprintln(Output, msg)
		return
	}
	writer.Info(msg)
}

func Err(msg string) {
	if writer == nil {
		fmt.Fprintln(Output, msg)
		return
	}
	writer.Err(msg)
}

func Crit(msg string) {
	if writer == nil {
		fmt.Fprintln(Output, msg)
		return
	}
	writer.Crit(msg)
}
