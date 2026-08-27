---
name: Dify model providers
description: >-
  Use this when adding or switching Dify model providers (OpenAI-compatible, vLLM, Xinference, Tongyi, embeddings, ASR).
---
# Dify model providers

Use this when adding or switching LLM / embedding / rerank / ASR providers on self-hosted Dify.

## Load order

1. Plugin `local runtime ready` (otherwise the provider is missing).
2. Save credentials on the provider.
3. Enable models. The Dify **display `name`** is what canvas/DSL store — it is often **not** vLLM `served-model-name`. Map them explicitly.

## OpenAI-compatible / vLLM / Xinference

Base URL is the internal `/v1`. API key can be a dummy string if the server ignores it. `agent_thought_support`: `not_supported` vs `supported` are **two Dify model rows** on the same physical endpoint — pick the one the agent strategy needs.

Intranet: do not default the workspace to MiniMax / cloud keys. Old MiniMax chat models require `minimax_group_id`; missing it fails every completion. Delete that default or fill Group ID.

## Credentials vs DB

Credentials encrypt with `SECRET_KEY`. Changing the key → `credentials is not initialized`. After plugin-daemon restart, stale `provider_models` rows can orphan — delete the row and re-save.

## Embeddings / rerank / ASR

`high_quality` datasets need a working embedding model. Rerank in a knowledge node needs both UI (`provider`/`model`) and engine (`reranking_provider_name`/`reranking_model_name`) names. FunASR / local ASR: plugin first, then provider credentials.

## Thinking / vision models

- Thinking: `max_tokens` ≥ 16384; optional `/no_think`; strip `<think>` in a code node if the downstream parser chokes.
- Vision: `vision.enabled` requires `configs.variable_selector` pointing at the file var.

## Do not

Paste cloud keys or host URLs into skills/git. `DEPLOYMENT_EDITION=ENTERPRISE` does not add providers.
