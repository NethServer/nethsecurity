/*
 * Copyright (C) 2026 Nethesis S.r.l.
 * SPDX-License-Identifier: GPL-2.0-only
 */

package configuration

import (
	"os"
	"testing"
)

func TestInitVictoriaMetricsURLDefault(t *testing.T) {
	os.Unsetenv("VICTORIA_METRICS_URL")
	os.Setenv("SECRET_JWT", "test-secret")
	os.Setenv("SECRETS_DIR", "/tmp/secrets")
	os.Setenv("TOKENS_DIR", "/tmp/tokens")

	Init()

	if Config.VictoriaMetricsURL != "http://127.0.0.1:8428" {
		t.Fatalf("VictoriaMetricsURL = %q, want %q", Config.VictoriaMetricsURL, "http://127.0.0.1:8428")
	}
}

func TestInitVictoriaMetricsURLFromEnv(t *testing.T) {
	os.Setenv("SECRET_JWT", "test-secret")
	os.Setenv("SECRETS_DIR", "/tmp/secrets")
	os.Setenv("TOKENS_DIR", "/tmp/tokens")
	os.Setenv("VICTORIA_METRICS_URL", "http://127.0.0.1:9428")
	defer os.Unsetenv("VICTORIA_METRICS_URL")

	Init()

	if Config.VictoriaMetricsURL != "http://127.0.0.1:9428" {
		t.Fatalf("VictoriaMetricsURL = %q, want %q", Config.VictoriaMetricsURL, "http://127.0.0.1:9428")
	}
}

func TestInitVMAlertURLDefault(t *testing.T) {
	os.Unsetenv("VMALERT_URL")
	os.Setenv("SECRET_JWT", "test-secret")
	os.Setenv("SECRETS_DIR", "/tmp/secrets")
	os.Setenv("TOKENS_DIR", "/tmp/tokens")

	Init()

	if Config.VMAlertURL != "http://127.0.0.1:8082" {
		t.Fatalf("VMAlertURL = %q, want %q", Config.VMAlertURL, "http://127.0.0.1:8082")
	}
}

func TestInitVMAlertURLFromEnv(t *testing.T) {
	os.Setenv("SECRET_JWT", "test-secret")
	os.Setenv("SECRETS_DIR", "/tmp/secrets")
	os.Setenv("TOKENS_DIR", "/tmp/tokens")
	os.Setenv("VMALERT_URL", "http://127.0.0.1:9082")
	defer os.Unsetenv("VMALERT_URL")

	Init()

	if Config.VMAlertURL != "http://127.0.0.1:9082" {
		t.Fatalf("VMAlertURL = %q, want %q", Config.VMAlertURL, "http://127.0.0.1:9082")
	}
}

func TestInitGlobalRateLimitDefaults(t *testing.T) {
	os.Unsetenv("GLOBAL_RATE_LIMIT_AVERAGE")
	os.Unsetenv("GLOBAL_RATE_LIMIT_BURST")
	os.Setenv("SECRET_JWT", "test-secret")
	os.Setenv("SECRETS_DIR", "/tmp/secrets")
	os.Setenv("TOKENS_DIR", "/tmp/tokens")

	Init()

	if Config.GlobalRateLimitAverage != 25 {
		t.Fatalf("GlobalRateLimitAverage = %d, want 25", Config.GlobalRateLimitAverage)
	}
	if Config.GlobalRateLimitBurst != 100 {
		t.Fatalf("GlobalRateLimitBurst = %d, want 100", Config.GlobalRateLimitBurst)
	}
}

func TestInitGlobalRateLimitFromEnv(t *testing.T) {
	os.Setenv("SECRET_JWT", "test-secret")
	os.Setenv("SECRETS_DIR", "/tmp/secrets")
	os.Setenv("TOKENS_DIR", "/tmp/tokens")
	os.Setenv("GLOBAL_RATE_LIMIT_AVERAGE", "50")
	os.Setenv("GLOBAL_RATE_LIMIT_BURST", "150")
	defer os.Unsetenv("GLOBAL_RATE_LIMIT_AVERAGE")
	defer os.Unsetenv("GLOBAL_RATE_LIMIT_BURST")

	Init()

	if Config.GlobalRateLimitAverage != 50 {
		t.Fatalf("GlobalRateLimitAverage = %d, want 50", Config.GlobalRateLimitAverage)
	}
	if Config.GlobalRateLimitBurst != 150 {
		t.Fatalf("GlobalRateLimitBurst = %d, want 150", Config.GlobalRateLimitBurst)
	}
}
