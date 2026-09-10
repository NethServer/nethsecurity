# ns-api-server

NS API server, see [source code](https://github.com/NethServer/nethsecurity-api).

The server is configured to listen on `127.0.0.1:8090`.

## Controller attribution

Units managed by a controller are accessed with a single machine account, created by
`ns-plug` as the `rpcd.controller` UCI section with a random username. Without further
information, every action performed from the controller would be logged under that name.

To report the real operator, `POST /login` accepts an optional `on_behalf_of` field:

```json
{ "username": "<controller machine account>", "password": "...", "on_behalf_of": "alice" }
```

The field is accepted only when the authenticating user is the account named by
`uci get rpcd.controller.username`; for any other user it is silently ignored. It is also
ignored when empty, longer than 64 characters, or containing control characters.

When accepted, the value is stored in the `on_behalf_of` JWT claim and reported on the
`[AUTH]` log lines, right before the client IP:

```
[INFO][AUTH] authentication success for user 3f2a1b0c9d8e on behalf of alice from 10.0.0.5
[INFO][AUTH] authorization success for user 3f2a1b0c9d8e on behalf of alice. POST /api/ubus/call {...}
```

The token identity (`id` claim) remains the machine account. The delegated identity is used
for logging only: it is not passed to the `/usr/libexec/rpcd/ns.*` handlers.

Older units ignore the field, and older controllers do not send it: in both cases the login
succeeds and the logs report the machine account alone.

## Rate limiting

The server applies a generous global per-client-IP rate limit as a coarse safety net across
all routes, on top of tighter per-route request body size limits on the pre-authentication
routes (`/login`, `/logout`, `/2fa/otp-verify`). Configured via env vars in
`ns-api-server.initd`:

- `GLOBAL_RATE_LIMIT_AVERAGE`: max sustained requests per second per client IP, default `25`;
  set to `0` to disable rate limiting.
- `GLOBAL_RATE_LIMIT_BURST`: burst allowance above the average before requests are rejected
  with HTTP 429, default `100`.
