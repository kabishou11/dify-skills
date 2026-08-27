---
name: Dify apps and workflows
description: >-
  Use this when creating or editing Dify apps, chatflows, workflows, DSL, canvas publish, variables, or triggers.
---
# Dify apps and workflows

Use this when creating or editing apps, the canvas, DSL, or publishing. Login: [Dify console API](sand-workflow:dify-console-api). After publish: [Dify service API](sand-workflow:dify-service-api). Failures: [Dify troubleshooting](sand-workflow:dify-troubleshooting).

Field-tested on 1.16.1 production canvases; this tree targets **1.17**. DSL `version` is **not** the Dify software version — `GET /console/api/app-dsl-version` (1.17 exports `0.7.0`; 1.16.1 exports were often `0.1.5`). Never copy a foreign `version`.

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
4. **Sync in place** (keep URL / API key): `POST /apps/{id}/workflows/draft` (not PATCH) with `graph`, `features`, `environment_variables`, `conversation_variables`, `hash`. Then `POST /apps/{id}/workflows/publish` `{}`.
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
| `data.type` | `llm` / `code` / `loop` / … no prefix | engine invalid |
| Do **not** write | `positionAbsolute`, child `extent`, loop `outputs` | unofficial |

Loop children: `parentId=<loopId>`, `zIndex: 1002`. Edges: `type: custom`, `data: {isInIteration, isInLoop, sourceType, targetType}`. If-else / classifier `sourceHandle` is `true`/`false`/`fail-branch` or the class id — not `source`.

Selectors: `["nodeId","field"]`, `["sys","query"]`, `["env","VAR"]`, loop vars `["loopId","var"]`. Templates: `{{#nodeId.field#}}`, `{{#sys.query#}}`, `{{#env.THINK_SWITCH#}}`. Knowledge into LLM: put `{{#context#}}` in the **system** prompt (this generation does not inject context unless you write the placeholder).

## Node gotchas (1.16 field-tested, still the checklist on 1.17)

**LLM.** Must include a **user** message (`No user query found`). `vision.enabled: true` requires `configs.variable_selector` (e.g. `["sys","files"]`) + `detail`, else publish "视觉变量不能为空". Thinking models: `max_tokens` ≥ 16384 or the thought eats the budget and `text` is empty. Fast path: `/no_think` at the end of system. Strip `<think>...</think>` with a code node if the provider surfaces it. `retry_config` + `error_strategy: default-value` are default. Do not enable node `structured_output` on models that lack it — JSON schema in the prompt + code parse.

**Code.** Input field is **`value_selector`**, not `variable_selector`. Sandbox: stdlib only, `sleep` ≤ 2s. Nested generators: build newlines with `chr(10)` to avoid escape hell. `compile(code, id, "exec")` before import.

**If-else.** Numeric operators are Unicode `≥` `≤` `≠`, not `>=`. Cases use `conditions[]` + `varType`.

**Knowledge-retrieval.** Rerank needs **four** keys: `provider` + `model` (UI) and `reranking_provider_name` + `reranking_model_name` (engine). Wrong provider → `credentials is not initialized`. Rerank `score` may be `None` — gate on chunk **count**, not score. Output is `result` (array). Dataset UUIDs are **this** tenant — remap on another box.

**Tool.** Three name systems: API tools use OpenAPI **`operationId`**; builtin plugins use identity.name; MCP uses MCP names. Mixing them → `Unknown error`. API tool output is **only** `text` (whole JSON string) — parse in code. `provider_id` for API tools is the `tool_api_providers.id` UUID (remap on another box). Builtin `provider_type: builtin` uses a name, not a UUID.

**HTTP request.** Always send `authorization: {"type":"no-auth","config":null}` even when unused. Timeouts are three ints (connect/read/write). Body `data` is a **string** with `{{#...#}}` templates. Intranet hosts: [Dify intranet](sand-workflow:dify-intranet) (`NO_PROXY` / SSRF).

**Loop.** Official pattern: inject via `loop_variables` → children read `[loopId, var]` → in-loop `assigner` v2 writes back → `break_conditions` reference **loop vars**, not child outputs (publish "无效的变量"). Each break condition needs `id` + `varType`. No `outputs` on the loop node. Sleep inside ≤ 2s.

**List-operator.** Output field is `result`. Set `var_type` / `item_var_type`. Workflow start `file` is often a **single** file, not `sys.files`.

**Variable-aggregator.** Merges branches without failing the unused side. Output commonly `output`.

**Document-extractor.** No images — `default-value` empty text and send scans to an OCR tool (e.g. MinerU) instead.

**Question-classifier.** Must have a `fail-branch` edge. `sourceHandle` = class id. Keep temperature low.

**Answer (chatflow).** Template may include `{{#nodeId.field#}}`. Empty leftover placeholders show in the WebApp.

**Assigner.** `version: "2"`, `operation: over-write`, `loop_id` set when inside a loop.

Prefer **serial** over join-heavy graphs: multiple inbound edges can stall as a join. Put `retry_config` + `error_strategy` on LLM/tool/HTTP.

## Bindings when moving DSL between instances

Remap before import: `dataset_ids`, API-tool `provider_id`, model **display** `name` (Dify entry, not the vLLM `served-model-name`). Same volume restore → UUIDs stay, do not rewrite. After remap, re-check the four rerank fields and tool `operationId`.

## Canvas collaboration (editor stuck on "同步数据中")

1.16+ uses **Socket.IO** (`/socket.io/?EIO=4&transport=websocket`), not `/api/ws`. nginx must proxy `/socket.io/` to `api_websocket` with Upgrade headers. `NEXT_PUBLIC_SOCKET_URL` must be a host the **browser** can reach (not `ws://localhost` for remote users). After recreating api/web, `nginx -s reload` (cached upstream IPs → 502).

## Human input / triggers / basic chat

Human input, triggers, site, annotations, stats: same routes as before (workspace extras / this skill's previous map). Site: `POST /apps/{id}/site-enable`. MCP: `POST /apps/{id}/server`.

## Publish checklist

1. Every node has top-level `type`.
2. Vision configs / rerank four fields / classifier fail-branch / loop break `id`+`varType`.
3. `compile` every code node; edges reference existing ids.
4. Draft run **every** branch (intent / tool fail / empty retrieve / file / HTTP timeout).
5. Publish → `api-enable` / `site-enable`. Start variables match caller `inputs`.
