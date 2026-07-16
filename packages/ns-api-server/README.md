# ns-api-server

NS API server, see [source code](https://github.com/NethServer/nethsecurity-api).

The server is configured to listen on `127.0.0.1:8090`.

## Rate limiting

The server applies a generous global per-client-IP rate limit as a coarse safety net across
all routes, on top of tighter per-route request body size limits on the pre-authentication
routes (`/login`, `/logout`, `/2fa/otp-verify`). Configured via env vars in
`ns-api-server.initd`:

- `GLOBAL_RATE_LIMIT_AVERAGE`: max sustained requests per second per client IP, default `25`;
  set to `0` to disable rate limiting.
- `GLOBAL_RATE_LIMIT_BURST`: burst allowance above the average before requests are rejected
  with HTTP 429, default `100`.
