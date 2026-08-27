---
name: Dify service API
description: >-
  Use this when calling published Dify apps via /v1 (chat-messages, workflows/run), API keys, WebApp, or file upload.
---
# Dify service API

Use this when calling a published Dify app or dataset from code. Prefix map: [Dify API catalog](sand-workflow:dify-api-catalog). File/user rules below were the #1 migration break from 1.10 → 1.16+ and still apply on 1.17.

## Surfaces

| Surface | Auth | Path prefix |
|---|---|---|
| Console | session cookie + `X-CSRF-Token` | `/console/api` |
| **Service (this skill)** | `Authorization: Bearer {api_key}` | `/v1` |
| WebApp | passport / site token | `/api` |
| OpenAPI / difyctl | OAuth bearer | `/openapi/v1` |
| MCP | `server_code` | `/mcp/server/{code}/mcp` |

Enable API: `POST /console/api/apps/{id}/api-enable`. Create a key: `POST /console/api/apps/{id}/api-keys`. One key is bound to **one app** — reusing it across apps → 401/404. Never store the key in a skill file.

There is often **no** `/v1/chat/completions`. Use `chat-messages` / `workflows/run`.

## `user` is a data scope (not a comment)

Official meaning: unique within the app; resources created with one `user` are only visible with the same `user`.

- Use a **stable** id (UUID or your product user id).
- Do **not** use the API key, a timestamp, or a random value per request.
- Upload and run **must** use the same `user` **and** the same API key.

## Files (FileAccessController, 1.16+)

`POST /v1/files/upload` (multipart) then pass the returned id. Console `POST /console/api/files/upload` files are **not** valid for `/v1` or WebApp — `Invalid upload file`.

File variable shape is a **single object**, not a string and not an array of ids:

```json
{
  "transfer_method": "local_file",
  "upload_file_id": "<id>",
  "type": "document"
}
```

`file in input form must be a file` → you passed an array/string. Preview: `/v1/files/{id}/preview`.

## Chat

```http
POST /v1/chat-messages
{"query":"你好","user":"<stable-id>","response_mode":"blocking","conversation_id":"","inputs":{},"files":[]}
```

- `user` required. Continue with `conversation_id`.
- Prefer **`blocking`** when you only need the final JSON (long RAG/tools: HTTP timeout **≥ 600s**).
- `streaming`: SSE events include `workflow_started` → `node_started` → `node_finished` → `text_chunk` → `workflow_finished`. Do not `json.loads` the whole body. Read timeout ≥ 600s.
- `A JSONObject text must begin with '{'` → you used blocking parse on an SSE stream (or the opposite).
- Chatflow returns `metadata.retriever_resources[]` (content, document_name, dataset_name, score, position, segment_id). **Workflow** apps do not — export the knowledge node's `result` from `end`.
- Stop: `POST /v1/chat-messages/{task_id}/stop`. History: `GET /v1/messages`. Conversations: `GET /v1/conversations`. Feedback: `POST /v1/messages/{id}/feedbacks`. Suggested: `GET /v1/messages/{id}/suggested`. Audio / human-input / annotations: `/v1/audio-to-text`, `/v1/form/human_input/{form_token}`, `/v1/apps/annotations*`.

## Workflow

```http
POST /v1/workflows/run
{"inputs":{"foo":"bar"},"user":"<stable-id>","response_mode":"blocking"}
```

Chatflow uses **chat-messages**, not this. Poll `GET /v1/workflows/run/{id}`. Stop: `POST /v1/workflows/tasks/{task_id}/stop`.

Production logs (app key; `mode=workflow`):

```http
GET /v1/workflows/logs?keyword=&status=failed&created_at__after=2026-08-01T00:00:00Z&created_at__before=2026-08-27T23:59:59Z&page=1&limit=20
```

`status`: `succeeded` | `failed` | `stopped`. Optional `created_by_end_user_session_id`, `created_by_account`. No `detail` flag (that is console `/workflow-app-logs`). Node traces stay on console `/workflow-runs/{id}/node-executions`. Dataset hit-test: `POST /v1/datasets/{id}/hit-testing` (same body as console; also aliased as `/retrieve`).

## WebApp

`POST /console/api/apps/{id}/site-enable`. Public chat is `/api` + site token, not the service key. Console uploads ≠ WebApp uploads.

## Dataset `/v1`

Bearer dataset key. create-by-text / create-by-file (and snake_case aliases), segments, retrieve, metadata, tags.

## Failure patterns

| Error | Cause | Fix |
|---|---|---|
| `Invalid upload file` | user or key mismatch; console file used on `/v1` | same user + same key; upload on `/v1` |
| `file in input form must be a file` | array/string | single file object |
| 401 | wrong key / API off / key from another app | enable + matching key |
| unused inputs | start vars ≠ `inputs` keys | match names |
| Broken pipe / client timeout | read timeout too small | ≥ 600s |
| 404 on `/v1/chat/completions` | endpoint not enabled | `chat-messages` |
