---
name: Dify agents and tools
description: >-
  Use this when building Dify Agent apps, attaching tools, OpenAPI/workflow-as-tool, or configuring agent strategies.
---
# Dify agents and tools

Use this when building Agent / agent-chat apps or wiring tools. Prefix `/console/api`. Studio roster (`/agent`) is [Dify workspace extras](sand-workflow:dify-workspace-extras), not this.

## Three `tool_name` systems (they do not mix)

| Kind | `tool_name` is | Typical miss |
|---|---|---|
| API / OpenAPI | the spec **`operationId`** | using the human title → `Unknown error` |
| Builtin / plugin | the **plugin tool name** | using the marketplace display name |
| MCP | the **MCP tool name** | using the server label |

API tools return **`text` only** (often a JSON string). Parse in a code node. Builtin/plugin tools may expose structured fields.

List: `GET /workspaces/current/tool-providers?type=builtin|api|workflow|mcp`. Also `/tools/builtin`, `/tools/api`, `/tools/workflow`, `/tools/mcp`.

## OpenAPI / API tools

Parse first, then add. `schema_type`: `openapi` | `swagger` | `openai_plugin`. `auth_type` in credentials is usually `none` or `api_key`.

```http
POST /workspaces/current/tool-provider/api/schema
{"schema":"<openapi yaml or json>"}
GET  /workspaces/current/tool-provider/api/remote?url=http://internal/openapi.json
POST /workspaces/current/tool-provider/api/add
{"provider":"invoice-api","schema_type":"openapi","schema":"<spec>","credentials":{"auth_type":"none"},"icon":{"background":"#E0F2FE","content":"🔧"},"labels":[],"privacy_policy":"","custom_disclaimer":""}
POST /workspaces/current/tool-provider/api/test/pre
{"tool_name":"<operationId>","provider_name":"invoice-api","credentials":{"auth_type":"none"},"parameters":{"id":"1"},"schema_type":"openapi","schema":"<spec>"}
```

Update: `POST .../api/update` (same body + `original_provider`). Delete: `POST .../api/delete` `{"provider":"invoice-api"}`. List tools: `GET .../api/tools?provider=invoice-api`. `provider_id` in a Tool node is the `tool_api_providers.id` UUID (remap on another box). Intranet hosts: [Dify intranet](sand-workflow:dify-intranet).

## Workflow-as-tool

Publish the workflow first. `name` is alphanumeric.

```http
POST /workspaces/current/tool-provider/workflow/create
{"name":"invoice_lookup","label":"发票查询","description":"...","icon":{"background":"#E0F2FE","content":"🔧"},"parameters":[],"workflow_app_id":"<app-uuid>"}
GET  /workspaces/current/tool-provider/workflow/get?workflow_app_id=<app-uuid>
POST /workspaces/current/tool-provider/workflow/update
{"workflow_tool_id":"<uuid>","name":"invoice_lookup","label":"发票查询","description":"...","icon":{"background":"#E0F2FE","content":"🔧"},"parameters":[]}
POST /workspaces/current/tool-provider/workflow/delete
{"workflow_tool_id":"<uuid>"}
```

Map start vars in `parameters[]`. Callers see the **published** graph, not the draft.

## Builtin / plugin credentials

```http
GET  /workspaces/current/tool-provider/builtin/{provider}/tools
GET  /workspaces/current/tool-provider/builtin/{provider}/credentials
POST /workspaces/current/tool-provider/builtin/{provider}/add
{"credentials":{"api_key":"..."},"name":"prod","type":"api-key","visibility":"all_team_members"}
POST /workspaces/current/tool-provider/builtin/{provider}/update
{"credential_id":"<uuid>","credentials":{"api_key":"..."},"name":"prod"}
POST /workspaces/current/tool-provider/builtin/{provider}/delete
{"credential_id":"<uuid>"}
POST /workspaces/current/tool-provider/builtin/{provider}/default-credential
{"id":"<credential_id>"}
```

`type`: `api-key` | `oauth2` | `unauthorized`. OAuth: `/oauth/plugin/{provider}/tool/authorization-url`.

## MCP tools (workspace MCP client)

This is **not** `POST /apps/{id}/server` (that publishes an app as an MCP server).

```http
POST /workspaces/current/tool-provider/mcp
{"server_url":"http://mcp-internal:8080/mcp","name":"internal-mcp","icon":"🔌","icon_type":"emoji","icon_background":"#E0F2FE","server_identifier":"internal-mcp"}
GET  /workspaces/current/tool-provider/mcp/tools/{provider_id}
POST /workspaces/current/tool-provider/mcp/auth
{"provider_id":"<id>","authorization_code":null}
```

Update: `POST .../mcp/update/{provider_id}` (same body + `provider_id`). Delete: body `{"provider_id":"..."}`. `identity_mode` stays off on community.

## Agent app (`mode: agent-chat`)

Create `agent-chat` (or a workflow with an Agent node). Strategy plugin must be installed. Model row must have the thought-support flavor the strategy expects.

Thought trace:

```http
GET /apps/{id}/agent/logs?conversation_id=<uuid>&message_id=<uuid>
```

Prefer serial tool calls over join when the vendor's parallel join is flaky. Classifier nodes need a `fail-branch`. HTTP **node** is not an agent tool; it still needs `authorization: {"type":"no-auth","config":null}`.

## Failure patterns

| Error | Cause | Fix |
|---|---|---|
| `Unknown error` no traceback | wrong `tool_name` | use `operationId` / plugin name / MCP name |
| Tool node empty output | API tool only returns `text` | parse JSON in a code node |
| Workflow-as-tool stale | draft not published | publish the source app |
| MCP tools empty after create | server unreachable / SSRF | `NO_PROXY`; retry `.../mcp/tools/{id}` |
| Builtin add 400 | plugin not installed | [Dify plugin install](sand-workflow:dify-plugin-install) |
