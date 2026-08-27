---
name: Dify agents and tools
description: >-
  Use this when building Dify Agent apps, attaching tools,
  OpenAPI/workflow-as-tool, or configuring agent strategies.
---
# Dify agents and tools

Use this when building Agent **apps**, attaching tools, or setting strategies. Agent Studio roster / workspace Skills / MCP server: [Dify workspace extras](sand-workflow:dify-workspace-extras). Canvas: [Dify apps and workflows](sand-workflow:dify-apps-and-workflows). Plugins: [Dify plugin install](sand-workflow:dify-plugin-install).

## Choose a shape
- `mode: "agent-chat"` — classic agent (prompt + tool picker in model-config) under `/apps`
- Chatflow/workflow — drop an **Agent** node (needs `langgenius/agent` strategy plugin)
- **Agent Studio** — `POST /agent` roster (not an `/apps` row). Follow workspace extras.

Optional strategy: `langgenius/self_refine_agent`. Without `langgenius/agent`, Agent nodes are limited.

## Enable tools (installed ≠ enabled)
1. Daemon: `Installed tool: ...` / `local runtime ready`
2. `GET /console/api/workspaces/current/tool-providers`
3. Credentials: `POST /workspaces/current/tool-provider/builtin/{provider}/add` (or `update`). Schema: `GET .../builtin/{provider}/credential/schema/{credential_type}`
4. agent-chat: put tools in `POST /apps/{id}/model-config`
5. Canvas: Tool node or Agent node → select provider/tool
6. Studio agent: bind workspace Skills (`PUT /workspaces/current/agents/{id}/skills`) and enable tools the same way

Also: `GET /workspaces/current/agent-providers` (strategy plugins), `GET /apps/{id}/agent/logs`.

## Intranet tools to prefer
SQL (`junjiem/db_query`, `hjlarry/database`, `spance/db_client_node`), SQLite, Redis, SSH/SFTP, SMTP (`langgenius/email`), Excel/PDF/Markdown exporters, datetime, maths, **built-in HTTP Request**, **built-in Code**. Point hosts at internal URLs.

Skip adding more Google/Tavily/Exa/Wolfram unless asked.

## Custom tools
- OpenAPI: `POST /workspaces/current/tool-provider/api/add`; test `POST .../api/test/pre`
- Workflow-as-tool: publish workflow first, then `POST .../tool-provider/workflow/create`
- MCP **client** (consume an external MCP): tool-provider MCP routes under `/workspaces/current/tool-providers`
- MCP **server** (expose this app): `/apps/{id}/server` — workspace extras

## Strategy knobs
Self-host `.env`: `MAX_TOOLS_NUM`, `MAX_ITERATIONS_NUM`, `WORKFLOW_CALL_MAX_DEPTH`. Function-calling needs a model that actually supports tools; otherwise ReAct.

## Debug
Tool missing in the Agent UI:

1. Not in `plugin/list` → install
2. List yes, daemon no `Installed tool` → uv/runtime (plugin install skill)
3. Runtime yes, picker empty → credentials not `add`ed
4. Picker yes, run fails → wrong internal URL, SSRF, or missing `user`/inputs
5. Studio composer empty Skills → skill not published, or not bound

HTTP 4xx from a tool to `10.`/`172.` → `SSRF_PROXY_ALLOW_PRIVATE_IPS`.

Composer on a workflow Agent node: `GET /apps/{id}/workflows/draft/nodes/{node_id}/agent-composer`, `POST .../copy-from-roster`, `.../validate`, `.../save-to-roster`.
