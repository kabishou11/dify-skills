---
name: Dify compose and config
description: >-
  Use this when changing self-hosted Dify 1.17 Community compose/.env knobs — workers, timeouts, uploads, workflow limits, nginx, postgres/redis, mail, login gates, logging, or env injection (recreate vs reload). Use this to tune a new isomorphic box to production-grade platform settings (not custom tools).
---
# Dify compose and config

## Instructions

Tune **Dify 1.17 Community itself** (compose, `.env`, nginx, workers, timeouts, uploads, caps, sandbox, SSRF, Postgres/Redis, login/mail, json-file logs). This is **not** custom OpenAPI tools, OCR workflows, or DSL import.

Keep `DEPLOYMENT_EDITION=COMMUNITY`. Never write passwords or `SECRET_KEY` into skills/git. Never `compose down -v`. Never `pull :latest` without a digest. Do not treat a live production stack as a greenfield box — read it, then edit the **new** compose directory.

Symptoms (401, 413, uv, Socket.IO hang): [Dify troubleshooting](sand-workflow:dify-troubleshooting). SSRF / air-gap URLs: [Dify intranet](sand-workflow:dify-intranet). Model rows: [Dify model providers](sand-workflow:dify-model-providers). Dumps: [Dify backup and upgrade](sand-workflow:dify-backup-and-upgrade). Offline plugins (one step): [Dify plugin install](sand-workflow:dify-plugin-install).

### How values actually land (read before editing)

Three layers. **Runtime `docker exec <svc> printenv KEY` wins.** `.env` on disk is not truth.

| Layer | What it does |
|---|---|
| Official 1.17 `env_file` | api / worker / worker_beat / web / plugin_daemon / sandbox load `.env` last. Copy `docker/envs/**/*.env.example` → `*.env` or advanced knobs never appear. |
| Compose `environment:` | **Overrides** env_file. nginx / ssrf_proxy / redis / db often only see listed keys or `command:`. A customized clone may list *everything* on api (then changing `.env` alone does nothing). |
| Bind-mounted conf | Some clones bind `nginx/nginx.conf` and `ssrf_proxy/squid.conf`. Then `NGINX_*` / `SSRF_PROXY_ALLOW_PRIVATE_*` in compose are **ignored**. Edit the file. |

Name remaps (`.env` → process): `PLUGIN_DAEMON_KEY` → daemon `SERVER_KEY`; `PLUGIN_MAX_PACKAGE_SIZE` → `MAX_PLUGIN_PACKAGE_SIZE`; `SANDBOX_WORKER_TIMEOUT` → sandbox `WORKER_TIMEOUT`.

### Recreate vs reload

| Change | Apply |
|---|---|
| Official nginx templates (`NGINX_*` body size, proxy timeouts, HTTPS) | **recreate nginx** (entrypoint `envsubst`). `nginx -s reload` does **not** re-render templates. |
| Bind-mounted `nginx.conf` | edit file, then **`nginx -s reload`** |
| Recreated api/web then 502 | `nginx -s reload` (stale upstream IP). Start **api_websocket** first. |
| Official `SSRF_PROXY_ALLOW_PRIVATE_*` | **recreate ssrf_proxy** |
| Bind-mounted `squid.conf` | edit file, recreate **ssrf_proxy** (Squid does not hot-reload ACLs reliably) |
| `POSTGRES_*` / db `command:` | **recreate db_postgres** |
| `CELERY_*` | **recreate worker** (and worker_beat if poller/cleanup flags) |
| Canvas Loop / tools / iterations / web generate timeouts | **recreate web** (`NEXT_PUBLIC_*` / entrypoint). Listing the key only on **api** does not change the editor. |
| API flags, `WORKFLOW_MAX_*`, uploads, mail, `NO_PROXY` | **recreate api + worker** (+ beat if schedule/cleanup) |
| Socket.IO workers | recreate **api_websocket** |
| Sandbox kill time / network | **recreate sandbox** (+ api+worker if `CODE_EXECUTION_*`) |
| plugin package size / uv index | **recreate plugin_daemon** |

Never `compose down -v`. Prefer `compose up -d --no-deps --force-recreate <svc>`. Verify `docker exec <svc> printenv KEY`. Nginx live: `docker exec <nginx> nginx -T | grep client_max_body_size`.

### Done when (new-box platform)

- Console login works (`GET /console/api/setup` finished; CSRF on GET).
- `curl <llm>:8001/v1/models` succeeds **and** Dify has an OpenAI-compatible / vLLM row pointing at it. **One** LLM on :8001. Embedding :8000 and rerank :8002 are separate. No second LLM. No MTP.
- Large PDF upload does not 413 (nginx body **>** Dify `UPLOAD_*`).
- A long workflow is not killed at 60s/120s/360s: gunicorn **and** nginx proxy **and** `WORKFLOW_MAX_EXECUTION_TIME` ≥ **7200** for contract-review / OCR-class runs.
- If you need cron: **worker_beat** up, worker `-Q` still includes `schedule_poller,schedule_executor` (do not override queues and drop them). `ENABLE_WORKFLOW_SCHEDULE_POLLER_TASK` defaults true.
- SSRF/NO_PROXY lets api reach the host LLM (`:8001`) and other internal HTTP; do **not** `http_access allow all` and do not `SSRF_PROXY_ALLOW_PRIVATE_IPS=*`.
- Images pinned by digest. `DEPLOYMENT_EDITION=COMMUNITY`.

### New-box order

1. Diff the new compose against a healthy clone: `printenv` + `nginx -T` + db `command:` — not the `.env` file alone.
2. Apply the tables below. Interpolate `${VAR}` in compose when the clone lists keys; do not assume env_file.
3. Recreate only the services in the Apply column.
4. Curl / printenv verify. Failures → troubleshooting.

### Do not copy these clone mistakes

| Seen on a tuned clone | Why it is wrong | New box |
|---|---|---|
| `.env` `GUNICORN_TIMEOUT=360` / `APP_MAX_EXECUTION_TIME=1200` while compose hardcodes 7200 | Disk `.env` lies | Trust `printenv`; set **both** compose `environment:` and `.env` |
| `CELERY_AUTO_SCALE=true` without `CELERY_MAX_WORKERS` in **worker** env | Entrypoint uses `nproc` (hundreds of greenlets; steals CPU from the GPU LLM) | Pass `CELERY_MIN_WORKERS=4` and `CELERY_MAX_WORKERS=16` into worker |
| Loop 3000 on **api** only | Canvas still uses web default 100 | Also recreate **web** with `LOOP_NODE_MAX_COUNT` |
| compose `NGINX_CLIENT_MAX_BODY_SIZE=100M` while bind-mount nginx is `500M` | Listed env never reaches nginx | Edit `nginx.conf` (or official templates), not the api env copy |
| daemon `MAX_PLUGIN_PACKAGE_SIZE=50MiB` vs api `500MiB` | Upload 413 on `.difypkg` | Same byte value on **plugin_daemon** |
| `CONSOLE_API_URL=http://127.0.0.1:5001` on **web** | Browser talks to localhost | Web: **empty** `CONSOLE_API_URL` / `APP_API_URL` |
| `NEXT_PUBLIC_SOCKET_URL=ws://<old-host>` | Remote canvas “同步数据中” | Browser-reachable host of **this** box |
| `ubuntu/squid:latest` / `nginx:latest` | Untagged pulls | Pin digest |
| Squid `http_access allow all` | Open proxy | Allow RFC1918 + localhost; deny the rest |
| `MARKETPLACE_ENABLED=true` + public `CHECK_UPDATE_URL` on air-gap | UI probes SaaS | false + empty URL |
| `ENABLE_WEBSITE_JINAREADER/FIRECRAWL/WATERCRAWL=true` | SaaS crawlers | false unless asked |
| json-file `LogConfig: {}` on old containers | daemon `50m×3` only applies after dockerd loaded log-opts **and** the container was recreated | Set compose `logging:` on Dify services |

### Tables: knob / clone-like example (will change) / new-box / why / apply

Clone-like numbers are from a 1.17 Community box that already runs long OCR/contract-review graphs. Copy **intent**, not host IPs or secrets.

#### 1. Workers / Celery / beat

| Knob | Clone-like (changes) | New box | Why | Apply |
|---|---|---|---|---|
| `SERVER_WORKER_AMOUNT` | 8 | **8** on ≥32 CPU; 2–4 if RAM tight | gunicorn processes; ~2–3GiB each | recreate **api** |
| `SERVER_WORKER_CONNECTIONS` | 500 | **500** | gevent pool; official default 10 is tiny | recreate **api** |
| `GUNICORN_TIMEOUT` | 7200 (`.env` may still say 360) | **7200** | SSE / long run; 360 kills contract-review | recreate **api** (+ websocket) |
| `API_WEBSOCKET_WORKER_AMOUNT` | 2 | **2** | canvas Socket.IO | recreate **api_websocket** |
| `API_WEBSOCKET_WORKER_CONNECTIONS` | listed 1000 (`.env` 2000 ignored) | **1000–2000** via websocket `environment:` | must be on the websocket service overlay | recreate **api_websocket** |
| `CELERY_AUTO_SCALE` | true | **true** | scale with load | recreate **worker** |
| `CELERY_MIN_WORKERS` / `MAX_WORKERS` | often **unset** → autoscale nproc | **4 / 16** (cap 16 so the LLM keeps CPU) | must appear in worker env, not only `.env` | recreate **worker** |
| `CELERY_WORKER_AMOUNT` | 4 when auto-scale off | unused if auto-scale on | empty in some files silently becomes 1 | recreate **worker** |
| worker `-Q` | includes `schedule_poller,schedule_executor` | **keep those queues** | cron Trigger never fires without them | recreate **worker** if you override queues |
| `ENABLE_WORKFLOW_SCHEDULE_POLLER_TASK` | unset = true | **true** if you need daily cron | beat polls every `WORKFLOW_SCHEDULE_POLLER_INTERVAL` (default 1 min) | recreate **worker_beat** |
| `GRAPH_ENGINE_MIN_WORKERS` / `MAX_WORKERS` | unset (3 / 10) | leave default unless graphs stall | api+worker threadpool | recreate api+worker |

#### 2. Timeouts (raise the layer that actually cut you off)

Keep `DIFY_AGENT_RUN_TIMEOUT_SECONDS` ≥ `APP_MAX_EXECUTION_TIME` ≥ `WORKFLOW_MAX_EXECUTION_TIME` if Studio agents run the same graphs. Callers still need HTTP client ≥ 600s (not a compose knob).

| Knob | Official-ish | Clone-like | New box | Why | Apply |
|---|---|---|---|---|---|
| nginx `proxy_read/send_timeout` | 3600s | **7200s** in bind-mount conf | **7200s** | 3600 can still cut a 1h video/OCR graph | nginx recreate **or** reload bind-mount |
| `APP_MAX_EXECUTION_TIME` | 1200 | **7200** | **7200** | wall clock for app run | api+worker |
| `WORKFLOW_MAX_EXECUTION_TIME` | 3600 | **7200** | **7200** | must match gunicorn/nginx | api+worker |
| `TEXT_GENERATION_TIMEOUT_MS` | 60000 | 120000 | **120000** | web generate | **web** |
| `WORKFLOW_GENERATION_TIMEOUT_MS` | 180000 | 180000 (`.env` 300000 may be ignored) | **180000–300000** on **web** | editor vs runtime are different planes | **web** |
| `HTTP_REQUEST_MAX_*_TIMEOUT` | 10 / 600 / 600 | often unset | keep **read/write 600** | HTTP node | api+worker |
| `SANDBOX_WORKER_TIMEOUT` | 15 | **15** | **60** if code nodes `sleep`/poll; else 15 | process kill inside sandbox | sandbox + api+worker |
| `CODE_EXECUTION_READ_TIMEOUT` | 60 | **60** (often hardcoded) | **> sandbox timeout** | API wait on sandbox HTTP | api+worker |
| `PLUGIN_MAX_EXECUTION_TIMEOUT` | 600 | **1800** | **1800** | fat plugin tools | plugin_daemon + api |
| `SSRF_DEFAULT_READ_TIME_OUT` | 5 | 5 | **60** if traffic goes through Squid | too low for slow internal HTTP | ssrf_proxy |
| `CONTENT_EXTRACTION_TIMEOUT` | 600 | 600 | 600 | document extractor | api+worker |
| `DIFY_AGENT_RUN_TIMEOUT_SECONDS` | 3600 | **1200** (below workflow 7200) | **≥ workflow** (7200) | Studio agents otherwise die first | agent_backend + api |

#### 3. Uploads and 413

Nginx must be **larger than** Dify MB limits. 413 is almost always nginx.

| Knob | Official | Clone-like | New box | Apply |
|---|---|---|---|---|
| `UPLOAD_FILE_SIZE_LIMIT` (MB, documents) | 15 | **20** | **20** (raise if you ingest bigger PDFs) | api+worker |
| `UPLOAD_VIDEO_FILE_SIZE_LIMIT` | 100 | **400** | **400** if hour-long media; else 100 | api+worker |
| `UPLOAD_AUDIO_FILE_SIZE_LIMIT` | 50 | **100** | **100** | api+worker |
| `UPLOAD_FILE_BATCH_LIMIT` / `BATCH_UPLOAD_LIMIT` | 5 / 20 | **99999** | **20–100** unless operators need unbounded batches | api+worker |
| nginx `client_max_body_size` | 100M | **500M** in `nginx.conf` (compose listed 100M is a lie) | **500M** if video 400; else ≥ 50M | nginx |
| `PLUGIN_MAX_PACKAGE_SIZE` | 50MiB | api 500MiB / daemon **50MiB** | **same on api and plugin_daemon** (50MiB enough for most; 500MiB if fat `.difypkg`) | api + **plugin_daemon** |

#### 4. Workflow / canvas (two planes)

| Knob | Official | Clone-like | New box | Apply |
|---|---|---|---|---|
| `WORKFLOW_MAX_EXECUTION_STEPS` | 500 | **20000** | **20000** for OCR-loop / long graphs; 500 is too small | api+worker |
| `WORKFLOW_CALL_MAX_DEPTH` | 5 | 5 | 5 unless nested workflow-as-tool | api+worker |
| `MAX_VARIABLE_SIZE` | 204800 | **2097152** | **2097152** (OCR markdown) | api+worker |
| `LOOP_NODE_MAX_COUNT` | 100 | **3000** on api | **3000** if you poll async jobs; also set on **web** | api+worker **and web** |
| `MAX_TOOLS_NUM` / `MAX_PARALLEL_LIMIT` | 10 / 10 | **20 / 20** | **20 / 20** | api **and web** |
| `MAX_TREE_DEPTH` | 50 | 50 | 50 | web |
| `TOP_K_MAX_VALUE` | 10 | **100** | **50–100** | api **and web** |
| `INDEXING_MAX_SEGMENTATION_TOKENS_LENGTH` | 4000 | **8000** | **8000** | api+worker |
| `EMBEDDING_BATCH_SIZE` |  | **32** | **32** | api+worker |
| `APP_MAX_ACTIVE_REQUESTS` | 0 = unlimited | **200** | **200** | api+worker |

#### 5. Sandbox

| Knob | Clone-like | New box | Why | Apply |
|---|---|---|---|---|
| `SANDBOX_ENABLE_NETWORK` | true | **true** | CodeExecutor always sends enable_network; egress still via Squid | sandbox |
| `SANDBOX_HTTP(S)_PROXY` | `http://ssrf_proxy:3128` | same | do not point at the public net | sandbox |
| `volumes/sandbox/conf` `worker_timeout` | image default / 5 in example yaml | match env | yaml and env can disagree | recreate sandbox |
| `/dependencies` extra pip | empty | only if a code node needs it | not PyPI torch; local index | recreate sandbox |

#### 6. SSRF / intranet allowlist

Do **not** `*`. HTTP nodes and OpenAPI go through Squid unless the host is on api+worker `NO_PROXY`.

| Knob | Clone-like | New box | Apply |
|---|---|---|---|
| `NO_PROXY` / `no_proxy` | docker DNS names + loopback + **that** box LAN IP | `localhost,127.0.0.1,<this-box-lan-ip>,api,api_websocket,db_postgres,redis,plugin_daemon,sandbox,ssrf_proxy,milvus-standalone,.local,.internal` | api+worker |
| `SSRF_PROXY_ALLOW_PRIVATE_IPS` | often unset (custom squid instead) | `10.0.0.0/8,172.16.0.0/12,192.168.0.0/16` — **CIDR list, not `true`** | ssrf_proxy |
| squid `http_access` | some clones `allow all` | **allow localhost + localnet; deny the rest** | ssrf_proxy |
| Host LLM `:8001` / embedding `:8000` / rerank `:8002` | on `NO_PROXY` via LAN IP | put **this** host IP (or `host.docker.internal`) on `NO_PROXY`; do not publish a second LLM | api+worker |
| `HTTP_PROXY` on api | optional parent proxy | omit unless that proxy container exists | api+worker |

#### 7. Postgres / Redis (Dify stack only — not FineBI)

| Knob | Clone-like | New box | Apply |
|---|---|---|---|
| `max_connections` | 500 in db `command:` | **500** | recreate **db_postgres** |
| `shared_buffers` / `effective_cache_size` | 4GB / 32GB | same if host RAM ≥ 64GB; else 1GB / 4GB | db_postgres |
| `work_mem` / `maintenance_work_mem` | 16MB / 256MB | keep | db_postgres |
| SQLAlchemy pool | 30 + overflow 10 | keep `pool × (api workers + celery) < max_connections` | api+worker |
| Redis `maxmemory` | 256mb allkeys-lru | **256mb–1gb**; match `CELERY_BROKER_URL` password | recreate **redis** |

Changing `REDIS_PASSWORD` must update broker URLs. Do not touch other products' Postgres.

#### 8. Login / mail / marketplace / plugin signature

| Knob | New box | Why | Apply |
|---|---|---|---|
| `ALLOW_REGISTER` / `ALLOW_CREATE_WORKSPACE` | **false** | intranet | api+web |
| `ENABLE_EMAIL_PASSWORD_LOGIN` | **true** | | api+web |
| `ENABLE_EMAIL_CODE_LOGIN` | false unless SMTP works | | api+web |
| `MAIL_TYPE` | **smtp** (not `resend`) | official shared example is wrong offline | api+worker |
| `MARKETPLACE_ENABLED` | **false** on air-gap | UI stops probing | api+web |
| `CHECK_UPDATE_URL` | **empty** | | api |
| `FORCE_VERIFYING_SIGNATURE` | true unless you install unsigned `.difypkg` | then false on **plugin_daemon** | plugin_daemon |
| `ENABLE_CHECK_UPGRADABLE_PLUGIN_TASK` | **false** offline | | api+beat |
| `DISABLE_TELEMETRY` | **true** | | api |
| crawler flags | **false** | no SaaS | api+worker |
| `ENABLE_CONVERSATION_CLEANUP_TASK` / `WORKFLOW_LOG_CLEANUP_ENABLED` | **false** | beat would delete history | worker_beat |
| `ENABLE_COLLABORATION_MODE` | true + `collaboration` profile | canvas sync | api+web |
| `TRIGGER_URL` | origin callers hit (scheme+host) | default `http://localhost` is only for local curl | api+worker |

Offline plugin install: host `.difypkg` + local PEP 503; do not open iptables. Details in plugin-install.

#### 9. json-file logs

| Knob | Clone-like | New box | Apply |
|---|---|---|---|
| compose `logging.driver` | often unset → inherit dockerd | **json-file** `max-size=50m` `max-file=3` on Dify services | recreate those services |
| dockerd `log-opts` | 50m×3, but **old** containers keep unlimited files | do **not** restart dockerd just to cap logs | truncate `*-json.log` if a file already >1GB |
| `LOG_TZ` | UTC | `Asia/Shanghai` if that is operator TZ | api+worker |
| `ENABLE_REQUEST_LOGGING` | False | False | api |

Do not `docker system prune`. Do not delete `containers/`. FineBI uses a different log driver — leave it.

#### 10. URLs / CSRF / reverse proxy (must change on a new host)

| Knob | New box | Apply |
|---|---|---|
| web `CONSOLE_API_URL` / `APP_API_URL` | **empty** (browser relative via nginx) | recreate **web** |
| `SERVER_CONSOLE_API_URL` | `http://api:5001` (SSR, container DNS) | web |
| `INTERNAL_FILES_URL` | `http://api:5001` (plugins, not the browser) | api |
| `NEXT_PUBLIC_SOCKET_URL` | `ws://<browser-reachable-host>` of **this** box, not `localhost`, not `api` | **web** |
| `FILES_URL` / `CONSOLE_WEB_URL` | empty unless you serve a public CDN | web |
| CSRF | 1.17 **GET** needs `X-CSRF-Token` + cookie | n/a (console-api) |
| `COOKIE_DOMAIN` | empty unless you split console/app hosts | web |

#### 11. Platform model access (not the tool marketplace)

Compose cannot register the Dify model row. After SSRF/NO_PROXY: [Dify model providers](sand-workflow:dify-model-providers). Endpoint `http://<host>:8001/v1` must resolve **inside api**. Timeout stack above must outlive a thinking completion (`max_tokens` ≥ 16384).

## Examples

**Raise the long-run stack on a new box** (compose lists keys):

1. Set `GUNICORN_TIMEOUT=7200`, `APP_MAX_EXECUTION_TIME=7200`, `WORKFLOW_MAX_EXECUTION_TIME=7200`, `WORKFLOW_MAX_EXECUTION_STEPS=20000` on the api environment anchor.
2. Set nginx `proxy_read_timeout` / `proxy_send_timeout` **7200s** and `client_max_body_size 500M` in the file nginx actually serves.
3. `compose up -d --no-deps --force-recreate api worker worker_beat api_websocket`
4. Reload nginx only after websocket is healthy.
5. `docker exec <api> printenv GUNICORN_TIMEOUT WORKFLOW_MAX_EXECUTION_TIME` → 7200.

**Fix Celery eating CPU:**

1. Put `CELERY_AUTO_SCALE=true`, `CELERY_MIN_WORKERS=4`, `CELERY_MAX_WORKERS=16` on the **worker** service environment.
2. Recreate worker. Confirm cmdline is `--autoscale=16,4`, not `--autoscale=<nproc>,1`.

**Fix canvas Loop still 100:**

1. Add `LOOP_NODE_MAX_COUNT=3000` (and tools/parallel/top_k) to **web** environment.
2. Recreate **web**. Api-only changes never move the editor slider.

## Performance Notes

- Dify shares the box with the GPU LLM. Cap Celery at 16. Do not autoscale to nproc.
- One LLM on :8001 (Dense 27B **TP=4**, `max-model-len` 262144, `--disable-custom-all-reduce`). Embedding :8000 and rerank :8002 stay up. Do not enable MTP. The old “27B must TP=1 / ctx 16384” rule is obsolete.
- json-file without `max-size` grows forever; cap in **compose** so you never need a dockerd restart.
- `WORKFLOW_LOG_CLEANUP_ENABLED=true` deletes run history at 02:00 beat TZ — leave it off.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `.env` changed, `printenv` old | key is listed in compose `environment:` or bind-mount conf | edit the layer that actually injects |
| 413 on PDF | nginx body < file | raise `client_max_body_size`; recreate/reload nginx |
| Run dies at ~6 min | gunicorn 360 | 7200 on api+websocket |
| Run dies at ~60s / 120s | web generate timeouts or sandbox 15 | web and/or sandbox |
| Cron never fires | beat down, poller false, or `-Q` dropped `schedule_*` | recreate beat+worker; do not customize queues |
| HTTP to `:8001` 502 | Squid + missing NO_PROXY / CIDR | intranet skill |
| Canvas “同步数据中” | `NEXT_PUBLIC_SOCKET_URL` wrong or websocket down | web URL; start websocket before nginx reload |
| Loop cap unchanged in UI | web not recreated | web env |
| Plugin pkg 413 | daemon still 50MiB | plugin_daemon `MAX_PLUGIN_PACKAGE_SIZE` |
| nginx 502 `host not found in upstream api_websocket` | reload while websocket stopped | start websocket first |

## Do not

Set `DEPLOYMENT_EDITION=ENTERPRISE`. Open egress with iptables. `compose down -v`. Blind-overwrite compose on upgrade. Put secrets in skills. Tune FineBI/Milvus-outside-Dify here. Reconfigure a live production clone “as if” it were empty. Publish frozen product apps.
