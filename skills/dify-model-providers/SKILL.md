---
name: Dify model providers
description: >-
  Use this when adding or switching Dify model providers (OpenAI-compatible, vLLM, Xinference, Tongyi, embeddings, ASR).
---
# Dify model providers

Use this when adding or switching LLM / embedding / rerank / ASR providers on self-hosted Dify. Prefix `/console/api`. Cookie + CSRF: [Dify console API](sand-workflow:dify-console-api). Intranet URLs: [Dify intranet](sand-workflow:dify-intranet).

## Load order

1. Plugin `local runtime ready` (otherwise the provider is missing from the list).
2. Save credentials on the provider (POST below).
3. Enable models. The Dify **display `name`** is what canvas/DSL store — it is often **not** vLLM `served-model-name`. Map them explicitly.
4. Set workspace defaults.

`provider` path is the plugin id, e.g. `langgenius/openai_api_compatible/openai_api_compatible`. `model_type`: `llm` | `text-embedding` | `rerank` | `speech2text` | `tts` | `moderation`.

## OpenAI-compatible / vLLM / Xinference

Base URL is the internal `/v1`. API key can be a dummy string if the server ignores it. `agent_thought_support`: `not_supported` vs `supported` are **two Dify model rows** on the same physical endpoint — pick the one the agent strategy needs.

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

- Thinking: `max_tokens` ≥ 16384; optional `/no_think`; strip `<think>` in a code node if the downstream parser chokes.
- Vision: `vision.enabled` requires `configs.variable_selector` pointing at the file var.

## Failure patterns

| Error | Cause | Fix |
|---|---|---|
| Provider missing from list | plugin not `local runtime ready` | [Dify plugin install](sand-workflow:dify-plugin-install) |
| validate `{result:"error"}` | unreachable endpoint / SSRF | `NO_PROXY` + CIDR list |
| `credentials is not initialized` | `SECRET_KEY` changed or orphan row | re-save; delete orphan `provider_models` |
| `credential_id is required` | `config_from=custom-model` without id | POST credentials first, pass id |
| empty LLM text | thinking budget | `max_tokens` ≥ 16384 |
| canvas model name mismatch | display `name` ≠ served name | map them; do not rewrite DSL blindly |

## Do not

Paste cloud keys or host URLs into skills/git. Keep `DEPLOYMENT_EDITION=COMMUNITY`.
