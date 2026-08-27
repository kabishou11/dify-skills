---
name: Dify agents and tools
description: >-
  Use this when building Dify Agent apps, attaching tools, OpenAPI/workflow-as-tool, or configuring agent strategies.
---
# Dify agents and tools

Use this when building Agent / agent-chat apps or wiring tools. Studio roster (`/agent`) is [Dify workspace extras](sand-workflow:dify-workspace-extras), not this.

## Three `tool_name` systems (they do not mix)

| Kind | `tool_name` is | Typical miss |
|---|---|---|
| API / OpenAPI | the spec **`operationId`** | using the human title → `Unknown error` |
| Builtin / plugin | the **plugin tool name** | using the marketplace display name |
| MCP | the **MCP tool name** | using the server label |

API tools return **`text` only** (often a JSON string). Parse in a code node. Builtin/plugin tools may expose structured fields.

## Attach

- OpenAPI: import spec, pick operations, then reference `operationId`.
- Workflow-as-tool: publish the workflow, add as a tool, map start vars.
- MCP: workspace MCP server first, then attach.
- HTTP node is **not** an agent tool; it still needs `authorization: {type: no-auth, config: null}` even when unused.

## Agent app

Create `agent-chat` (or workflow with an agent node). Strategy plugin must be installed. Model row must have the thought-support flavor the strategy expects (`supported` vs `not_supported` are different entries).

Prefer serial tool calls over join when the vendor's parallel join is flaky. Classifier nodes need a `fail-branch`.

## Debug

Draft run SSE `node_finished` shows tool input/output. `Unknown error` with no traceback is almost always a wrong `tool_name`. Intranet HTTP tools: `NO_PROXY` (see [Dify intranet](sand-workflow:dify-intranet)).
