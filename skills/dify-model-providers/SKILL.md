---
name: Dify model providers
description: >-
  Use this when adding or switching Dify model providers (OpenAI-compatible,
  vLLM, Xinference, Tongyi, embeddings, ASR).
---
# Dify model providers

Use this when adding LLM / embedding / rerank / STT / TTS. Plugin must already be ready ([Dify plugin install](sand-workflow:dify-plugin-install)). Login: [Dify console API](sand-workflow:dify-console-api).

## List and save
- `GET /console/api/workspaces/current/model-providers`
- Save: `POST /workspaces/current/model-providers/{provider}/credentials`
- Validate: `POST .../credentials/validate` — always, before wiring apps
- Switch: `POST .../credentials/switch`
- Per-model credentials: `.../model-providers/{provider}/models` and `.../models/credentials`
- Load defaults: `GET/POST /workspaces/current/default-model`
- By type: `GET /workspaces/current/models/model-types/{llm|text-embedding|rerank|speech2text|tts}`

`{provider}` is a **path** (may contain `/`). Missing from the list = plugin not `local runtime ready` (daemon logs), not a "wrong URL".

## Intranet first
| Plugin | When |
|---|---|
| `langgenius/openai_api_compatible` | Any OpenAI-style gateway (vLLM serve, OneAPI, internal nginx). Set **custom base URL**. |
| `yangyaofei/vllm` | Direct vLLM (official `langgenius/vllm` often does not exist) |
| `langgenius/xinference` | Xinference |
| `langgenius/modelscope` | ModelScope / local |
| `langgenius/funasr` | Self-host ASR (SenseVoice etc.) |
| `langgenius/tongyi` | DashScope — needs Aliyun key even on intranet |
| `langgenius/openai` / `zhipuai` / `moonshot` / `minimax` | Vendor clouds |

Do not assume `api.openai.com` is reachable. For RAG you need **embedding** (and usually rerank) on the same workspace.

## Types
`llm`, `text-embedding`, `rerank`, `speech2text`, `tts`. Add at least: one chat LLM, one embedding. STT: FunASR or OpenAI-compatible whisper.

## Validate
After save: `credentials/validate`, then a 1-token chat or a dataset hit-test. Plugin listed but validate fails → wrong endpoint, key, or daemon uv still broken.

## System defaults
Set workspace default LLM / embedding / rerank / speech via `default-model`. New apps inherit these.
