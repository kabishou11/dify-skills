---
name: Dify workspace extras
description: >-
  Use this when operating Dify 1.17 workspace Skills, snippets, Agent roster,
  RAG pipelines, MCP servers, plugin endpoints, members, tags, annotations, or
  human-input forms.
---
# Dify workspace extras (1.17)

Use this for Console surfaces that are not the core app canvas, plugins, or dataset upload. Prefix `/console/api`. Cookie + `X-CSRF-Token` from [Dify console API](sand-workflow:dify-console-api). Route index: [Dify API catalog](sand-workflow:dify-api-catalog).

These are **Dify** Skills / Agents, not Cursor skills.

Community: `/workspaces/current/rbac/*` and `/billing/*` 403 or empty. RAG pipeline **publish** is gated by `knowledge_pipeline.publish_enabled` (403 if off). Agent Studio still works as community APIs unless a handler is wrapped with `enterprise_license_required`.

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

This is **not** `mode: agent-chat`. Roster agents live under `/agent`.

```http
POST /agent
{"name":"客服","description":"optional, max 400","role":"optional"}
GET  /agent
GET  /agent/{id}
```

Draft: `GET/POST /agent/{id}/build-draft`, `POST .../build-draft/checkout`, `POST .../build-draft/apply`. Composer: `GET /agent/{id}/composer`, `POST .../composer/validate`, `GET .../composer/candidates`. Copy a roster agent into a workflow Agent node: `POST /apps/{app_id}/workflows/draft/nodes/{node_id}/agent-composer/copy-from-roster` (same under `/snippets/{id}/...`).

Publish: `POST /agent/{id}/publish`. Versions: `GET .../versions`, restore `POST .../versions/{vid}/restore`. Copy: `POST .../copy`. Chat debug: `POST /agent/{id}/chat-messages` (+ stop). Refresh debug thread: `POST .../debug-conversation/refresh`.

API: `POST /agent/{id}/api-enable` `{"enable_api":true}`, then `POST /agent/{id}/api-keys`. `GET .../api-access` returns chat/stop/files URLs (streaming-only). Callers still use [Dify service API](sand-workflow:dify-service-api) `/v1/chat-messages`.

Logs: `GET /agent/{id}/logs`, `.../logs/{conversation_id}/messages`, `.../log-sources`, `.../statistics/summary`. Sandbox files: `GET /agent/{id}/sandbox/files`. Features: `/agent/{id}/features`. Workflows that reference this agent: `GET /agent/{id}/referencing-workflows`.

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

Members: `GET /workspaces/current/members`. Invite: `POST .../members/invite-email` `{"emails":["a@b.c"],"role":"editor"}`. Role: `PUT .../members/{id}/update-role`. Remove: `DELETE .../members/{id}`. Owner transfer: send-confirm-email → check → `.../members/{id}/owner-transfer`.

Account: `GET/PATCH /account/profile`, `POST /account/password`, language/theme/timezone. Workspaces: `GET /workspaces`, `POST /workspaces/switch`.

Tags: `GET/POST /tags`, `PATCH /tags/{id}`, `POST /tag-bindings`, `POST /tag-bindings/remove`. Bind apps or datasets; type is in the body.

## Annotations, human input, generators, stats, explore

Annotations (chat apps): `GET /apps/{id}/annotations`, export, batch-import, `.../annotation-reply/{action}`, hit-histories. Service API mirrors some under `/v1/apps/annotations`.

Human input: canvas `POST /apps/{id}/workflows/draft/human-input/nodes/{node_id}/form/preview` (and `/form/run`, `/delivery-test`; chatflow uses `advanced-chat/...`). Token form: `GET/POST /form/human_input/{form_token}`. Live events: `GET /workflow/{workflow_run_id}/events`. Service/WebApp have the same form path under `/v1` and `/api`.

Generators (LLM-assisted studio): `POST /rule-generate`, `/rule-code-generate`, `/rule-structured-output-generate`, `/instruction-generate`, `/workflow-generate` (+ `/suggestions`, `/stream`).

Stats: `/apps/{id}/statistics/*` and `/apps/{id}/workflow/statistics/*`. Agent: `/agent/{id}/statistics/summary`. Archives: `/workflow-run-archives`.

Explore (installed templates in this workspace): `GET /installed-apps`, `GET /explore/apps`. Chat those with `/installed-apps/{id}/chat-messages` (console session, not the service key).

## Failure patterns

- 403 on `/rag/pipelines/.../publish` or `/billing` or `/rbac` → community / feature flag, not a CSRF bug.
- 404 on `/agent` vs `/apps?mode=agent-chat` → two products; roster is `/agent`.
- Skill bind empty in composer → skill not **published**, or `PUT .../agents/{id}/skills` not called.
- MCP client 404 → `server/refresh` rotated the code, or site/API not enabled.
- Snippet draft 400 hash → GET draft again; same as app canvas.
