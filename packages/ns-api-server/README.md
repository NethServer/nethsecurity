# ns-api-server

NS API server, see [source code](https://github.com/NethServer/nethsecurity-api).

The server is configured to listen on `127.0.0.1:8090`.

## Metrics and alerts proxies

Reverse proxies to the local VictoriaMetrics and vmalert APIs, for the authenticated UI. Live
inside the JWT-protected group: authenticated, rate-limited, `Authorization`/`Cookie` headers
stripped before forwarding. Registered routes accept any HTTP method; unregistered paths 404.
Backend unreachable or slow → `502`.

| Route | Backend |
|---|---|
| `/api/metrics/query` | VictoriaMetrics `/api/v1/query` |
| `/api/metrics/query_range` | VictoriaMetrics `/api/v1/query_range` |
| `/api/alerts/alerts` | vmalert `/api/v1/alerts` |

Backend addresses: `VICTORIA_METRICS_URL` / `VMALERT_URL` env vars in `ns-api-server.initd`,
read from `victoria-metrics.main.http_listen_addr` / `vmalert.main.http_listen_addr` (default
`http://127.0.0.1:8428` / `http://127.0.0.1:8082`). Restarts on `victoria-metrics`/`vmalert`
config change (`service_triggers`).

Example:

```
GET /api/metrics/query?query=up
GET /api/metrics/query_range?query=<promql>&start=<ts>&end=<ts>&step=<dur>
GET /api/alerts/alerts
```

## Rate limiting

The server applies a generous global per-client-IP rate limit as a coarse safety net across
all routes, on top of tighter per-route request body size limits on the pre-authentication
routes (`/login`, `/logout`, `/2fa/otp-verify`). Configured via env vars in
`ns-api-server.initd`:

- `GLOBAL_RATE_LIMIT_AVERAGE`: max sustained requests per second per client IP, default `25`;
  set to `0` to disable rate limiting.
- `GLOBAL_RATE_LIMIT_BURST`: burst allowance above the average before requests are rejected
  with HTTP 429, default `100`.
