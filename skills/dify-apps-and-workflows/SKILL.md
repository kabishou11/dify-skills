---
name: Dify apps and workflows
description: >-
  Use this when creating or editing Dify apps, chatflows, workflows, DSL, canvas publish, variables, triggers, or the code-node sandbox.
---
# Dify apps and workflows

Use this when creating or editing apps, the canvas, DSL, or publishing. Login: [Dify console API](sand-workflow:dify-console-api). After publish: [Dify service API](sand-workflow:dify-service-api). Failures: [Dify troubleshooting](sand-workflow:dify-troubleshooting). Trigger URLs, webhook body size, schedule poller, sandbox timeouts: [Dify compose and config](sand-workflow:dify-compose-and-config). Plugin HTTP endpoints (`/e/{hook_id}`) are not workflow triggers: [Dify workspace extras](sand-workflow:dify-workspace-extras).

Community only. Triggers are **workflow** `mode` only (not chatflow). Quota / 429 "upgrade your plan" is Cloud billing — Community `QuotaService.reserve` is a no-op.

Canvas Loop/iteration/tools caps (`LOOP_NODE_MAX_COUNT`, `MAX_ITERATIONS_NUM`, `MAX_TOOLS_NUM`) are **web** env — [Dify compose and config](sand-workflow:dify-compose-and-config). Field-tested on 1.16.1 production canvases; this tree targets **1.17**. DSL `version` is **not** the Dify software version — `GET /console/api/app-dsl-version` (1.17 exports `0.7.0`; 1.16.1 exports were often `0.1.5`). Never copy a foreign `version`.

## Create
```http
POST /console/api/apps
{"name":"发票助手","mode":"workflow","description":"optional, max 400"}
```
`mode`: `chat` | `agent-chat` | `advanced-chat` (chatflow) | `workflow` | `completion`. Agent Studio is `POST /agent`.

List `GET /apps`. Copy `POST /apps/{id}/copy`. Convert chat → workflow: `POST /apps/{id}/convert-to-workflow`.

## Code-first loop (preferred)

Generate JSON (valid YAML) → validate → import **or** sync draft → publish → draft/run every branch. Do not only click the canvas.

1. Login (Base64 password + cookie + CSRF). Tokens last ~1h (`unauthorized` → login again).
2. `GET /apps/{id}/workflows/draft` and keep `hash`.
3. **Import** `POST /apps/imports` `{"mode":"yaml-content","yaml_content":"..."}` creates a **new** app every time.
4. **Sync in place** (keep URL / API key): `POST /apps/{id}/workflows/draft` (not PATCH). 1.17 payload is `graph` + `features` + `hash` + optional `conversation_variables`. Do **not** send `environment_variables` — pydantic `extra_forbidden`. Env var edits use `environment_variable_patch: {environment_variables:[...], deleted_environment_variable_ids:[...]}`. Then `POST /apps/{id}/workflows/publish` `{}`.
5. Debug without WebApp:
   - workflow: `POST /apps/{id}/workflows/draft/run`
   - chatflow: `POST /apps/{id}/advanced-chat/workflows/draft/run` with `query` + `conversation_id`
   Parse SSE `node_finished` (`status`/`outputs`/`error`) and `workflow_finished`.

`draft_workflow_not_sync` → GET a fresh hash. Stale hash → 400.

## DSL top-level

```json
{
  "version": "<from GET /app-dsl-version>",
  "kind": "app",
  "app": {"name":"...","mode":"advanced-chat|workflow","icon":"🔧","icon_background":"#E0F2FE","description":""},
  "workflow": {
    "graph": {"nodes":[],"edges":[],"viewport":{"x":0,"y":0,"zoom":0.5}},
    "features": {},
    "environment_variables": [],
    "conversation_variables": []
  }
}
```

- `advanced-chat`: `sys.query` / `sys.files` (array) / **answer** nodes. Features: opening_statement, file_upload, retriever_resource.
- `workflow`: no `sys.query`. Files live on **start** variables (often a single `file`, not `sys.files`).
- Write JSON with `json.dump`; do not hand-edit YAML.

## Node top-level (frontend) vs data.type (engine)

| Field | Required | Missing |
|---|---|---|
| top-level `type` | `"custom"` for almost every node | canvas **React #130** (component undefined) |
| loop start | `"custom-loop-start"` 44×48 | same crash |
| iteration start | `"custom-iteration-start"` | same class of crash |
| `position` `{x,y}` | loop children are **relative to parent** | layout junk |
| `width`/`height` | loop container must cover children | children clip |
| `data.type` | `llm` / `code` / `loop` / `trigger-schedule` / `trigger-webhook` / `trigger-plugin` / … no prefix | engine invalid |
| Do **not** write | `positionAbsolute`, child `extent`, loop `outputs` | unofficial |

Loop children: `parentId=<loopId>`, `zIndex: 1002`. Edges: `type: custom`, `data: {isInIteration, isInLoop, sourceType, targetType}`. If-else / classifier `sourceHandle` is `true`/`false`/`fail-branch` or the class id — not `source`.

Selectors: `["nodeId","field"]`, `["sys","query"]`, `["env","VAR"]`, loop vars `["loopId","var"]`. Templates: `{{#nodeId.field#}}`, `{{#sys.query#}}`, `{{#env.THINK_SWITCH#}}`. Knowledge into LLM: put `{{#context#}}` in the **system** prompt (this generation does not inject context unless you write the placeholder).

## Node gotchas (1.16 field-tested, still the checklist on 1.17)

**LLM.** Must include a **user** message (`No user query found`). `vision.enabled: true` requires `configs.variable_selector` (e.g. `["sys","files"]`) + `detail`, else publish "视觉变量不能为空". Thinking models: `max_tokens` ≥ 16384 or the thought eats the budget and `text` is empty. Fast path: `/no_think` at the end of system. Strip `<think>...</think>` with a code node if the provider surfaces it. `retry_config` + `error_strategy: default-value` are default. Do not enable node `structured_output` on models that lack it — JSON schema in the prompt + code parse.

**Code.** Input field is **`value_selector`**, not `variable_selector`. There is **no** 2s `sleep` cap in 1.17 source — kill time is `SANDBOX_WORKER_TIMEOUT` (default 15s). Stdlib + optional `/dependencies`. Full recipe: [Code node and sandbox](#code-node-and-sandbox). Nested generators: build newlines with `chr(10)` to avoid escape hell. `compile(code, id, "exec")` before import.

**If-else.** Numeric operators are Unicode `≥` `≤` `≠`, not `>=`. Cases use `conditions[]` + `varType`.

**Knowledge-retrieval.** Rerank needs **four** keys: `provider` + `model` (UI) and `reranking_provider_name` + `reranking_model_name` (engine). Wrong provider → `credentials is not initialized`. Rerank `score` may be `None` — gate on chunk **count**, not score. Output is `result` (array). Dataset UUIDs are **this** tenant — remap on another box.

**Tool.** Three name systems: API tools use OpenAPI **`operationId`**; builtin plugins use identity.name; MCP uses MCP names. Mixing them → `Unknown error`. API tool output is **only** `text` (whole JSON string) — parse in code. `provider_id` for API tools is the `tool_api_providers.id` UUID (remap on another box). Builtin `provider_type: builtin` uses a name, not a UUID.

**HTTP request.** Always send `authorization: {"type":"no-auth","config":null}` even when unused. Timeouts are three ints (connect/read/write). Body `data` is a **string** with `{{#...#}}` templates. Intranet hosts: [Dify intranet](sand-workflow:dify-intranet) (`NO_PROXY` / SSRF).

**Loop.** Official pattern: inject via `loop_variables` → children read `[loopId, var]` → in-loop `assigner` v2 writes back → `break_conditions` reference **loop vars**, not child outputs (publish "无效的变量"). Each break condition needs `id` + `varType`. No `outputs` on the loop node. Sleep inside a loop is still sandbox-bounded (`SANDBOX_WORKER_TIMEOUT`), not a 2s hard cap.

**List-operator.** Output field is `result`. Set `var_type` / `item_var_type`. Workflow start `file` is often a **single** file, not `sys.files`.

**Variable-aggregator.** Merges branches without failing the unused side. Output commonly `output`.

**Document-extractor.** Reads text PDFs / Office, not scans or photos. Empty extract → `error_strategy: default-value` with empty `text`. If the product also needs OCR, publish a **separate** app for the OCR loop — do not hang MinerU/tool nodes on the text-PDF graph behind an if-else (`length ≥ N` → extractor, else OCR). That still ships OCR on the canvas and callers will hit it. Text-PDF start `file` should use `allowed_file_types: ["document"]` only; including `image` invites scans the extractor cannot read.

**Question-classifier.** Must have a `fail-branch` edge. `sourceHandle` = class id. Keep temperature low.

**Answer (chatflow).** Template may include `{{#nodeId.field#}}`. Empty leftover placeholders show in the WebApp.

**Assigner.** `version: "2"`, `operation: over-write`, `loop_id` set when inside a loop.

Prefer **serial** over join-heavy graphs: multiple inbound edges can stall as a join. Typical bug: `document-extractor` edges **both** into the LLM and into a cleaner/gate that also feeds the same LLM — the engine waits for every inbound edge, including the unused OCR branch. One chain: extractor → clean → LLM. Put `retry_config` + `error_strategy` on LLM/tool/HTTP.

**Published vs draft.** `/v1` and product backends run the **published** graph. Canvas-only surgery does not change the demo. After a graph fix: draft/run → publish.

**Prompt wording.** Do not write “OCR后的正文” in a non-OCR workflow. It confuses operators into adding OCR nodes.

## Bindings when moving DSL between instances

Remap before import: `dataset_ids`, API-tool `provider_id`, model **display** `name` (Dify entry, not the vLLM `served-model-name`). Same volume restore → UUIDs stay, do not rewrite. After remap, re-check the four rerank fields and tool `operationId`. Trigger `subscription_id` / plugin `provider_id` are **this** tenant — rebuild the plugin subscription, do not copy foreign IDs.

## Canvas collaboration (editor stuck on "同步数据中")

1.16+ uses **Socket.IO** (`/socket.io/?EIO=4&transport=websocket`), not `/api/ws`. nginx must proxy `/socket.io/` to `api_websocket` with Upgrade headers. `NEXT_PUBLIC_SOCKET_URL` must be a host the **browser** can reach (not `ws://localhost` for remote users). After recreating api/web, `nginx -s reload` (cached upstream IPs → 502).

## Logs / annotations / human input

Conversation logs, workflow-app-logs, node traces (`triggered_from=app-run`), statistics, annotations: [Dify workspace extras](sand-workflow:dify-workspace-extras). Do not duplicate those HTTP here.

Site: `POST /apps/{id}/site-enable`. MCP: `POST /apps/{id}/server`.

## Triggers (workflow only)

`data.type` is one of `trigger-schedule` | `trigger-webhook` | `trigger-plugin`. They are **start** nodes. Publish rejects a graph that also has a `start` node (`Start node and trigger nodes cannot coexist in the same workflow`). Chatflow handlers no-op — do not put triggers on `advanced-chat`.

Caps from source: **<=5** webhook nodes and **<=5** plugin-trigger nodes per workflow. Schedule sync takes the **first** `trigger-schedule` node only (one `workflow_schedule_plans` row per app).

### Lifecycle

| Moment | What happens |
|---|---|
| Draft save `POST /apps/{id}/workflows/draft` | Syncs `workflow_webhook_triggers` and `workflow_plugin_triggers` (creates 24-char `webhook_id` if missing). Schedule plan is **not** written yet. |
| Publish `POST /apps/{id}/workflows/publish` | Writes `app_triggers` (`status: enabled`) and `workflow_schedule_plans` (cron + timezone + `next_run_at`). Removing a trigger node on the next publish deletes the `app_triggers` row / schedule plan. |
| Enable / disable | `POST /console/api/apps/{id}/trigger-enable` — production webhook/schedule/plugin skip when `disabled`. Debug webhook ignores this flag. |

```http
GET  /console/api/apps/{id}/triggers
POST /console/api/apps/{id}/trigger-enable
{"trigger_id":"<app_triggers.id>","enable_trigger":true}
```

List item: `id`, `trigger_type` (`trigger-webhook` / `trigger-schedule` / `trigger-plugin`), `title`, `node_id`, `provider_name`, `icon`, `status` (`enabled` | `disabled` | `unauthorized` | `rate_limited`). Plugin icons: `/console/api/workspaces/current/tool-provider/builtin/{provider_name}/icon`.

### Public URLs — TRIGGER_URL vs ENDPOINT_URL_TEMPLATE

Set both on api/worker (`.env` / `shared.env`). Recreate **api + worker**. Callers must reach the **nginx** host, not the container name.

| Knob | Default (example) | Used for |
|---|---|---|
| `TRIGGER_URL` | `http://localhost` | Workflow triggers. Concatenated as `{TRIGGER_URL}/triggers/...` |
| `ENDPOINT_URL_TEMPLATE` | `http://localhost/e/{hook_id}` | **Plugin HTTP Endpoint** instances. `{hook_id}` is replaced. nginx `/e/` -> `plugin_daemon:5002` |

Generated trigger URLs (no console prefix):

| Kind | Path | nginx |
|---|---|---|
| production webhook | `{TRIGGER_URL}/triggers/webhook/{webhook_id}` | `location /triggers` -> `api:5001` |
| debug webhook | `{TRIGGER_URL}/triggers/webhook-debug/{webhook_id}` | same |
| plugin **trigger** | `{TRIGGER_URL}/triggers/plugin/{endpoint_id}` (UUID) | same |
| plugin **Endpoint** | `ENDPOINT_URL_TEMPLATE` with `{hook_id}` -> `/e/{hook_id}` | `location /e/` -> plugin_daemon |

Do **not** mix them. `/e/{hook_id}` never runs a workflow graph. `/triggers/plugin/{uuid}` never hits plugin_daemon's endpoint router. The public path is **`/triggers/webhook/{id}`**, not `/webhook/{id}`.

Set `TRIGGER_URL` to the origin **external callers** use (scheme + host + optional port). Leave `http://localhost` only when the caller is on the same machine as nginx.

### Schedule (cron)

Node `data.type: trigger-schedule`. Default: `mode: visual`, `frequency: daily`, `timezone: UTC`, `visual_config: {time: "12:00 AM", on_minute: 0, weekdays: ["sun"], monthly_days: [1]}`.

```json
{
  "id": "sched-1",
  "type": "custom",
  "data": {
    "type": "trigger-schedule",
    "title": "Nightly",
    "mode": "cron",
    "cron_expression": "0 2 * * *",
    "timezone": "Asia/Shanghai"
  }
}
```

Visual mode (`mode: visual`) converts to 5-field cron:

| `frequency` | Required | Cron |
|---|---|---|
| `hourly` | `visual_config.on_minute` 0-59 | `{minute} * * * *` |
| `daily` | `time` 12-hour (`"2:30 PM"`) | `{minute} {hour} * * *` |
| `weekly` | `time` + `weekdays` `sun`..`sat` | `{minute} {hour} * * {dow}` (sun=0) |
| `monthly` | `time` + `monthly_days` 1-31 and/or `"last"` | `{minute} {hour} {days} * *` (`L` for last) |

Cron mode: exactly **5** fields, or a predefined `@hourly` / `@daily` / `@weekly` / `@monthly` / `@yearly`. `croniter` also accepts `L`, `?`, month/day names. Invalid -> publish `ScheduleConfigError`.

**Poller (must be up or nothing fires):** knobs in [Dify compose and config](sand-workflow:dify-compose-and-config).

1. `ENABLE_WORKFLOW_SCHEDULE_POLLER_TASK=true` (default) on api/worker/worker_beat.
2. **worker_beat** (`MODE=beat`) registers `schedule.workflow_schedule_task.poll_workflow_schedules` every `WORKFLOW_SCHEDULE_POLLER_INTERVAL` minutes (default **1**).
3. **worker** consumes queues `schedule_poller` then `schedule_executor` (Community default `-Q` already includes both).
4. Due rows: `next_run_at <= now`, matching `app_triggers` `trigger-schedule` **enabled**. Batch `WORKFLOW_SCHEDULE_POLLER_BATCH_SIZE` (100). Circuit breaker `WORKFLOW_SCHEDULE_MAX_DISPATCH_PER_TICK` (`0` = unlimited).
5. Recreate **worker_beat** after toggling the flag; recreate **worker** if you overrode `CELERY_QUEUES` and dropped `schedule_*`.

Schedule debug (canvas): `POST /apps/{id}/workflows/draft/nodes/{node_id}/trigger/run` runs immediately (no wait). Full-graph debug: `POST /apps/{id}/workflows/draft/trigger/run` `{"node_id":"..."}` — if nothing is due yet you get `{"status":"waiting","retry_in":2000}`. `POST .../draft/trigger/run-all` `{"node_ids":[...]}`.

Published run inputs are `{}`. Runs as the tenant **owner** (fallback admin).

### Webhook

Node `data.type: trigger-webhook`. After draft save:

```http
GET /console/api/apps/{id}/workflows/triggers/webhook?node_id=<nodeId>
```

Returns `id`, `webhook_id` (24 chars), `webhook_url`, `webhook_debug_url`, `node_id`.

DSL `data` (engine lowercases method):

```json
{
  "type": "trigger-webhook",
  "title": "Inbound",
  "method": "post",
  "content_type": "application/json",
  "headers": [{"name": "X-Token", "type": "string", "required": true}],
  "params": [{"name": "order_id", "type": "string", "required": false}],
  "body": [{"name": "payload", "type": "object", "required": true}],
  "status_code": 200,
  "response_body": ""
}
```

Allowed methods: `get` `post` `head` `patch` `put` `delete`. Content types: `application/json`, `multipart/form-data`, `application/x-www-form-urlencoded`, `text/plain`, `application/octet-stream`. Header types: string only. Query: string / number / boolean. Body: those plus object / arrays / file.

Caller (no cookie): GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS on `/triggers/webhook/{webhook_id}`. Must match configured method **and** Content-Type or 400 `HTTP method mismatch` / `Content-type mismatch`. Production also requires the app trigger **enabled** and a **published** workflow; otherwise 404.

Response is **async**: Dify enqueues Celery then returns `status_code` + `response_body` immediately. Empty body -> `{"status":"success","message":"Webhook processed successfully"}`. JSON-looking strings are parsed; otherwise `{"message":"..."}`.

Workflow inputs:

```json
{
  "webhook_data": {"method":"POST","headers":{},"query_params":{},"body":{},"files":{}},
  "webhook_headers": {},
  "webhook_query_params": {},
  "webhook_body": {}
}
```

Header/query keys with `-` are sanitized to `_` for variable names.

**Body size.** `WEBHOOK_REQUEST_BODY_MAX_SIZE` (bytes, default **10485760** / 10 MiB) is checked from `Content-Length` -> 413 `Webhook request too large`. Raise it **and** `NGINX_CLIENT_MAX_BODY_SIZE` (recreate nginx). Recreate **api** after the Dify knob.

**Debug URL** `/triggers/webhook-debug/{id}`: uses the **draft** graph, skips enabled check, does **not** enqueue production. Needs an active Variable Inspector listener; otherwise **409** `No active debug listener` (body includes `execution_url` of the production webhook). Canvas poller: `POST /apps/{id}/workflows/draft/trigger/run` `{"node_id":"..."}`.

### Plugin trigger (workflow) vs plugin Endpoint

**Plugin trigger** = a `trigger-plugin` start node bound to a workspace **trigger subscription**.

1. Install a trigger-capable plugin.
2. Workspace APIs (cookie + CSRF):
   - `GET /console/api/workspaces/current/triggers`
   - `GET /console/api/workspaces/current/trigger-provider/{provider}/info`
   - `POST /console/api/workspaces/current/trigger-provider/{provider}/subscriptions/builder/create` `{"credential_type":"unauthorized"|"api-key"|"oauth2"}`
   - update / verify / build / logs under `.../subscriptions/builder/...`
   - list: `GET .../trigger-provider/{provider}/subscriptions/list`
   - OAuth: `GET .../subscriptions/oauth/authorize` (callback `/console/api/oauth/plugin/{provider}/trigger/callback`)
3. Put a node with `subscription_id` (required — draft sync **skips** nodes without it):

```json
{
  "type": "trigger-plugin",
  "title": "Repo event",
  "plugin_id": "<plugin id>",
  "provider_id": "<plugin_id/provider_name>",
  "event_name": "<event>",
  "subscription_id": "<subscription uuid>",
  "plugin_unique_identifier": "<plugin unique identifier>",
  "event_parameters": {
    "repo": {"type": "constant", "value": "org/name"}
  }
}
```

`event_parameters` values must be `type: "constant"` (engine rejects `variable` / `mixed`). Third party posts to `{TRIGGER_URL}/triggers/plugin/{endpoint_id}`. Dify dispatches matching events onto published workflows with that `subscription_id`.

**Plugin Endpoint** = HTTP hook implemented **inside the plugin**, not a workflow start node. Details: [Dify workspace extras](sand-workflow:dify-workspace-extras).

```http
POST /console/api/workspaces/current/endpoints
{"plugin_unique_identifier":"...","name":"my-hook","settings":{}}
POST /console/api/workspaces/current/endpoints/enable
{"endpoint_id":"..."}
POST /console/api/workspaces/current/endpoints/disable
{"endpoint_id":"..."}
```

Public URL from `ENDPOINT_URL_TEMPLATE` (`/e/{hook_id}`). Enable/disable here does **not** toggle `app_triggers`.

### Typical trigger errors

| Symptom | Cause |
|---|---|
| publish `Start node and trigger nodes cannot coexist` | Graph has both `start` and a trigger type |
| webhook 404 | unknown id, unpublished, or `enable_trigger: false` |
| webhook 400 method / content-type | caller != node `method` / `content_type` |
| webhook 413 | body > `WEBHOOK_REQUEST_BODY_MAX_SIZE` or nginx 413 |
| webhook-debug 409 | Variable Inspector not listening |
| schedule never fires | `worker_beat` down, flag false, trigger disabled, or worker missing `schedule_poller`/`schedule_executor` |
| plugin trigger silent | node missing `subscription_id`, or `TRIGGER_URL` not the origin the vendor can reach |
| 429 upgrade plan | Cloud quota — ignore on Community |

## Code node and sandbox

`data.type: code`. Inputs are `variables[].value_selector` (array path), **not** `variable_selector`.

```json
{
  "id": "code",
  "type": "custom",
  "data": {
    "type": "code",
    "title": "Sum",
    "code_language": "python3",
    "variables": [
      {"variable": "args1", "value_selector": ["start", "a"]},
      {"variable": "args2", "value_selector": ["start", "b"]}
    ],
    "outputs": {"result": {"type": "number", "children": null}},
    "code": "def main(args1, args2):\n    return {\"result\": args1 + args2}\n"
  }
}
```

`code_language`: `python3` (sandbox `python3`), `javascript` (sandbox `nodejs`). Jinja2 template-transform also hits the sandbox as python3. Entry is `def main(**inputs)` and **must** return a dict whose keys match `outputs`.

### Timeouts — not "sleep <= 2s"

1.17 has **no** 2-second sleep limit in api/sandbox config. Real knobs ([Dify compose and config](sand-workflow:dify-compose-and-config)):

| Knob | Default | Where | Meaning |
|---|---|---|---|
| `SANDBOX_WORKER_TIMEOUT` | 15 | sandbox env `WORKER_TIMEOUT` | Process kill inside `langgenius/dify-sandbox`. Recreate **sandbox**. |
| `volumes/sandbox/conf/config.yaml` `worker_timeout` | 5 in the checked-in file | sandbox yaml | Same layer; set **both** this and the env if a short kill persists. |
| `CODE_EXECUTION_CONNECT_TIMEOUT` | 10 | api+worker | HTTP connect to `CODE_EXECUTION_ENDPOINT` |
| `CODE_EXECUTION_READ_TIMEOUT` | 60 | api+worker | HTTP read from sandbox |
| `CODE_EXECUTION_WRITE_TIMEOUT` | 10 | api+worker | HTTP write |
| `CODE_EXECUTION_ENDPOINT` | `http://sandbox:8194` | api+worker | Must reach sandbox:8194 |
| `CODE_EXECUTION_API_KEY` | `dify-sandbox` | api+worker | Must **equal** sandbox `SANDBOX_API_KEY` / `API_KEY` |

If `sleep(20)` with `SANDBOX_WORKER_TIMEOUT=15`, the sandbox kills the worker even though the API is still waiting up to 60s. Raise sandbox timeout first, then `CODE_EXECUTION_READ_TIMEOUT` so it stays larger. Recreate **sandbox + api + worker**.

### Stdlib allowlist and `/dependencies`

Sandbox image `langgenius/dify-sandbox:0.2.15`. Compose mounts:

- `volumes/sandbox/conf` -> `/conf`
- `volumes/sandbox/dependencies` -> `/dependencies`

Filesystem allowlist is `python_lib_path` in `volumes/sandbox/conf/config.yaml.example` (checked-in `config.yaml` omits the list and uses image defaults):

- `/usr/local/lib/python3.10`, `/usr/lib/python3.10`, `/usr/lib/python3`, `/usr/lib/x86_64-linux-gnu`
- certs / nsswitch / hosts / resolv / localtime / zoneinfo / timezone

That is a **bind-mount** allowlist (CPython stdlib + resolver/tz), not a Python `sys.modules` whitelist. Extra pip packages belong in the `/dependencies` volume; recreate **sandbox** after adding them. Dify 1.17 source does not name the requirements filename.

Output size caps (api, after stdout parse): `CODE_MAX_STRING_LENGTH` 400000, `CODE_MAX_DEPTH` 5, `CODE_MAX_STRING_ARRAY_LENGTH` 30, `CODE_MAX_OBJECT_ARRAY_LENGTH` 30, `CODE_MAX_NUMBER_ARRAY_LENGTH` 1000, `CODE_MAX_PRECISION` 20.

### Network via SSRF

`CodeExecutor` always sends `"enable_network": true`. Sandbox `SANDBOX_ENABLE_NETWORK` default true. Egress is forced through `SANDBOX_HTTP_PROXY` / `SANDBOX_HTTPS_PROXY` -> `http://ssrf_proxy:3128`.

Private/internal URLs need `SSRF_PROXY_ALLOW_PRIVATE_IPS` (CIDR list) and matching `NO_PROXY` on api/worker — [Dify intranet](sand-workflow:dify-intranet). Recreate **ssrf_proxy** (+ sandbox). This is **not** the HTTP Request node path; same proxy, different client.

### Typical code-node errors

| Message | Fix |
|---|---|
| `Failed to execute code ... check if the sandbox service is running` | sandbox down, wrong `CODE_EXECUTION_ENDPOINT`, or API key mismatch |
| `Code execution service is unavailable` | sandbox 503 (workers busy / timeout storm) |
| `Got error code: ... Got error msg: ...` | sandbox rejected the run (import outside allowlist, seccomp, syntax) |
| traceback in `node_finished.error` with `sleep` / killed | hit `SANDBOX_WORKER_TIMEOUT` |
| `Output result must be a string, got int instead` | `outputs` type != returned value |
| `Depth limit 5 reached, object too deep` | raise `CODE_MAX_DEPTH` or flatten |
| publish/import OK but runtime empty | `value_selector` empty or wrong node id (frontend requires a non-empty selector) |

## Publish checklist

1. Every node has top-level `type`.
2. Vision configs / rerank four fields / classifier fail-branch / loop break `id`+`varType`.
3. `compile` every code node; edges reference existing ids.
4. Draft run **every** branch (intent / tool fail / empty retrieve / file / HTTP timeout).
5. Publish → `api-enable` / `site-enable`. Start variables match caller `inputs`.
6. Trigger graphs: no `start` node; webhook `GET .../triggers/webhook?node_id=` has a URL; schedule has `worker_beat` + poller flag; plugin node has `subscription_id`.
7. `TRIGGER_URL` is the origin callers actually hit. `ENDPOINT_URL_TEMPLATE` is only for `/e/{hook_id}` plugin Endpoints.
