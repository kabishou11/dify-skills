---
name: Dify compose and config
description: >-
  Use this when changing self-hosted Dify 1.17 Community compose/.env knobs — workers, timeouts, uploads, workflow limits, nginx, postgres/redis, mail, login gates, or env injection (recreate vs reload).
---
# Dify compose and config

Use this when changing self-hosted Dify **1.17 Community** knobs (`.env`, `docker/envs/*.env`, compose). Symptoms (401, 413, uv, Socket.IO hang): [Dify troubleshooting](sand-workflow:dify-troubleshooting). SSRF / air-gap URLs: [Dify intranet](sand-workflow:dify-intranet). Plugin packages: [Dify plugin install](sand-workflow:dify-plugin-install). Dumps: [Dify backup and upgrade](sand-workflow:dify-backup-and-upgrade).

Keep `DEPLOYMENT_EDITION=COMMUNITY`. Never write passwords or `SECRET_KEY` into skills/git.

## 1.17 file layout (read first)

| File | Role |
|---|---|
| `docker/.env` (copy of `.env.example`) | Essential. Compose interpolates `${VAR}`. Loaded **last** on api/worker/web/plugin_daemon/sandbox. |
| `docker/envs/**/*.env` (copy from `*.env.example`) | Optional/advanced. `required: false` — if the file is missing, those knobs never appear. |
| Compose `environment:` | Overrides env_file. **nginx / ssrf_proxy / weaviate / redis / db** only see listed keys or `command:` interpolation. |

Copy at least `envs/core-services/shared.env.example` → `shared.env`. Upload, workflow caps, mail, and login gates live there, not in the slim `.env.example`.

Name remaps inside the container (`.env` name → process name):

| `.env` | Inside |
|---|---|
| `PLUGIN_DAEMON_KEY` | plugin_daemon `SERVER_KEY` |
| `PLUGIN_MAX_PACKAGE_SIZE` | `MAX_PLUGIN_PACKAGE_SIZE` |
| `PLUGIN_PYTHON_ENV_INIT_TIMEOUT` | `PYTHON_ENV_INIT_TIMEOUT` |
| `SANDBOX_API_KEY` | sandbox `API_KEY` |
| `SANDBOX_WORKER_TIMEOUT` | sandbox `WORKER_TIMEOUT` |

### Recreate vs reload

| Change | Apply |
|---|---|
| `NGINX_*` (body size, timeouts, HTTPS, Socket.IO upstream) | **recreate nginx** (entrypoint re-renders templates). `nginx -s reload` does **not** re-run `envsubst`. |
| Recreated api/web then 502 | `nginx -s reload` (stale upstream IP only) |
| `SSRF_PROXY_ALLOW_PRIVATE_*` | **recreate ssrf_proxy** |
| `POSTGRES_*` | **recreate db_postgres** (`command:` interpolates) |
| `CELERY_*` | **recreate worker** (entrypoint; not hardcoded `--autoscale`) |
| Canvas Loop/tools/iterations caps | **recreate web** (`web/docker/entrypoint.sh` copies to `NEXT_PUBLIC_*`) |
| API feature flags, `WORKFLOW_MAX_*`, uploads, mail | **recreate api + worker** |
| Socket.IO workers | recreate **api_websocket** (`collaboration` profile) |

Never `compose down -v`. Verify: `docker exec <svc> printenv KEY`. Nginx: `docker exec <nginx> nginx -T \| grep client_max_body_size`. After env change: `GET /console/api/system-features` and `/features`.

## Workers

| Key | Default | Service |
|---|---|---|
| `SERVER_WORKER_AMOUNT` | 1 | api gunicorn `--workers` |
| `SERVER_WORKER_CLASS` | gevent | api |
| `SERVER_WORKER_CONNECTIONS` | 10 | api |
| `GUNICORN_TIMEOUT` | 360 | api |
| `API_WEBSOCKET_WORKER_AMOUNT` / `_CLASS` / `_CONNECTIONS` / `_GUNICORN_TIMEOUT` | 1 / geventwebsocket / 1000 / 360 | api_websocket (mapped onto `SERVER_WORKER_*`) |
| `CELERY_WORKER_AMOUNT` | 4 in `.env.example`; **empty in shared.env → 1** | worker |
| `CELERY_AUTO_SCALE` | false | worker. `true` → `--autoscale=${CELERY_MAX_WORKERS:-nproc},${CELERY_MIN_WORKERS:-1}` |
| `GRAPH_ENGINE_MIN_WORKERS` / `MAX_WORKERS` | 3 / 10 | api+worker |
| `MAX_SUBMIT_COUNT` | 100 | api+worker threadpool |

Empty `CELERY_WORKER_AMOUNT` silently becomes **1**. Recreate **worker** for Celery, not api.

## Timeouts (pick the failing layer)

Raise the layer that actually cut you off. Keep `DIFY_AGENT_RUN_TIMEOUT_SECONDS` ≥ `APP_MAX_EXECUTION_TIME` ≥ `WORKFLOW_MAX_EXECUTION_TIME` when Studio agents run long graphs.

| Layer | Keys | Recreate |
|---|---|---|
| nginx | `NGINX_PROXY_READ_TIMEOUT` / `SEND_TIMEOUT` (3600), `NGINX_KEEPALIVE_TIMEOUT` | nginx |
| gunicorn | `GUNICORN_TIMEOUT` 360 | api |
| app / workflow | `APP_MAX_EXECUTION_TIME`, `WORKFLOW_MAX_EXECUTION_TIME` (3600) | api+worker |
| web generate | `TEXT_GENERATION_TIMEOUT_MS` 60000, `WORKFLOW_GENERATION_TIMEOUT_MS` 180000 | **web** |
| HTTP Request node | `HTTP_REQUEST_MAX_CONNECT/READ/WRITE_TIMEOUT` (10/600/600) | api+worker |
| sandbox | `CODE_EXECUTION_*_TIMEOUT`, `SANDBOX_WORKER_TIMEOUT` (15) | api+worker+sandbox |
| plugin | `PLUGIN_MAX_EXECUTION_TIMEOUT`, `PLUGIN_DAEMON_TIMEOUT` (600) | plugin_daemon (+ api) |
| agent backend | `DIFY_AGENT_RUN_TIMEOUT_SECONDS` (3600) | agent_backend + api+worker |

Service API callers still need their **HTTP client** timeout ≥ 600s; that is not a compose knob.

## Uploads and 413

Set **nginx larger than Dify**:

- `UPLOAD_FILE_SIZE_LIMIT` (15 MB, in `shared.env`)
- `UPLOAD_IMAGE/VIDEO/AUDIO_FILE_SIZE_LIMIT`, `UPLOAD_SKILL_FILE_SIZE_LIMIT`, `WORKFLOW_FILE_UPLOAD_LIMIT`
- `UPLOAD_FILE_BATCH_LIMIT`, `BATCH_UPLOAD_LIMIT`
- `PLUGIN_MAX_PACKAGE_SIZE` (50 MiB)
- `NGINX_CLIENT_MAX_BODY_SIZE` (100M) — recreate **nginx**

413 is almost always nginx. Recreate api+worker+nginx.

## Workflow and canvas (two planes)

**API (runtime)** — recreate api+worker:

- `WORKFLOW_MAX_EXECUTION_STEPS` 500
- `WORKFLOW_MAX_EXECUTION_TIME` 3600
- `WORKFLOW_CALL_MAX_DEPTH` 5
- `MAX_VARIABLE_SIZE` 204800
- `TEMPLATE_TRANSFORM_MAX_LENGTH` 400000
- `APP_MAX_ACTIVE_REQUESTS` 0 = unlimited

**Web (canvas UI)** — recreate **web** or the editor still blocks you:

- `LOOP_NODE_MAX_COUNT` 100
- `MAX_ITERATIONS_NUM` 99
- `MAX_TOOLS_NUM` 10
- `MAX_PARALLEL_LIMIT` 10
- `MAX_TREE_DEPTH` 50
- `TOP_K_MAX_VALUE` 10
- `INDEXING_MAX_SEGMENTATION_TOKENS_LENGTH` 4000 (also API)

Raising Loop max without recreating web does nothing in the UI. Raising UI without API steps/time still fails at run.

## Nginx

`NGINX_CLIENT_MAX_BODY_SIZE`, proxy timeouts, `NGINX_HTTPS_ENABLED`, ports, `NGINX_SOCKET_IO_UPSTREAM` (default `api_websocket:5001`). Recreate nginx to apply templates. `nginx -s reload` only after api/web/websocket IP change.

Do not reload (or recreate) nginx while `api_websocket` is stopped: `host not found in upstream "api_websocket:5001"` takes down the whole console with 502. Start websocket first, then reload.

## Postgres and Redis

`POSTGRES_MAX_CONNECTIONS`, `POSTGRES_SHARED_BUFFERS`, `WORK_MEM`, `MAINTENANCE_WORK_MEM`, `EFFECTIVE_CACHE_SIZE` are in db `command:` and **do** interpolate from `.env`. Recreate **db_postgres**.

Keep `SQLALCHEMY_POOL_SIZE` + `MAX_OVERFLOW` × (api workers + celery concurrency) **<** `max_connections`.

Redis password is `command: redis-server --requirepass`. Changing `REDIS_PASSWORD` recreates redis **and** must match `CELERY_BROKER_URL`.

## Vector store / profiles

`COMPOSE_PROFILES=${VECTOR_STORE},${DB_TYPE},collaboration`. Dropping `collaboration` stops `api_websocket` → canvas "同步数据中". Switching `VECTOR_STORE` is a profile + data move, not a toggle. CJK weaviate: `WEAVIATE_ENABLE_TOKENIZER_GSE=true` (recreate weaviate). Milvus needs `MILVUS_USER`/`MILVUS_PASSWORD`.

## URLs

Leave `CONSOLE_API_URL` and `APP_API_URL` **empty** (browser relative via nginx). `SERVER_CONSOLE_API_URL=http://api:5001` is **required** for 1.17 Next.js SSR (missing → “Server console API URL is not configured”). `INTERNAL_FILES_URL=http://api:5001` (plugins, not the browser). `NEXT_PUBLIC_SOCKET_URL` = what the **browser** can reach. Air-gap: `CHECK_UPDATE_URL=` empty, `MARKETPLACE_ENABLED=false`. Triggers: `TRIGGER_URL`, `ENDPOINT_URL_TEMPLATE`.

## SSRF (short)

`SSRF_PROXY_ALLOW_PRIVATE_IPS` is a **CIDR list** (`10.0.0.0/8,172.16.0.0/12`), not `true`. `SSRF_PROXY_ALLOW_PRIVATE_DOMAINS` = dstdomain suffixes. Recreate **ssrf_proxy**. Also put internal hosts on api+worker `NO_PROXY`. Details: [Dify intranet](sand-workflow:dify-intranet).

## Sandbox / plugins (knobs only)

`SANDBOX_WORKER_TIMEOUT` 15, `CODE_EXECUTION_READ_TIMEOUT` 60, `CODE_MAX_STRING_LENGTH`, `PLUGIN_PYTHON_ENV_INIT_TIMEOUT`, `PLUGIN_MAX_EXECUTION_TIMEOUT`. Install/uv: plugin-install skill.

## Mail

This is Dify's invite / reset / email-code mailer, **not** the email plugin.

`MAIL_TYPE=smtp` (shared example defaults to `resend` — wrong on intranet), `SMTP_SERVER/PORT/USERNAME/PASSWORD/USE_TLS`, `MAIL_DEFAULT_SEND_FROM`. Recreate **api + worker**. Then `GET /console/api/system-features` and send an invite.

## Community gates

Keep `DEPLOYMENT_EDITION=COMMUNITY`. `/rbac` `/billing` 403 is expected. 1.17 still accepts a leftover `EDITION=` in `.env`; the process reads `DEPLOYMENT_EDITION`.

| Key | Typical |
|---|---|
| `ALLOW_REGISTER` | false |
| `ALLOW_CREATE_WORKSPACE` | false |
| `ENABLE_EMAIL_PASSWORD_LOGIN` | true |
| `ENABLE_EMAIL_CODE_LOGIN` | false (needs mail) |
| `ENABLE_COLLABORATION_MODE` | true, and `collaboration` in `COMPOSE_PROFILES` |
| `ENABLE_SKILL` | true (workspace Skills UI). 1.17.0 **upload** of Skill files is buggy — leave the flag on if you already use the library, but do not demo upload until a patch. |
| `ENABLE_CONVERSATION_CLEANUP_TASK` | **false** unless you want beat to delete old chats |
| `OPENAPI_ENABLED` + `ENABLE_OAUTH_BEARER` | both true for difyctl |
| `DISABLE_TELEMETRY` | true on intranet |
| `CREATORS_PLATFORM_FEATURES_ENABLED` | false on air-gap |
| `ENABLE_CHECK_UPGRADABLE_PLUGIN_TASK` | false on air-gap |
| `ENABLE_WEBSITE_JINAREADER/FIRECRAWL/WATERCRAWL` | false if no SaaS crawlers |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 60 |
| `INVITE_EXPIRY_HOURS` | 72 |

Recreate api+web (and worker for mail/tasks). Confirm with `GET /console/api/system-features`.

## Logging and workflow-log retention

`LOG_LEVEL`, `LOG_TZ` (default UTC — set `Asia/Shanghai` if that is the operator TZ), `LOG_OUTPUT_FORMAT`, `ENABLE_REQUEST_LOGGING`. Files: `docker compose logs` and `/app/logs/server.log` in api/worker.

Workflow **run** rows (Postgres), not api log files. Keys live in `docker/envs/core-services/shared.env` (copy from `*.env.example` or they never appear). Recreate **worker_beat** (+ worker) after change.

| Key | Default | Role |
|---|---|---|
| `WORKFLOW_LOG_CLEANUP_ENABLED` | false | Beat schedules `clean_workflow_runlogs_precise` at 02:00 (worker_beat TZ, usually UTC) |
| `WORKFLOW_LOG_RETENTION_DAYS` | 30 | Delete runs older than this; cascades messages / annotations / thoughts |
| `WORKFLOW_LOG_CLEANUP_BATCH_SIZE` | 100 | Rows per batch |
| `WORKFLOW_LOG_CLEANUP_SPECIFIC_WORKFLOW_IDS` | empty | Comma-separated **workflow** ids; empty = all |

HTTP to list remaining rows: [Dify workspace extras](sand-workflow:dify-workspace-extras) (`/workflow-app-logs`, `/workflow-runs`). Empty logs after enabling cleanup is expected once the cutoff passes.

## Storage (local default)

`STORAGE_TYPE=opendal`, `OPENDAL_SCHEME=fs`, `OPENDAL_FS_ROOT=storage` → `volumes/app/storage`. Do not switch S3/OSS in this skill unless asked.

## Do not

Set `DEPLOYMENT_EDITION=ENTERPRISE`. Open egress with iptables. `compose down -v`. Blind-overwrite compose on upgrade (merge keys; backup skill). Put secrets in skills.
