---
name: Dify apps and workflows
description: >-
  Use this when creating or editing Dify apps, chatflows, workflows, DSL, canvas
  publish, variables, or triggers.
---
# Dify apps and workflows

Use this when creating or editing apps, the canvas, DSL, or publishing. Login: [Dify console API](sand-workflow:dify-console-api). After publish: [Dify service API](sand-workflow:dify-service-api). Private network: [Dify intranet](sand-workflow:dify-intranet). Human-input / annotations / snippets: [Dify workspace extras](sand-workflow:dify-workspace-extras).

## Create
```http
POST /console/api/apps
{"name":"发票助手","mode":"workflow","description":"optional, max 400"}
```

`mode`: `chat` | `agent-chat` | `advanced-chat` (chatflow) | `workflow` | `completion`.

List `GET /apps?page=1&limit=20&mode=all`. Recent/starred: `/apps/recent`, `/apps/starred`, `POST /apps/{id}/star`. Get/update/delete `/apps/{id}`. Copy `POST /apps/{id}/copy`. Rename/icon: `POST /apps/{id}/name`, `.../icon`. Convert chat → workflow: `POST /apps/{id}/convert-to-workflow`.

Agent Studio is `POST /agent`, not this list.

## Canvas
Always **GET draft → mutate graph → POST draft → publish**. Never invent colliding node ids.

`POST /apps/{id}/workflows/draft` body:

- `graph` — nodes, edges, viewport
- `features` — file upload, speech, etc.
- `hash` — send back the hash from GET; omit/mismatch can 400 on concurrent edits
- `conversation_variables` — chatflow only, optional
- `environment_variable_patch` — env vars

Also:

- Publish: `POST /apps/{id}/workflows/publish` (GET lists published versions)
- Restore: `POST /apps/{id}/workflows/{workflow_id}/restore`, `PATCH .../workflows/{workflow_id}`
- Run workflow: `POST /apps/{id}/workflows/draft/run` with `inputs` (+ optional `files`)
- Run chatflow: `POST /apps/{id}/advanced-chat/workflows/draft/run` with `query` + `conversation_id`
- One node: `POST /apps/{id}/workflows/draft/nodes/{node_id}/run` (iteration/loop variants exist)
- Last run: `GET .../draft/nodes/{node_id}/last-run`
- Features: `GET/POST /apps/{id}/workflows/draft/features`
- Vars: `.../environment-variables`, `conversation-variables`, `system-variables`, plus `/workflows/draft/variables`
- Stop: `POST /apps/{id}/workflow-runs/tasks/{task_id}/stop`
- Runs: `GET /apps/{id}/workflow-runs` (+ `/{run_id}`, `node-executions`, export). Chatflow: `/apps/{id}/advanced-chat/workflow-runs`
- Node outputs inspector: `/apps/{id}/workflows/draft/runs/{run_id}/node-outputs`
- Block configs: `GET .../default-workflow-block-configs`
- Presence: `POST /apps/workflows/online-users`
- Comments: `/apps/{id}/workflow/comments`

## Human input
`POST /apps/{id}/workflows/draft/human-input/nodes/{node_id}/form/preview` and `/form/run`, `/delivery-test`. Chatflow paths sit under `advanced-chat/`. Token + events live in workspace extras.

## Built-in nodes (intranet first)
LLM, Knowledge retrieval, Agent, HTTP Request, Code, If/Else, Iteration, Loop, Template, Variable aggregator, Doc extractor, List operator, Question classifier, Human input, Answer.

HTTP to `10.`/`172.` needs `SSRF_PROXY_ALLOW_PRIVATE_IPS`. Code runs in sandbox (no plugin).

## Triggers / webhooks
List `GET /workspaces/current/triggers`. Provider info `GET /workspaces/current/trigger-provider/{provider}/info`. Subscriptions under `.../subscriptions/list`. App: `GET /apps/{id}/triggers`, `POST /apps/{id}/trigger-enable`, webhook urls `GET /apps/{id}/workflows/triggers/webhook`. Callbacks use `TRIGGER_URL` (must be reachable by the external system). Public: `/webhook/{id}`, `/webhook-debug/{id}`. Draft trigger test: `POST /apps/{id}/workflows/draft/trigger/run` (+ `/run-all`, per-node).

## DSL
Export `GET /apps/{id}/export`. Import `POST /apps/imports` then `.../imports/{id}/confirm`. Check plugins `GET /apps/imports/{app_id}/check-dependencies` then install (plugin install skill).

## Basic chat
`POST /apps/{id}/model-config`. Canvas apps mostly ignore this. Prompt templates: `GET /app/prompt-templates`. Site: `GET/POST /apps/{id}/site`, `POST .../site-enable`, `POST .../api-enable`. Trace: `GET /apps/{id}/trace`, `GET /apps/{id}/trace-config`. Audio: `POST /apps/{id}/audio-to-text`, `text-to-audio`.

Debug chat from console: `POST /apps/{id}/chat-messages` (or `/completion-messages`). Conversations: `/apps/{id}/chat-conversations`. Feedbacks: `POST /apps/{id}/feedbacks`, export `GET .../feedbacks/export`.

## Annotations / stats
Annotations: `GET /apps/{id}/annotations` (export, batch-import, annotation-reply, hit-histories) — workspace extras. Stats: `/apps/{id}/statistics/daily-messages` (conversations, end-users, token-costs, satisfaction, response-time, tokens-per-second). Workflow stats under `/apps/{id}/workflow/statistics/*`. Logs: `/apps/{id}/workflow-app-logs`, archived `/workflow-archived-logs`.

## Publish checklist
Draft node run → full run → publish → `api-enable` / `site-enable` → start vars match caller `inputs`. Optional: MCP `POST /apps/{id}/server`.
