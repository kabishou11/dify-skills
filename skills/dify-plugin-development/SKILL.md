---
name: Dify plugin development
description: >-
  Use this when writing, packing, debugging, or publishing a Dify plugin (tool,
  model, agent strategy, endpoint).
---
# Dify plugin development

Use this when writing, packing, debugging, or publishing a Dify plugin. Installing the result: [Dify plugin install](sand-workflow:dify-plugin-install).

## Layout

SDK: `dify-plugin`. Pack: `dify-plugin plugin package ./your-plugin` → `.difypkg`.

```
manifest.yaml
main.py
provider/my_tool.yaml
provider/my_tool.py
tools/lookup.yaml
tools/lookup.py
_assets/icon.svg
requirements.txt
```

`manifest.yaml`:

```yaml
version: 0.0.1
type: plugin
author: myorg
name: my-tool
label: {en_US: My Tool, zh_Hans: 我的工具}
description: {en_US: lookup, zh_Hans: 查询}
icon: _assets/icon.svg
resource:
  memory: 268435456
  permission:
    tool: {enabled: true}
    model: {enabled: false, llm: false}
    endpoint: {enabled: false}
    app: {enabled: false}
    storage: {enabled: false, size: 1048576}
plugins:
  tools: [provider/my_tool.yaml]
meta:
  version: 0.0.1
  arch: [amd64, arm64]
  runner: {language: python, version: "3.12", entrypoint: main}
```

`plugins:` keys are `tools` | `models` | `agent_strategies` | `endpoints` | `datasources` — match `type`. `resource.memory` is bytes (256 MiB default is tight for PDF stacks).

Tool provider yaml points at tools; each tool yaml `identity.name` is the **`tool_name`** Agents call (not the marketplace title).

```python
from collections.abc import Generator
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

class LookupTool(Tool):
    def _invoke(self, tool_parameters: dict) -> Generator[ToolInvokeMessage, None, None]:
        q = tool_parameters.get("query") or ""
        if not q:
            yield self.create_json_message({"ok": False, "error": "query required"})
            return
        yield self.create_text_message(q)
        yield self.create_json_message({"ok": True, "query": q})
```

`main.py` is the runner entry (`from dify_plugin import Plugin; Plugin(...).run()`). Pin `dify-plugin` in `requirements.txt`. Do not use unbounded extras (`markitdown[all]`).

## Types

| Type | Role | `plugins:` key |
|---|---|---|
| Tool | Agent / Tool node callable | `tools` |
| Model | llm / embedding / rerank / stt / tts | `models` |
| Agent strategy | ReAct, function-calling | `agent_strategies` |
| Endpoint | HTTP the plugin serves | `endpoints` |
| Datasource | knowledge ingest | `datasources` |

## Debug against a running Dify

1. `.env`: `FORCE_VERIFYING_SIGNATURE=false`. Recreate **plugin_daemon** (+ api if the flag is read there).
2. Publish daemon debug port (`PLUGIN_DEBUGGING_PORT`, default 5003). Host shown to the CLI: `EXPOSE_PLUGIN_DEBUGGING_HOST` / `EXPOSE_PLUGIN_DEBUGGING_PORT`.
3. Plugin dir `.env` with the daemon debug URL, then `dify-plugin plugin run` (flag name: `dify-plugin --help` — it moved across CLI versions).
4. Console shows a debugging plugin; invoke without packing.

Install the packed file: `POST /console/api/workspaces/current/plugin/upload/pkg` then `install/pkg`. If plugin_daemon cannot reach PyPI, vendor wheels into the local index (plugin install skill).

## Design

- Prefer calling an **internal HTTP service** over shipping GPU models in the plugin process.
- Tools should timeout and return structured JSON errors the Agent can read (`create_json_message`).
- Endpoint plugins serve `/plugin/{endpoint_id}` (not `/console/api`).

## Failure patterns

| Error | Cause | Fix |
|---|---|---|
| plugin missing after pack | `plugins:` key ≠ type | tools vs models vs agent_strategies |
| Agent `Unknown error` | `identity.name` ≠ node `tool_name` | use the yaml name |
| uv `exit status 1` | extra not mirrored | pin tiny `requirements.txt` |
| debug never appears | daemon debug port unpublished / signature on | `FORCE_VERIFYING_SIGNATURE=false`, publish 5003 |
| 413 on upload | package > `PLUGIN_MAX_PACKAGE_SIZE` | raise it **and** `NGINX_CLIENT_MAX_BODY_SIZE` |

## Marketplace

Publish at the public Marketplace (org + signing). Self-host can load unsigned `.difypkg` when signature verification is off.
