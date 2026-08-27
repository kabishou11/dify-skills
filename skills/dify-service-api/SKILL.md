---
name: Dify service API
description: >-
  Use this when calling published Dify apps via /v1 (chat-messages,
  workflows/run), API keys, WebApp, or file upload.
---
# Dify service API

Use this when calling a published Dify app or dataset from code: chat, workflow run, file upload, API keys, WebApp. Prefix map: [Dify API catalog](sand-workflow:dify-api-catalog). Human-input / MCP / annotations extras: [Dify workspace extras](sand-workflow:dify-workspace-extras).

## Surfaces

| Surface | Auth | Path prefix |
|---|---|---|
| Console | session cookie + `X-CSRF-Token` | `/console/api` |
| **Service (this skill)** | `Authorization: Bearer {api_key}` | `/v1` |
| WebApp | passport / site token | `/api` |
| OpenAPI / difyctl | OAuth bearer | `/openapi/v1` (off unless `OPENAPI_ENABLED` + `ENABLE_OAUTH_BEARER`) |
| MCP | `server_code` | `/mcp/server/{code}/mcp` |

Enable the app API: `POST /console/api/apps/{id}/api-enable`. Create a key: `POST /console/api/apps/{id}/api-keys`. Dataset keys: `/console/api/datasets/api-keys` or `/datasets/{id}/api-keys`. Agent Studio keys: `/console/api/agent/{id}/api-enable` + `/agent/{id}/api-keys`.

Never put the key in a skill file. Show it once to the user.

## Chat (chat / chatflow / agent-chat / studio)

```http
POST /v1/chat-messages
Authorization: Bearer APP_KEY
Content-Type: application/json

{
  "query": "你好",
  "user": "user-123",
  "response_mode": "streaming",
  "conversation_id": "",
  "inputs": {},
  "files": []
}
```

- `user` is required (end-user id you choose).
- `response_mode`: `streaming` (SSE) or `blocking`. Agent Studio keys may be **streaming-only**.
- Continue a thread by passing back `conversation_id`.
- Stop: `POST /v1/chat-messages/{task_id}/stop`
- History: `GET /v1/messages?conversation_id=`
- Conversations: `GET/DELETE /v1/conversations`, rename `POST .../name`, variables `GET/PATCH /v1/conversations/{id}/variables`
- Feedback: `POST /v1/messages/{id}/feedbacks`, list `GET /v1/app/feedbacks`
- Suggested: `GET /v1/messages/{id}/suggested`
- Completion apps: `POST /v1/completion-messages` (+ stop)
- Events: `GET /v1/workflow/{task_id}/events`
- Human input: `GET/POST /v1/form/human_input/{form_token}`
- Annotations: `/v1/apps/annotations`, `/v1/apps/annotation-reply/{action}`
- Audio: `POST /v1/audio-to-text`, `/v1/text-to-audio`

## Workflow
```http
POST /v1/workflows/run
{"inputs": {"foo": "bar"}, "user": "user-123", "response_mode": "blocking"}
```

Also `POST /v1/workflows/{workflow_id}/run`. Poll `GET /v1/workflows/run/{workflow_run_id}`. Stop: `POST /v1/workflows/tasks/{task_id}/stop`. Logs: `GET /v1/workflows/logs`.

Chatflow uses **chat-messages**, not workflows/run.

## Files
`POST /v1/files/upload` (multipart) then pass the `id` in `files` on chat/workflow. Preview: `/v1/files/{id}/preview`. Console uploads: `POST /console/api/files/upload`. Signed public: `/files/{id}/file-preview` and `/image-preview`.

## WebApp (share site)
`POST /console/api/apps/{id}/site-enable`. Site settings: `GET/POST /apps/{id}/site`. Public chat uses **`/api`** with the site token, not the service API key. Reset token: `POST /apps/{id}/site/access-token-reset`. Passport: `GET /api/passport`.

## Dataset service API
Same Bearer dataset key. Create by text/file (`create-by-text` **and** `create_by_text` aliases), list documents, status batch, segments + child_chunks, hit-testing `/v1/datasets/{id}/retrieve`, metadata, tags (`/v1/datasets/tags`, binding).

## Parameters / info
`GET /v1/parameters`, `/v1/info`, `/v1/meta`, `/v1/site` — what the WebApp needs (opening statement, file types). Workspace models (if the key allows): `/v1/workspaces/current/models/model-types/{model_type}`.

## OpenAPI
`POST /openapi/v1/apps/{id}:run`, `:stop`, DSL import, human-input-forms. Health: `GET /openapi/v1/_health`. Skip unless those env flags are on.

## Failure patterns
- 401: wrong key or API not enabled.
- 400 unused inputs: workflow start variables must match `inputs` keys.
- Streaming parse: SSE `data: {json}` lines; do not assume a single JSON body.
- File URLs from tools may use `INTERNAL_FILES_URL` (`http://api:5001`) which browsers cannot open — keep public `FILES_URL` for humans.
- Hitting `/console/api/...` with a Bearer app key fails; that is the wrong surface.
