---
name: Dify troubleshooting
description: >-
  Use this when Dify login, plugins, models, RAG, uploads, or containers fail — CSRF, uv, 413, SSRF, stale failed tasks, reboot.
---
# Dify troubleshooting

## Instructions

Use this when Dify is up but something fails. Changing workers/timeouts/.env: [Dify compose and config](sand-workflow:dify-compose-and-config). Intranet/SSRF: [Dify intranet](sand-workflow:dify-intranet). Plugin uv: [Dify plugin install](sand-workflow:dify-plugin-install). Canvas/DSL: [Dify apps and workflows](sand-workflow:dify-apps-and-workflows). Prefixes: [Dify API catalog](sand-workflow:dify-api-catalog).

## Decide where it broke

| Symptom | Likely layer |
|---|---|
| Connection refused on `:80` | nginx / compose / dockerd |
| `/install` loops | admin not created |
| `401 Invalid encrypted data` | password not **Base64** |
| `401 CSRF` / `unauthorized` | missing CSRF **on GET too**, or session ~1h expired |
| Unauthenticated `/` is 307 `/signin` | 1.17 WebApp; follow redirects or open `/signin` |
| `Server console API URL is not configured` | web missing `SERVER_CONSOLE_API_URL=http://api:5001` |
| nginx 502 `host not found in upstream "api_websocket"` | websocket container down during nginx reload — start it first |
| Agent missing from `GET /apps` | roster is `GET /agent` |
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
| Draft save 400 `environment_variables` `extra_forbidden` | 1.17 dropped top-level `environment_variables` on graph sync. Send `graph`+`features`+`hash`; env edits use `environment_variable_patch` |
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
| Long workflow dies ~6 min | `GUNICORN_TIMEOUT` still 360 | 7200; compose `environment:` may ignore `.env` |
| Long workflow dies ~15s in code | `SANDBOX_WORKER_TIMEOUT` | raise sandbox; keep `CODE_EXECUTION_READ_TIMEOUT` larger |
| Celery pegs all CPUs | `CELERY_AUTO_SCALE` without `CELERY_MAX_WORKERS` in worker env | cap 16; confirm `--autoscale=16,4` |
| Schedule never fires | beat down or worker `-Q` dropped `schedule_*` | recreate beat+worker |
| 413 PDF but Dify limit is 20MB | nginx `client_max_body_size` still 100M / bind-mount not edited | `nginx -T`; 500M if you need 400MB video |
| `.env` 200M nginx, live 100M | listed compose env is not what nginx serves | bind-mount `nginx.conf` vs official templates |
| New box canvas sync hang | `NEXT_PUBLIC_SOCKET_URL` still the old host | recreate **web** |
| LLM 502 from a node | host not on `NO_PROXY` / Squid 5s | intranet skill |

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
Never `compose down -v`. After `--force-recreate`, reload nginx **only if** `api_websocket` is already up.

## Env injection
Official 1.17: api / worker / beat / web / plugin_daemon / sandbox have `env_file` including `./.env`. **Custom clones** often list the same keys in compose `environment:` (listed value wins) or bind-mount nginx/squid (then `NGINX_*` / `SSRF_*` never reach the process). Always `docker exec <svc> printenv KEY`. Procedure: [Dify compose and config](sand-workflow:dify-compose-and-config).

## Plugins / models / RAG
Installed ≠ credentials saved. `high_quality` needs embedding. External KB: [Dify knowledge bases](sand-workflow:dify-knowledge-bases). MiniMax is a cloud API — on an air-gap, remove it as the workspace default.

## Nested Docker
`whiteout … operation not permitted` → `fuse-overlayfs`. ICC broken → `bridge-nf-call-iptables`.

## Examples

New-box smoke (read-only on a live clone; apply only on the new compose dir):

```bash
curl -sS http://127.0.0.1/console/api/setup
curl -sS http://127.0.0.1:8001/v1/models
docker exec docker-api-1 printenv GUNICORN_TIMEOUT WORKFLOW_MAX_EXECUTION_TIME NO_PROXY
docker exec docker-nginx-1 nginx -T | grep -E 'client_max_body_size|proxy_read_timeout'
```

## Performance Notes

Cap json-file in compose (`50m` × 3). Old containers may have unlimited logs until recreated; truncate `*-json.log`, do not restart dockerd to apply daemon log-opts.

## Troubleshooting

The table above is the symptom index. Compose knobs: [Dify compose and config](sand-workflow:dify-compose-and-config).

## Do not
Set `DEPLOYMENT_EDITION=ENTERPRISE`. Open container egress with iptables to "fix" marketplace. Delete `volumes/` to fix one plugin. Put host passwords or `SECRET_KEY` into skills/git. Do not retune a live production stack as if it were empty.
