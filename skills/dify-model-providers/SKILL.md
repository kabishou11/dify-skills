---
name: Dify model providers
description: >-
  Use this when adding or switching Dify model providers (OpenAI-compatible, vLLM, Xinference, Tongyi, embeddings, ASR).
---
# Dify model providers

## Instructions

Use this when adding or switching LLM / embedding / rerank / ASR providers on self-hosted Dify. Prefix `/console/api`. Cookie + CSRF: [Dify console API](sand-workflow:dify-console-api). Intranet URLs: [Dify intranet](sand-workflow:dify-intranet).

## Load order

1. Plugin `local runtime ready` (otherwise the provider is missing from the list).
2. Save credentials on the provider (POST below).
3. Enable models. The Dify **display `name`** is what canvas/DSL store — it is often **not** vLLM `served-model-name`. Map them explicitly.
4. Set workspace defaults.

`provider` path is the plugin id, e.g. `langgenius/openai_api_compatible/openai_api_compatible`. `model_type`: `llm` | `text-embedding` | `rerank` | `speech2text` | `tts` | `moderation`.

## New-box platform wiring (not tools)

This skill registers **Dify model providers**. It does not import OpenAPI tools.

1. `curl -sS http://127.0.0.1:8001/v1/models` (or the new box equivalent). Fail → fix the GPU process, not Dify.
2. **One** LLM on **:8001**. Embedding :8000, rerank :8002. Do not start a second LLM. Do not enable MTP. Multi-GPU: `--disable-custom-all-reduce`. Dense 27B is **TP=4**, `max-model-len` 262144 — ignore the obsolete “must TP=1 / ctx 16384” rule.
3. From **inside** the api container the URL must resolve (host LAN IP or host-gateway). Put that host on `NO_PROXY` first ([Dify intranet](sand-workflow:dify-intranet)).
4. Install `langgenius/openai_api_compatible` (and optional `yangyaofei/vllm`) until `local runtime ready`.
5. POST credentials + enable models + workspace default (below).
6. Thinking completions need `max_tokens` ≥ 16384 **and** the timeout stack in [Dify compose and config](sand-workflow:dify-compose-and-config) (gunicorn/nginx/workflow ≥ 7200 for long graphs).

| Role | Clone-like endpoint (changes) | New box |
|---|---|---|
| LLM | `http://127.0.0.1:8001/v1` served name e.g. `Qwen3.8-27B` | same ports; Dify **display** `name` may differ |
| Embedding | `:8000/v1` | keep; do not share 8001 |
| Rerank | `:8002/v1` (`/v1/rerank`, not chat) | keep |

## OpenAI-compatible / vLLM / Xinference

Base URL is the internal `/v1`. API key can be a dummy string if the server ignores it. `agent_thought_support`: `not_supported` vs `supported` are **two Dify model rows** on the same physical endpoint.

- Fast / no visible chain-of-thought: the `not_supported` row **and** put `/no_think` at the end of the system prompt. That row still lets the model think internally if you omit `/no_think` — you just will not see it, and it still eats `max_tokens`.
- Visible reasoning: the `supported` row, `max_tokens` ≥ 16384, strip `<think>` downstream.

The Dify **display `name`** is what canvas/DSL store. It often lags the vLLM `served-model-name` (operators rename the GPU process and forget the Dify row). Map them; do not “fix” DSL by pasting the served name into `model.name`.

```http
GET /workspaces/current/model-providers
GET /workspaces/current/model-providers/summary
POST /workspaces/current/model-providers/{provider}/credentials/validate
{"credentials":{"api_key":"dummy","endpoint_url":"http://vllm-internal:8000/v1"}}
POST /workspaces/current/model-providers/{provider}/credentials
{"name":"vllm","credentials":{"api_key":"dummy","endpoint_url":"http://vllm-internal:8000/v1"}}
```

Validate returns `{result:"success"}` or `{result:"error",error:"..."}` (not always HTTP 4xx). Create is 201. Update: `PUT` same path `{"credential_id":"...","credentials":{...},"name":"..."}`. Switch active: `POST .../credentials/switch` `{"credential_id":"..."}`. Delete: `DELETE .../credentials` `{"credential_id":"..."}`. GET current: `GET .../credentials?credential_id=`.

Enable / load-balance a model:

```http
GET  /workspaces/current/model-providers/{provider}/models
POST /workspaces/current/model-providers/{provider}/models
{"model":"<display-name>","model_type":"llm","config_from":"custom-model","credential_id":"<uuid>"}
DELETE /workspaces/current/model-providers/{provider}/models
{"model":"<display-name>","model_type":"llm"}
```

Custom-model **requires** `credential_id`. Per-model credentials: `POST .../models/credentials` `{"model":"...","model_type":"llm","name":"...","credentials":{...}}`. Parameter rules: `GET .../models/parameter-rules?model=`. Available by type: `GET /workspaces/current/models/model-types/llm`.

Default for the workspace:

```http
GET  /workspaces/current/default-model?model_type=llm
POST /workspaces/current/default-model
{"model_settings":[{"model_type":"llm","provider":"langgenius/openai_api_compatible/openai_api_compatible","model":"<display-name>"}]}
```

Repeat `model_settings` rows for `text-embedding` / `rerank` / `speech2text`. Empty `provider` on a row is skipped.

Do not leave MiniMax / cloud keys as the workspace default on an air-gap. Old MiniMax chat models require `minimax_group_id`; missing it fails every completion.

## Credentials vs DB

Credentials encrypt with `SECRET_KEY`. Changing the key → `credentials is not initialized`. After plugin-daemon restart, stale `provider_models` rows can orphan — delete the row (`DELETE .../models`) and re-save.

## Embeddings / rerank / ASR

`high_quality` datasets need a working embedding model. Rerank in a knowledge node needs both UI (`provider`/`model`) and engine (`reranking_provider_name`/`reranking_model_name`) names. FunASR / local ASR: plugin first, then provider credentials.

## Thinking / vision models

- Thinking: `max_tokens` ≥ 16384 on the `supported` row; on the `not_supported` row always add `/no_think`. Strip `<think>` in a code node if the downstream parser chokes.
- Vision: `vision.enabled` requires `configs.variable_selector` pointing at the file var.

## Examples

Validate then save:

```http
POST /workspaces/current/model-providers/langgenius/openai_api_compatible/openai_api_compatible/credentials/validate
{"credentials":{"api_key":"dummy","endpoint_url":"http://127.0.0.1:8001/v1"}}
```

Use the host URL that **api** can open (often the LAN IP, not `localhost` from inside Docker unless you added `extra_hosts`).

## Performance Notes

Same physical vLLM: two Dify rows. Fast path = `not_supported` + `/no_think`. Visible reasoning = `supported` + `max_tokens` ≥ 16384. Display `name` is what DSL stores.

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| Provider missing from list | plugin not `local runtime ready` | [Dify plugin install](sand-workflow:dify-plugin-install) |
| validate `{result:"error"}` | unreachable endpoint / SSRF | `NO_PROXY` + CIDR list |
| `credentials is not initialized` | `SECRET_KEY` changed or orphan row | re-save; delete orphan `provider_models` |
| `credential_id is required` | `config_from=custom-model` without id | POST credentials first, pass id |
| empty LLM text | thinking budget | `max_tokens` ≥ 16384 |
| canvas model name mismatch | display `name` ≠ served name | map them; do not rewrite DSL blindly |

## Do not

Paste cloud keys or host URLs into skills/git. Keep `DEPLOYMENT_EDITION=COMMUNITY`. Do not add a second LLM “just to test”. Do not enable MTP. Do not treat custom tools as part of provider setup.

### OpenAI-API-compatible per-model credentials (1.17, validated)

`configurate_methods: customizable-model` — there is **no provider-level credential schema** (POST `.../credentials` → `does not have provider_credential_schema`). Flow for a hosted OpenAI-compatible embedding/rerank:

1. `POST .../{provider}/models/credentials` `{"model": "<upstream-id>", "model_type": "text-embedding", "name": "...", "credentials": {"api_key": ..., "endpoint_url": "https://.../v1", "max_chunks": "16", "context_size": "4096", "encoding_format": "float"}}` (201; text-embedding needs `max_chunks`, llm needs `context_size` + `mode`).
2. `GET .../{provider}/models/credentials?model=...&model_type=text-embedding` → take **`current_credential_id`** (not in the POST response).
3. `POST .../{provider}/models` `{"model": "<upstream-id>", "model_type": "text-embedding", "config_from": "custom-model", "credential_id": "<uuid>"}`.
4. Set workspace default: `POST /workspaces/current/default-model` — pass the **core model name** (`minimax-m3`), not the display label (`MiniMax-M3` → "Model does not exist").

Provider-level key quirks: `add` requires `{"type": "api-key", "credentials": {...}}`; plugin yaml names the key (`aistudio_access_token`, not `access_token` — 400 "credential not found"). Existing rows survive on `providers` table even without a UI credential; enable predefined models via `POST .../{provider}/models` `{"config_from": "predefined-model"}`.
