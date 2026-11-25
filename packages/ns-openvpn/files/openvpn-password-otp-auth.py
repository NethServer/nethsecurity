#!/usr/bin/python3
#
# Copyright (C) 2026 Nethesis S.r.l.
# SPDX-License-Identifier: GPL-2.0-only
#

# Two-step authentication: password first, then OTP.
# The OTP is asked only if the password is correct.
#
# The script is configured both as auth-user-pass-verify and as
# client-crresponse, OpenVPN sets the script_type env variable accordingly.
#
# Clients announcing the "crtext" method in IV_SSO (e.g. OpenVPN GUI,
# OpenVPN Connect) use the auth-pending API, on a single connection:
#
# 1. user-pass-verify: verify the password, then defer the authentication
#    and ask for the OTP (auth_pending_file, CR_TEXT)
# 2. client-crresponse: verify the OTP and write the result to
#    auth_control_file
#
# Other clients (e.g. the openvpn command line client, NetworkManager,
# Tunnelblick) use the dynamic challenge protocol (CRV1), on two connections:
#
# 1. user-pass-verify: verify the password, then reject the client with a
#    CRV1 challenge containing a random state id
# 2. the client asks for the OTP and reconnects sending
#    "CRV1::<state_id>::<otp>" as password: the state id proves the password
#    was already verified, then the OTP is verified
#
# The CRV1 state id can be used only once and expires after OTP_TIMEOUT seconds.
#
# Used env variables:
# - script_type
# - username, password, common_name, config, IV_SSO
# - auth_pending_file, auth_control_file, auth_failed_reason_file

import base64
import binascii
import json
import os
import secrets
import subprocess
import sys
import syslog
import time

from euci import EUci
from nethsec import users

LIBEXEC = "/usr/libexec/ns-openvpn"
STATE_DIR = "/var/run/ns-openvpn/otp-challenge"
OTP_TIMEOUT = 60
OTP_PROMPT = "Enter the OTP code"


def get_username():
    # client-crresponse env may not contain the username
    return os.environ.get("username") or os.environ.get("common_name", "")


def log(msg):
    syslog.openlog("openvpn-password-otp-auth")
    syslog.syslog(syslog.LOG_INFO, f"[{get_username()}] {msg}")


def write_file(env_var, content):
    with open(os.environ[env_var], "w") as fp:
        fp.write(content)


def get_instance():
    instance = os.path.basename(os.environ.get("config", ""))
    return instance.removeprefix("openvpn-").removesuffix(".conf")


def run_check(script, secret):
    env = os.environ.copy()
    env["password"] = secret
    env["username"] = get_username()
    return subprocess.run(
        [os.path.join(LIBEXEC, script)], check=False, env=env
    ).returncode


def verify_password(password):
    uci = EUci()
    db = uci.get("openvpn", get_instance(), "ns_user_db", default=None)
    if db is None:
        # user db not set
        sys.exit(5)

    if users.get_database_type(uci, db) == "ldap":
        script = "openvpn-remote-auth"
    else:
        script = "openvpn-local-auth"
    ret = run_check(script, password)
    if ret != 0:
        log(f"password check failed ({script} exit code {ret})")
        # always exit 1: exit code 2 would defer the authentication
        sys.exit(1)


def verify_otp(otp):
    ret = run_check("openvpn-otp-auth", otp)
    if ret == 0:
        log("OTP ok")
    else:
        log(f"OTP check failed (openvpn-otp-auth exit code {ret})")
    return ret == 0


# CRV1 state: a random id, saved on disk, that proves the password was
# already verified for this user and instance


def state_path(state_id):
    return os.path.join(STATE_DIR, state_id)


def save_state(username):
    os.makedirs(STATE_DIR, mode=0o700, exist_ok=True)
    # remove expired states
    now = time.time()
    for name in os.listdir(STATE_DIR):
        try:
            if os.path.getmtime(state_path(name)) < now - OTP_TIMEOUT:
                os.remove(state_path(name))
        except OSError:
            pass
    state_id = secrets.token_hex(16)
    fd = os.open(state_path(state_id), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with open(fd, "w") as fp:
        json.dump({"username": username, "instance": get_instance(), "time": now}, fp)
    return state_id


def pop_state(state_id):
    # the state can be used only once
    if not state_id.isalnum():
        return None
    try:
        with open(state_path(state_id)) as fp:
            state = json.load(fp)
        os.remove(state_path(state_id))
    except (OSError, ValueError):
        return None
    if state.get("time", 0) < time.time() - OTP_TIMEOUT:
        return None
    return state


def crv1_response(username, password):
    # password format: CRV1::<state_id>::<otp>
    parts = password.split("::")
    if len(parts) != 3:
        log("invalid challenge response")
        sys.exit(1)
    state = pop_state(parts[1])
    if (
        state is None
        or state.get("username") != username
        or state.get("instance") != get_instance()
    ):
        log("invalid or expired challenge")
        sys.exit(1)
    sys.exit(0 if verify_otp(parts[2].strip()) else 1)


def user_pass_verify():
    username = os.environ.get("username", "")
    password = os.environ.get("password", "")

    if password.startswith("CRV1::"):
        # second connection of the dynamic challenge: the client sent the OTP
        crv1_response(username, password)

    verify_password(password)

    if "crtext" in os.environ.get("IV_SSO", "").split(","):
        # ask for the OTP on the same connection and defer the authentication
        write_file(
            "auth_pending_file", f"{OTP_TIMEOUT}\ncrtext\nCR_TEXT:E,R:{OTP_PROMPT}"
        )
        log("password ok, OTP requested (crtext)")
        sys.exit(2)

    # ask for the OTP with a dynamic challenge: the client reconnects with the OTP
    user_b64 = base64.b64encode(username.encode()).decode()
    challenge = f"CRV1:R,E:{save_state(username)}:{user_b64}:{OTP_PROMPT}"
    write_file("auth_failed_reason_file", challenge)
    log("password ok, OTP challenge sent (CRV1)")
    sys.exit(1)


def client_crresponse():
    # the response file contains the OTP, base64 encoded
    try:
        with open(sys.argv[1]) as fp:
            otp = base64.b64decode(fp.read().strip(), validate=True).decode().strip()
    except (IndexError, OSError, binascii.Error, UnicodeDecodeError):
        log("invalid OTP response")
        write_file("auth_control_file", "0")
        return
    write_file("auth_control_file", "1" if verify_otp(otp) else "0")


script_type = os.environ.get("script_type")
if script_type == "user-pass-verify":
    user_pass_verify()
elif script_type == "client-crresponse":
    client_crresponse()
else:
    print(f"Unknown script type {script_type}", file=sys.stderr)
    sys.exit(1)
