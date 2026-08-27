---
name: Dify troubleshooting
description: >-
  Use this when Dify login, plugins, models, RAG, uploads, or containers fail — CSRF, uv, 413, SSRF, stale failed tasks, reboot.
---
# Dify troubleshooting

Use this when Dify is up but something fails. Changing workers/timeouts/.env: [Dify compose and config](sand-workflow:dify-compose-and-config). Intranet/SSRF: [Dify intranet](sand-workflow:dify-intranet). Plugin uv: [Dify plugin install](sand-workflow:dify-plugin-install). Canvas/DSL: [Dify apps and workflows](sand-workflow:dify-apps-and-workflows). Prefixes: [Dify API catalog](sand-workflow:dify-api-catalog).

## Decide where it broke

| Symptom | Likely layer |
|---|---|
| Connection refused on `:80` | nginx / compose / dockerd |
| `/install` loops | admin not created |
| `401 Invalid encrypted data` | password not **Base64** |
| `401 CSRF` / `unauthorized` | missing CSRF, or session ~1h expired |
| Plugin red / uv `exit status 1` | daemon cannot reach PyPI / local index |
| UI "N failed tasks" but list ok | stale tasks; `POST .../plugin/tasks/delete_all` |
| Provider missing | plugin not `local runtime ready` |
| Upload 413 | nginx body size **and** `UPLOAD_FILE_*` |
| `.env` changed, container unchanged | 1.17: api/worker/web/plugin_daemon/sandbox load `.env`; nginx/ssrf/weaviate/db still need listed keys. Optional knobs live in `docker/envs/*.env`. Recreate the service (nginx `NGINX_*` ≠ reload). |
| HTTP / external KB 502 to `10.`/`192.168.` | Squid SSRF; `NO_PROXY` on api+worker and/or `SSRF_PROXY_ALLOW_PRIVATE_IPS` as **CIDR list** (not `true`) |
| `MILVUS_USER is required` | set `MILVUS_USER`/`MILVUS_PASSWORD` in compose **and** `.env` |
| `minimax_group_id` | old MiniMax models need Group ID, or delete that default |
| File preview broken in plugins | `INTERNAL_FILES_URL=http://api:5001` |
| Logged out / file URLs die | `SECRET_KEY` changed after boot (also kills model credential decrypt) |
| After reboot, nothing listens | nested boxes: manual `dockerd`, then compose up |
| Draft save 400 / `draft_workflow_not_sync` | stale workflow `hash` |
| Canvas "同步数据中" / React #130 | Socket.IO `/socket.io/` missing, `NEXT_PUBLIC_SOCKET_URL=localhost`, or DSL nodes lack top-level `type: custom` |
| Plugin icons 503 | nginx `console_limit` burst; give `/plugin/icon` its own location without limit |
| Recreate api/web then 502 | nginx cached upstream IP → `nginx -s reload` |
| 403 `/rbac` `/billing` RAG publish | community feature gate |
| `/agent` 404 vs empty app list | Studio `/agent` ≠ `agent-chat` |
| Bearer on `/console/api` | wrong surface |
| `Invalid upload file` | see service API (user + key + `/v1` upload) |
| External KB low scores / zero recall | RAGFlow `/dify/retrieval` has no rerank; **disable** Dify score_threshold |
| External KB path 404 | endpoint must be `.../dify` because Dify appends `/retrieval` |
| LLM empty text | thinking model `max_tokens` too small (use ≥16384) or missing user message |
| Tool `Unknown error` | `tool_name` is not the OpenAPI `operationId` |
| Publish "无效的变量" on Loop | break_conditions missing `id`/`varType`, or they reference child outputs |
| Publish "视觉变量不能为空" | `vision.enabled` without `configs` |
| Publish "Rerank 模型不能为空" | rerank missing `provider`/`model` (UI) vs `reranking_*` (engine) — write all four |
| `credentials is not initialized` | model row on the wrong provider, or orphan `provider_models` after daemon restart |
| `CONSOLE_API_URL` points at `api:5001` in the browser | leave `CONSOLE_API_URL`/`APP_API_URL` empty (relative via nginx) |
| 403 on `/rbac` | community |
| Empty `/workflow-app-logs` or `/workflow-runs` | default `triggered_from=debugging`; cleanup already ran | production needs `triggered_from=app-run`; see extras + `WORKFLOW_LOG_CLEANUP_*` |
| `/workflow-app-logs` 400 on a chat app | route is `mode=workflow` | use `/chat-conversations` |
| Agent debug `blocking` 400 | Studio is SSE-only | `response_mode=streaming` |
| Hit-test empty `records` | embedding down / threshold / still indexing | disable `score_threshold`; wait for index; RAGFlow use 0 |

## Compose health
```bash
sudo docker compose ps
sudo docker compose logs --tail=80 api plugin_daemon nginx api_websocket
curl -sS http://127.0.0.1/console/api/setup
curl -sS http://127.0.0.1/console/api/version
# Socket.IO (expect 101 or 426, not 308)
curl -s -o /dev/null -w "%{http_code}" -H "Upgrade: websocket" -H "Connection: Upgrade" \
  "http://127.0.0.1/socket.io/?EIO=4&transport=websocket"
```
Never `compose down -v`. After `--force-recreate`, reload nginx.

## Env injection
1.17: api / worker / worker_beat / web / plugin_daemon / sandbox have `env_file` including `./.env`, so keys in `.env` **do** inject. nginx / ssrf_proxy / weaviate / redis / db still only see listed `environment:` or `command:` interpolation. Copy `docker/envs/**/*.env.example` → `*.env` or advanced knobs never appear. `POSTGRES_*` and `CELERY_AUTO_SCALE` **are** interpolated in 1.17. Verify with `docker exec <svc> printenv KEY`. Procedure: [Dify compose and config](sand-workflow:dify-compose-and-config).

## Plugins / models / RAG
Installed ≠ credentials saved. `high_quality` needs embedding. External KB: [Dify knowledge bases](sand-workflow:dify-knowledge-bases). MiniMax is a cloud API — on an air-gap, remove it as the workspace default.

## Nested Docker
`whiteout … operation not permitted` → `fuse-overlayfs`. ICC broken → `bridge-nf-call-iptables`.

## Do not
Set `DEPLOYMENT_EDITION=ENTERPRISE`. Open container egress with iptables to "fix" marketplace. Delete `volumes/` to fix one plugin. Put host passwords or `SECRET_KEY` into skills/git.
