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
	"sync"
)

var (
	mu     sync.Mutex
	tag    string
	writer *syslog.Writer
)

// Output receives the log lines when syslog isn't available
var Output io.Writer = os.Stderr

func Init(name string) {
	tag = name
	if _, err := connect(); err != nil {
		fmt.Fprintln(Output, "[ERR][LOGS] cannot connect to syslog: "+err.Error())
	}
}

// connect returns the syslog writer, retrying the connection if Init couldn't open it
func connect() (*syslog.Writer, error) {
	mu.Lock()
	defer mu.Unlock()
	if writer == nil && tag != "" {
		w, err := syslog.New(syslog.LOG_DAEMON|syslog.LOG_INFO, tag)
		if err != nil {
			return nil, err
		}
		writer = w
	}
	return writer, nil
}

func Info(msg string) {
	w, _ := connect()
	if w == nil {
		fmt.Fprintln(Output, msg)
		return
	}
	w.Info(msg)
}

func Err(msg string) {
	w, _ := connect()
	if w == nil {
		fmt.Fprintln(Output, msg)
		return
	}
	w.Err(msg)
}

func Crit(msg string) {
	w, _ := connect()
	if w == nil {
		fmt.Fprintln(Output, msg)
		return
	}
	w.Crit(msg)
}
