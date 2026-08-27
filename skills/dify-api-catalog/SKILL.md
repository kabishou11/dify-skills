---
name: Dify API catalog
description: >-
  Use this when looking up Dify 1.17 HTTP prefixes, auth, or which skill owns a
  route (console, /v1, WebApp, OpenAPI, MCP, inner API).
---
# Dify API catalog (1.17)

Use this to pick the right prefix and skill. Do not invent HTTP. Re-scan `api/controllers` in your Dify checkout if the tree moved.

Login / CSRF: [Dify console API](sand-workflow:dify-console-api). Workspace Skills / Agent roster / RAG pipeline / MCP / members: [Dify workspace extras](sand-workflow:dify-workspace-extras).

## Prefixes and auth

| ns | Prefix (nginx) | Auth | Call from |
|---|---|---|---|
| console | `/console/api` | Cookie + `X-CSRF-Token` | You as admin |
| service | `/v1` | `Authorization: Bearer` app or dataset key | Published callers |
| web | `/api` | WebApp passport / site token | Share site, not console |
| openapi | `/openapi/v1` | OAuth bearer (`difyctl`); needs `OPENAPI_ENABLED` + `ENABLE_OAUTH_BEARER` | CLI / OAuth clients |
| files | `/files` | Signed URL or session | Previews, plugin uploads |
| mcp | `/mcp` or `/server/{code}/mcp` | MCP `server_code` | MCP clients |
| inner | plugin_daemon ↔ api only | Internal key | **Never call from the host as a product API** |
| blueprints | `/webhook/{id}`, `/webhook-debug/{id}`, `/plugin/{endpoint_id}`, `/oauth/device/*`, `/knowledge-fs/*` | Each its own | Triggers / plugin HTTP / SSO |

Community: `/workspaces/current/rbac/*` and `/billing/*` 403 or empty. That is not a license unlock.

`?` in the dump means the scanner missed the `def` (often POST/PUT next to GET). Confirm in the controller before claiming a method.

## Console groups → skill

All paths below are under `/console/api`.

| Prefix | Skill |
|---|---|
| `/login`, `/logout`, `/refresh-token`, `/account/*`, `/setup`, `/files/upload` | Dify console API |
| `/apps`, `/apps/{id}/workflows/*`, `/apps/imports`, `/apps/{id}/triggers` | Dify apps and workflows |
| `/datasets`, `/datasets/{id}/documents`, `/datasets/{id}/hit-testing` | Dify knowledge bases |
| `/rag/pipelines`, `/rag/pipeline/*`, `/auth/plugin/datasource` | Dify workspace extras (RAG pipeline) + knowledge bases |
| `/workspaces/current/model-providers`, `/default-model` | Dify model providers |
| `/workspaces/current/tool-providers`, `/workspaces/current/triggers` | Dify agents and tools |
| `/workspaces/current/plugin/*` | Dify plugin install |
| `/agent`, `/agent/{id}/*`, `/apps/{id}/server`, `/workspaces/current/skills` | Dify workspace extras + agents and tools |
| `/workspaces/current/customized-snippets`, `/snippets/{id}/workflows` | Dify workspace extras |
| `/apps/{id}/chat-conversations`, `/workflow-app-logs`, `/workflow-runs`, `/statistics/*`, `/workflow/statistics/*`, `/annotations` | Dify workspace extras |
| `/apps/{id}/triggers`, `/apps/{id}/trigger-enable`, `/apps/{id}/workflows/triggers/webhook` | Dify apps and workflows |
| `/v1/*` after publish | Dify service API |

## `/v1` service API (complete)

Bearer app key: `/v1/chat-messages`, `/v1/completion-messages`, `/v1/workflows/run` (+ `/{id}` and `/{workflow_id}/run`), stop, `/v1/workflows/logs`, `/v1/workflow/{task_id}/events`, `/v1/conversations` (+ name, variables), `/v1/messages` (+ feedbacks, suggested), `/v1/files/upload`, `/v1/files/{id}/preview`, `/v1/audio-to-text`, `/v1/text-to-audio`, `/v1/parameters`, `/v1/info`, `/v1/meta`, `/v1/site`, `/v1/form/human_input/{form_token}`, `/v1/apps/annotations*`.

Bearer dataset key: `/v1/datasets`, documents (`create-by-text` / `create-by-file` and snake_case aliases), segments + child_chunks, retrieve / hit-testing, metadata, tags.

## WebApp `/api`

Same shapes as chat/workflow, but site token. Also `/api/passport`, `/api/login`, `/api/webapp/access-mode`, saved-messages, pin/unpin, more-like-this.

## OpenAPI `/openapi/v1`

`GET /_health`, `/_version`, workspaces, apps, `:run` / `:stop`, DSL import (`:confirm`, `dependencies:check`), human-input-forms, device OAuth. Off unless both env flags are on.

## MCP

Enable on an app: `GET/POST/PUT /console/api/apps/{id}/server`, rotate `POST .../server/refresh`. Clients hit `POST /mcp/server/{server_code}/mcp`.

## Inner API

`/invoke/llm`, `/invoke/tool`, `/agent-config/*`, `/skills/{id}/pull`, `/enterprise/*`. plugin_daemon only. A 401 here is expected from the host.

## How to look up

1. Match the prefix table.
2. Open the matching skill. Do not copy a console path onto `/v1`.
3. If still missing, `rg '@console_ns.route' api/controllers` in the Dify source tree. Re-scan beats guessing methods.
