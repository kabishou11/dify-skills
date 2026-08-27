---
name: Dify plugin development
description: >-
  Use this when writing, packing, debugging, or publishing a Dify plugin (tool,
  model, agent strategy, endpoint).
---
# Dify plugin development

Use this when writing, packing, debugging, or publishing a Dify plugin. Installing the result: [Dify plugin install](sand-workflow:dify-plugin-install).

## Layout
SDK: `dify-plugin`. Typical tree:

- `manifest.yaml` — author, name, type, version, resources (`tool` / `model` / `agent_strategy` / `endpoint` / `datasource`)
- `provider/*.yaml` + Python, or `tools/*.yaml` + Python
- `_assets/icon.svg`
- `requirements.txt` or `pyproject.toml` (pin `dify-plugin` and HTTP libs)
- `.env` for local debug

Pack: `dify-plugin plugin package ./your-plugin` → `.difypkg`.

## Types
| Type | Role |
|---|---|
| Tool | Agent / Tool node callable |
| Model | llm / embedding / rerank / stt / tts |
| Agent strategy | ReAct, function-calling, custom planner |
| Endpoint | HTTP the plugin serves |
| Datasource | knowledge ingest |

## Debug against a running Dify
1. Server: `FORCE_VERIFYING_SIGNATURE=false`
2. Daemon debug port published (`PLUGIN_DEBUGGING_PORT`, default 5003)
3. Run the plugin CLI in debug/remote mode so it connects to the daemon (flag name depends on CLI version — `dify-plugin --help`)
4. Console shows a debugging plugin; invoke without packaging

## Install the package
`POST /console/api/workspaces/current/plugin/upload/pkg` then `install/pkg`. If plugin_daemon cannot reach PyPI, vendor wheels into the local index (plugin install skill). Fat extras (`markitdown[all]`) fail unless every extra wheel is mirrored.

## Design
- Prefer calling an **internal HTTP service** over shipping GPU models in the plugin process.
- Keep `requirements.txt` tiny and pinned. Avoid unbounded extras.
- Tools should timeout and return structured JSON errors the Agent can read.
- Manifest `resource.memory` should match real usage (256MB default is tight for PDF stacks).

## Marketplace
Publish at https://marketplace.dify.ai (org + signing). Self-host can load unsigned `.difypkg` when signature verification is off.
