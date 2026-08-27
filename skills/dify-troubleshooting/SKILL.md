---
name: Dify troubleshooting
description: >-
  Use this when Dify login, plugins, models, RAG, uploads, or containers fail —
  CSRF, uv, 413, SSRF, stale failed tasks, reboot.
---
# Dify troubleshooting

Use this when Dify is up but something fails: login, plugins red, models missing, RAG empty, 413, containers unhealthy, "install failed" in the UI. Intranet/SSRF: [Dify intranet](sand-workflow:dify-intranet). Plugin uv: [Dify plugin install](sand-workflow:dify-plugin-install). Prefix mix-ups: [Dify API catalog](sand-workflow:dify-api-catalog).

## Decide where it broke
| Symptom | Likely layer |
|---|---|
| Connection refused on `:80` | nginx / compose / dockerd not running |
| `/install` loops or setup `not_started` | admin not created |
| `401 Invalid encrypted data` | password sent as plaintext; must be **Base64** |
| `401 CSRF token is missing or invalid` | missing `X-CSRF-Token` (cookie alone is not enough) |
| Plugin card red / uv `exit status 1` | plugin_daemon cannot reach PyPI or local index missing wheels |
| UI "N failed tasks" but list shows plugins | stale tasks; plugins may already work |
| Provider missing from model list | plugin not `local runtime ready` |
| Upload 413 | `NGINX_CLIENT_MAX_BODY_SIZE` smaller than upload/plugin caps |
| HTTP node can't hit `10.x` / `172.x` | SSRF deny-by-default |
| File preview broken in plugins | set `INTERNAL_FILES_URL=http://api:5001` |
| Everyone logged out, file URLs die | `SECRET_KEY` changed after first boot |
| After host reboot, nothing listens | nested boxes often need **manual `dockerd`**, then `compose up -d` |
| Draft save 400 | missing/stale workflow `hash` from GET draft |
| 403 on `/rbac`, `/billing`, RAG publish | community / feature flag, not CSRF |
| `/agent` 404 vs app list empty | Agent Studio (`/agent`) ≠ `mode: agent-chat` (`/apps`) |
| Bearer key on `/console/api` 401 | wrong surface; app keys are `/v1` only |
| MCP client 404 after refresh | `POST .../server/refresh` rotated `server_code` |

## Compose health
```bash
sudo docker compose ps
sudo docker compose logs --tail=80 api plugin_daemon nginx
curl -sS http://127.0.0.1/console/api/setup
curl -sS http://127.0.0.1/console/api/version
```
`init_permissions` Exited 0 is normal. Never `compose down -v`.

## Login
1. `GET /console/api/setup` = `finished`
2. POST `/login` with Base64 password
3. Cookies **and** CSRF
4. Still 401 → wrong password; do not rotate `SECRET_KEY`

## Plugins
Host can reach marketplace; container often cannot. Download `.difypkg` on the host. Daemon `failed to install dependencies` = missing wheels. Rebuild `simple/` index, delete `cwd/.uv-cache/simple-v24`. `POST .../plugin/tasks/delete_all` clears the red list. Trust `plugin/list` + `local runtime ready`.

## Models / RAG / Agent
Plugin installed ≠ credentials saved. `high_quality` dataset needs embedding first. Agent tool missing: ready + tool-provider `add` + selected on the node. Studio Skills missing: published + `PUT /workspaces/current/agents/{id}/skills`.

## Nested Docker
Image extract `whiteout … operation not permitted` → `fuse-overlayfs`. Containers cannot talk to redis/db → `bridge-nf-call-iptables` dropping ICC.

## Do not
Set `DEPLOYMENT_EDITION=ENTERPRISE` to unlock features. Open container egress with iptables/host proxy if that was already blocked. Delete `volumes/` to fix a plugin.
