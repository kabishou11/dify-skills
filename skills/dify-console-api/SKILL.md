---
name: Dify console API
description: >-
  Use this when logging into or driving self-hosted Dify via Console API (CSRF,
  apps, workflows, plugins, datasets).
---
# Dify Console API

Use this to drive self-hosted Dify over HTTP. Pair with [Dify troubleshooting](sand-workflow:dify-troubleshooting) when a call fails. Prefix lookup: [Dify API catalog](sand-workflow:dify-api-catalog).

## Login
Password is **Base64**, not RSA. Plaintext → `401 Invalid encrypted data`.

```bash
PW=$(python3 -c "import base64; print(base64.b64encode(b'PASSWORD').decode())")
curl -c /tmp/dify-cookies.txt -X POST "$DIFY/console/api/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"USER@email\",\"password\":\"$PW\",\"language\":\"zh-Hans\",\"remember_me\":true}"
CSRF=$(awk '$6=="csrf_token"{print $7}' /tmp/dify-cookies.txt)
```

Every later mutating call: `-b /tmp/dify-cookies.txt -H "X-CSRF-Token: $CSRF"`. Cookie without CSRF → `401 CSRF token is missing or invalid`. Access token cookies expire ~1h; login again. `POST /refresh-token` if you still have the refresh cookie.

Sanity: `GET /console/api/setup` (`finished` = admin exists), `GET /console/api/account/profile`, `GET /console/api/version`, `GET /console/api/features`, `GET /console/api/system-features`.

First-time box: open `/install` only if setup is `not_started`. Do not POST `/setup` if already finished.

## Conventions
- Prefix `/console/api`. Default compose nginx is `:80`.
- JSON in/out. Files: multipart (`POST /files/upload`; GET on the same path is metadata). Support types: `GET /files/support-type`.
- Prefer this API over clicking the UI. Browser only for `/install`, OAuth, captcha.
- Never write passwords or `SECRET_KEY` into skills/git. Changing `SECRET_KEY` after boot logs everyone out and breaks signed file URLs.
- Keep `DEPLOYMENT_EDITION=COMMUNITY`.

## Endpoint map
| Area | Routes | Next skill |
|---|---|---|
| Apps | `GET/POST /apps`, `GET/PUT/DELETE /apps/{id}`, `POST /apps/{id}/copy`, `GET /apps/{id}/export`, `POST /apps/imports` | Dify apps and workflows |
| Canvas | `GET/POST /apps/{id}/workflows/draft`, `POST .../publish`, `POST .../draft/run`, human-input, comments | Dify apps and workflows |
| Datasets | `GET/POST /datasets`, `/datasets/{id}/documents`, segments, metadata | Dify knowledge bases |
| RAG pipeline | `/rag/pipelines`, `/rag/pipeline/dataset` | Dify workspace extras |
| Models | `/workspaces/current/model-providers`, `.../default-model`, `.../models` | Dify model providers |
| Tools | `/workspaces/current/tool-providers` | Dify agents and tools |
| Agent Studio | `/agent`, `/agent/{id}/*` | Dify workspace extras |
| Workspace Skills / snippets | `/workspaces/current/skills`, `/workspaces/current/customized-snippets` | Dify workspace extras |
| MCP / endpoints | `/apps/{id}/server`, `/workspaces/current/endpoints` | Dify workspace extras |
| Plugins | `/workspaces/current/plugin/list`, `install/*`, `upload/pkg`, `tasks` | Dify plugin install |
| Files | `POST /files/upload`, `GET /files/{id}/preview` | Dify service API |
| Keys | `POST /apps/{id}/api-keys`, `POST /apps/{id}/api-enable` | Dify service API |
| Members / tags | `/workspaces/current/members`, `/tags` | Dify workspace extras |
| Logs / stats / annotations | `/apps/{id}/chat-conversations`, `/workflow-app-logs`, `/workflow-runs`, `/statistics/*`, `/workflow/statistics/*`, `/annotations` | Dify workspace extras |
| Agent Studio runtime / sandbox | `/agent/{id}/chat-messages`, `/agent/{id}/logs`, `/agent/{id}/sandbox/*` | Dify workspace extras |
| Dataset hit-test | `POST /datasets/{id}/hit-testing` | Dify knowledge bases |
| Triggers | `/apps/{id}/triggers`, `/apps/{id}/trigger-enable` | Dify apps and workflows |

## After reboot
Nested/cloud VMs often need **manual `dockerd`**, then `docker compose up -d` from the Dify `docker/` dir. Do not `compose down -v`. See Dify backup and upgrade.
