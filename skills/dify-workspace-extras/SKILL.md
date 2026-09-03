---
name: Dify workspace extras
description: >-
  Use this when operating Dify 1.17 workspace Skills, snippets, Agent roster,
  RAG pipelines, MCP servers, plugin endpoints, members, tags, annotations,
  workflow/conversation logs, statistics, or human-input forms.
---
# Dify workspace extras (1.17)

Use this for Console surfaces that are not the core app canvas, plugins, or dataset upload. Prefix `/console/api`. Cookie + `X-CSRF-Token` from [Dify console API](sand-workflow:dify-console-api). Route index: [Dify API catalog](sand-workflow:dify-api-catalog).

These are **Dify workspace** Skills / Agents, not this repository's operating skills.

**1.17.0 caution.** Workspace Skill **zip/blob upload**, FastMCP OAuth, and Agent Studio tool calling have open upstream bugs. Keep the HTTP map below for when they work; do not build a customer demo on them until a patch release. Classic `mode: workflow` + `/v1` is the stable path.

Community: `/workspaces/current/rbac/*` and `/billing/*` 403 or empty. RAG pipeline **publish** is gated by `knowledge_pipeline.publish_enabled` (403 if off). Agent Studio still works as community APIs unless a handler is wrapped with a license gate.

## Workspace Skills (Agent Skill files)

List: `GET /workspaces/current/skills?keyword=&page=1&limit=20` (repeat `tag=`). Tags: `GET .../skills/tags`.

Create:

```http
POST /workspaces/current/skills
{"name":"invoice-parse","display_name":"发票解析","icon":"📄","description":"...","tags":[]}
```

Then edit draft files, then publish.

| Action | Route |
|---|---|
| Get / patch metadata / delete | `GET/PATCH/DELETE /workspaces/current/skills/{id}` |
| Duplicate | `POST .../skills/{id}/duplicate` |
| Export | `GET .../skills/{id}/export` |
| Import zip | `POST .../skills/import` (multipart file) |
| Upload blob | `POST .../skills/files/upload` |
| Check paths | `POST .../skills/{id}/files/check` |
| Patch / replace tree | `PATCH` / `PUT .../skills/{id}/files` |
| Preview / content | `GET .../skills/{id}/files/preview` and `.../content?path=` |
| Publish | `POST .../skills/{id}/publish` `{"publish_note":"","version_name":null}` |
| Restore | `POST .../skills/{id}/restore` `{"version_id":"..."}` |
| Versions | `GET .../skills/{id}/versions` (+ `/{version_id}` PATCH note) |
| References | `GET .../skills/{id}/references` |
| Assist | `POST .../skills/{id}/assist/messages` |

Delete of a referenced skill needs `{"confirmation_name":"<display_name>"}`.

Bind to Agent Studio agent (ordered ids):

```http
PUT /workspaces/current/agents/{agent_id}/skills
{"skill_ids":["skill-uuid-1","skill-uuid-2"]}
GET  /workspaces/current/agents/{agent_id}/skills
```

Inspect files already on an agent/app: `/agent/{id}/config/skills` and `/apps/{id}/agent/config/skills` (upload / inspect / download / delete). That is the **bound copy**, not the workspace library.

## Agent roster (Agent Studio)

This is **not** `mode: agent-chat`. Roster agents live under `/agent`. They do **not** appear in `GET /apps` — an empty or shorter app list is not data loss.

```http
POST /agent
{"name":"客服","description":"optional, max 400","role":"optional"}
GET  /agent
GET  /agent/{id}
```

Draft: `GET/POST /agent/{id}/build-draft`, `POST .../build-draft/checkout`, `POST .../build-draft/apply`. Composer: `GET /agent/{id}/composer`, `POST .../composer/validate`, `GET .../composer/candidates`. Copy a roster agent into a workflow Agent node: `POST /apps/{app_id}/workflows/draft/nodes/{node_id}/agent-composer/copy-from-roster` (same under `/snippets/{id}/...`).

Publish: `POST /agent/{id}/publish`. Versions: `GET .../versions`, restore `POST .../versions/{vid}/restore`. Copy: `POST .../copy`. Debug chat, logs, sandbox: procedures below.

API: `POST /agent/{id}/api-enable` `{"enable_api":true}`, then `POST /agent/{id}/api-keys`. `GET .../api-access` returns chat/stop/files URLs (streaming-only). Callers still use [Dify service API](sand-workflow:dify-service-api) `/v1/chat-messages`.

Features: `/agent/{id}/features`. Workflows that reference this agent: `GET /agent/{id}/referencing-workflows`.

## Snippets (reusable subgraphs)

List/CRUD: `/workspaces/current/customized-snippets`. Create body: `name`, `type` (`node`|`group`), optional `graph`, `input_fields`, `icon_info`.

Draft canvas is **not** `/apps/{id}/...`. It is `/snippets/{id}/workflows/draft` (GET/POST, same hash rule as apps). Run node / run all / stop / variables / publish / restore mirror the app workflow routes under `/snippets/{id}/...`. Agent-composer routes exist here too.

Import DSL: `POST .../customized-snippets/imports` then `.../imports/{id}/confirm`. Export: `GET .../{id}/export`. Use-count: `POST .../{id}/use-count/increment`. Check plugins: `GET .../{id}/check-dependencies`.

## RAG pipeline

Separate from a normal dataset. Create from DSL: `POST /rag/pipeline/dataset` `{"yaml_content":"..."}`. Empty: `POST /rag/pipeline/empty-dataset`. Templates: `GET /rag/pipeline/templates?type=built-in|customized`.

Draft/publish/run: `/rag/pipelines/{pipeline_id}/workflows/draft` (same GET → mutate → POST → publish loop as apps). Datasource node run: `.../draft/datasource/nodes/{node_id}/run` and `.../published/...`. Transform an existing dataset: `POST /rag/pipelines/transform/datasets/{dataset_id}`.

Datasource plugin auth: `/auth/plugin/datasource/*` and `/oauth/plugin/{provider}/datasource/*`. List plugins: `GET /rag/pipelines/datasource-plugins`, `GET /rag/pipelines/recommended-plugins`.

Publish customized template: `POST /rag/pipelines/{id}/customized/publish` (403 if `knowledge_pipeline.publish_enabled` is false). Import/export: `/rag/pipelines/imports`, `.../exports`.

Document pipeline log on a normal dataset: `GET /datasets/{id}/documents/{doc_id}/pipeline-execution-log`.

## MCP (app as MCP server)

```http
GET  /apps/{app_id}/server
POST /apps/{app_id}/server
{"parameters":{...},"description":"optional"}
PUT  /apps/{app_id}/server
{"id":"...","parameters":{...},"status":"active"}
POST /apps/{app_id}/server/refresh
```

Clients: `POST /mcp/server/{server_code}/mcp`. Refresh rotates `server_code` — old clients break.

## Plugin HTTP endpoints

Create: `POST /workspaces/current/endpoints` or legacy `.../endpoints/create` with `plugin_unique_identifier`, `name`, `settings`. List: `GET .../endpoints/list?page=&page_size=`, `GET .../endpoints/list/plugin?plugin_id=`. Enable/disable: `POST .../endpoints/enable` and `.../disable`. Public traffic: `/plugin/{endpoint_id}` (not under `/console/api`).

## Members, account, tags

Members: `GET /workspaces/current/members`. Invite: `POST .../members/invite-email` `{"emails":["<addr>"],"role":"editor"}`. Role: `PUT .../members/{id}/update-role`. Remove: `DELETE .../members/{id}`. Owner transfer: send-confirm-email → check → `.../members/{id}/owner-transfer`.

Account: `GET/PATCH /account/profile`, `POST /account/password`, language/theme/timezone. Workspaces: `GET /workspaces`, `POST /workspaces/switch`.

Tags: `GET/POST /tags`, `PATCH /tags/{id}`, `POST /tag-bindings`, `POST /tag-bindings/remove`. Bind apps or datasets; type is in the body.

## Logs, traces, statistics

Three surfaces. Dates `YYYY-MM-DD HH:MM` are the **account timezone**. Debugger traffic is excluded from statistics.

### Conversation logs (chat / agent-chat / chatflow)

```http
GET /apps/{id}/chat-conversations?keyword=&start=2026-08-01 00:00&end=2026-08-27 23:59&annotation_status=all&sort_by=-updated_at&page=1&limit=20
GET /apps/{id}/chat-conversations/{conversation_id}
GET /apps/{id}/chat-messages?conversation_id={conversation_id}&limit=20
DELETE /apps/{id}/chat-conversations/{conversation_id}
```

`annotation_status`: `annotated` | `not_annotated` | `all`. `sort_by`: `created_at` | `-created_at` | `updated_at` | `-updated_at`. Chatflow hides `invoke_from=debugger` rows. Completion apps: `/completion-conversations` (same filters, no `sort_by`).

```http
POST /apps/{id}/feedbacks
{"message_id":"<uuid>","rating":"like","content":""}
GET  /apps/{id}/feedbacks/export?format=csv
```

`rating`: `like` | `dislike` | `null` (revoke). Classic agent-chat thought trace: `GET /apps/{id}/agent/logs?conversation_id=&message_id=` (`mode=agent-chat` only).

### Workflow logs (`mode=workflow`)

Production log list (not the canvas debugger):

```http
GET /apps/{id}/workflow-app-logs?keyword=&status=failed&created_at__after=2026-08-01T00:00:00Z&created_at__before=2026-08-27T23:59:59Z&detail=true&page=1&limit=20
```

`status`: `succeeded` | `failed` | `stopped` | `partial-succeeded`. Optional `created_by_end_user_session_id`, `created_by_account`. `detail=true` includes run payload. Page 1–99999, limit 1–100. Response `{page,limit,total,has_more,data[{id,workflow_run:{id,status,error,elapsed_time,total_tokens,total_steps,triggered_from},details,...}]}`. Archived rows: `GET /apps/{id}/workflow-archived-logs` (page/limit).

Service API (app key): `GET /v1/workflows/logs` — same keyword/status/created_at__* filters, no `detail`. [Dify service API](sand-workflow:dify-service-api).

### Node traces

Default `triggered_from` is **`debugging`**. Production WebApp/API runs need `triggered_from=app-run`.

```http
GET /apps/{id}/workflow-runs?limit=20&status=failed&triggered_from=app-run
GET /apps/{id}/workflow-runs/count?status=failed&time_range=7d&triggered_from=app-run
GET /apps/{id}/workflow-runs/{run_id}
GET /apps/{id}/workflow-runs/{run_id}/node-executions
```

Chatflow debugger: `GET /apps/{id}/advanced-chat/workflow-runs` (+ `/count`). `status`: `running` | `succeeded` | `failed` | `stopped` | `partial-succeeded`. `time_range`: `7d` | `4h` | `30m` | `30s`. Pagination: `last_id`. Paused human-input: `GET /workflow/{workflow_run_id}/pause-details`. Archived-run export: `GET /apps/{id}/workflow-runs/{run_id}/export` → `presigned_url` (404 `archive_log_not_found` if never archived).

### Statistics

`?start=YYYY-MM-DD HH:MM&end=YYYY-MM-DD HH:MM`.

Chat / completion — `GET /apps/{id}/statistics/`:
- `daily-messages` `{date,message_count}`
- `daily-conversations` `{date,conversation_count}`
- `daily-end-users` `{date,terminal_count}`
- `token-costs` `{date,token_count,total_price,currency}`
- `average-session-interactions` (chat modes)
- `user-satisfaction-rate` (likes / messages × 1000)
- `average-response-time` (**completion** only, ms)
- `tokens-per-second`

Workflow — `GET /apps/{id}/workflow/statistics/`:
- `daily-conversations` (daily **runs**)
- `daily-terminals`
- `token-costs`
- `average-app-interactions` (`mode=workflow` only)

Agent Studio: `GET /agent/{id}/statistics/summary?start=&end=&source=`. Workspace monthly archives `GET /workflow-run-archives` are cloud-paid (community 403).

### Retention

Beat task `clean_workflow_runlogs_precise` at 02:00 (worker_beat TZ, usually UTC) when `WORKFLOW_LOG_CLEANUP_ENABLED=true`. Cascades messages/annotations/thoughts for expired runs. Knobs: [Dify compose and config](sand-workflow:dify-compose-and-config). Empty list → cleanup already ran, **or** you queried `triggered_from=debugging` for production runs.

## Agent Studio runtime (debug + sandbox)

Debug chat is **SSE only** (`blocking` → 400):

```http
POST /agent/{id}/chat-messages
{"query":"你好","inputs":{},"response_mode":"streaming","conversation_id":null,"draft_type":"draft"}
```

`draft_type`: `draft` | `debug_build`. Stop: `POST /agent/{id}/chat-messages/{task_id}/stop`. History: `GET /agent/{id}/chat-messages?conversation_id=&limit=20`. Refresh debug thread: `POST .../debug-conversation/refresh`.

```http
GET /agent/{id}/logs?keyword=&page=1&limit=20&sort_by=updated_at&sort_order=desc&start=&end=
GET /agent/{id}/logs/{conversation_id}/messages
GET /agent/{id}/log-sources
```

Repeat `statuses=` (`success`|`failed`|`paused`) and `sources=` (`webapp:<app_id>` or `workflow:<app_id>`).

Sandbox caller is a conversation or a build draft:

```http
GET  /agent/{id}/sandbox?caller_type=conversation&caller_id=<conversation_id>
GET  /agent/{id}/sandbox/files?caller_type=conversation&caller_id=<id>&path=.
GET  /agent/{id}/sandbox/files/read?caller_type=conversation&caller_id=<id>&path=out.txt
POST /agent/{id}/sandbox/files/download
{"caller_type":"conversation","caller_id":"<id>","path":"out.txt"}
```

Workflow Agent node after a run: `GET /apps/{app_id}/workflow-runs/{run_id}/agent-nodes/{node_id}/sandbox/files?node_execution_id=&path=.` (+ `/read`; POST `/download` `{"node_execution_id":"...","path":"..."}`). 502 `agent_backend_unreachable` if the agent backend is down.

## Annotations (chat apps)

```http
GET  /apps/{id}/annotations?page=1&limit=20&keyword=
POST /apps/{id}/annotations
{"question":"发票抬头怎么填","answer":"用公司全称"}
```

Also `message_id` to annotate an existing message. Update: `POST /apps/{id}/annotations/{annotation_id}` `{"question":"...","answer":"..."}`. Delete one: `DELETE .../annotations/{annotation_id}`. Batch: `DELETE .../annotations?annotation_id=uuid1&annotation_id=uuid2`. Clear all: `DELETE .../annotations` with no ids.

```http
POST /apps/{id}/annotation-reply/enable
{"score_threshold":0.9,"embedding_provider_name":"<provider>","embedding_model_name":"<display-name>"}
GET  /apps/{id}/annotation-reply/enable/status/{job_id}
```

Disable: `POST .../annotation-reply/disable` (same body required). Settings: `GET /apps/{id}/annotation-setting`. Threshold: `POST .../annotation-settings/{setting_id}` `{"score_threshold":0.9}`. Export: `GET .../annotations/export`. Import CSV: `POST .../annotations/batch-import` (multipart `file`; poll `.../batch-import-status/{job_id}`; 413 if over `ANNOTATION_IMPORT_FILE_SIZE_LIMIT`). Hits: `GET .../annotations/{id}/hit-histories?page=1&limit=20`. Count: `GET .../annotations/count`. Service API: `/v1/apps/annotations*`.

## Human input, generators, explore

Human input: canvas `POST /apps/{id}/workflows/draft/human-input/nodes/{node_id}/form/preview` (and `/form/run`, `/delivery-test`; chatflow uses `advanced-chat/...`). Token form: `GET/POST /form/human_input/{form_token}`. Live events: `GET /workflow/{workflow_run_id}/events`. Service/WebApp have the same form path under `/v1` and `/api`.

Generators (LLM-assisted studio): `POST /rule-generate`, `/rule-code-generate`, `/rule-structured-output-generate`, `/instruction-generate`, `/workflow-generate` (+ `/suggestions`, `/stream`).

Explore (installed templates in this workspace): `GET /installed-apps`, `GET /explore/apps`. Chat those with `/installed-apps/{id}/chat-messages` (console session, not the service key).

## Failure patterns

- 403 on `/rag/pipelines/.../publish` or `/billing` or `/rbac` → community / feature flag, not a CSRF bug.
- 404 on `/agent` vs `/apps?mode=agent-chat` → two products; roster is `/agent`.
- Skill bind empty in composer → skill not **published**, or `PUT .../agents/{id}/skills` not called.
- MCP client 404 → `server/refresh` rotated the code, or site/API not enabled.
- Snippet draft 400 hash → GET draft again; same as app canvas.
- Empty workflow logs → `triggered_from` default is `debugging`; production needs `app-run`. Or cleanup already ran.
- Workflow-app-logs 400 on a chat app → that route is `mode=workflow` only; use chat-conversations.
- Agent debug `blocking` 400 → streaming only.
- Sandbox 502 `agent_backend_unreachable` → agent backend down, not CSRF.
- Annotation enable job `error` → embedding provider missing / `credentials is not initialized`.
