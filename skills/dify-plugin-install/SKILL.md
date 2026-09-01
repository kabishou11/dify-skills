---
name: Dify plugin install
description: >-
  Use this when installing or repairing Dify marketplace plugins, including
  offline/no-egress and uv wheel failures.
---
# Dify plugin install

Use this when installing, upgrading, listing, or repairing Marketplace plugins. Login first ([Dify console API](sand-workflow:dify-console-api)). Failures: [Dify troubleshooting](sand-workflow:dify-troubleshooting).

## Resolve IDs
Marketplace `https://marketplace.dify.ai`, header `X-Dify-Version: <running Dify version, e.g. 1.17.0>`.

- Batch: `POST /api/v1/plugins/batch` `{"plugin_ids":["langgenius/openai"]}` → `latest_package_identifier` / plugins[]. unique id
- Search: `POST /api/v1/plugins/search/advanced` (plain `/search` often empty)
- Download URL: `GET /api/v1/plugins/download-url?unique_identifier=`
- Unique id: `org/name:version@sha256`

If host batch works but the **api container** times out, skip marketplace install and use the offline path.

## Online install
```http
POST /console/api/workspaces/current/plugin/install/marketplace
{"plugin_unique_identifiers":["org/name:version@checksum"]}
```
Poll `GET .../plugin/tasks`. Healthy list: `GET .../plugin/list`. Daemon must log `local runtime ready`.

Install **3–8 at a time**. One bad id can fail a batch.

`plugin-daemon` image tag is **independent** of `api`/`web`. After a Dify upgrade, if every model provider goes red, bump daemon to the version in that release (1.17 needed a newer `*-local` daemon than 1.16). Do not assume `api:1.17.0` implies the old daemon still works.

## Offline / no-egress (nested cloud VMs)
Do **not** open iptables FORWARD or a host CONNECT proxy.

1. Host: download `.difypkg` from the download-url API.
2. `POST /console/api/workspaces/current/plugin/upload/pkg` (multipart file) → unique identifier.
3. `POST .../plugin/install/pkg` `{"plugin_unique_identifiers":["..."]}`.
4. uv inside **plugin_daemon** installs Python deps. If it cannot reach pypi.org, use the local PEP 503 index already pointed at by `PIP_MIRROR_URL` / `UV_INDEX_URL`:
   - Host `pip download <req> -d .../pypi-mirror/packages` (cp312 manylinux x86_64 **and** abi3).
   - Rebuild `simple/<pkg>/index.html` with href `/packages/<filename>`.
   - **Delete** `plugin_daemon/cwd/.uv-cache/simple-v24`. `UV_NO_CACHE=1` is not enough (`--cache-dir`).
5. Retry install. Logs: `failed to install dependencies` vs `local runtime ready` / `Installed tool:`.

Fat extras (`markitdown[all]`, GPU stacks) need every extra wheel or they fail after the `.difypkg` itself uploaded.

## Failed-task UI
`GET .../plugin/tasks` keeps old failures even after a later success. `POST .../plugin/tasks/delete_all` clears the red list. Trust `plugin/list` + daemon logs.

## Flags
- `FORCE_VERIFYING_SIGNATURE=false` — unsigned/community packages.
- `MARKETPLACE_ENABLED=true` unless fully air-gapped.
- Raise `PLUGIN_MAX_PACKAGE_SIZE` **and** `NGINX_CLIENT_MAX_BODY_SIZE` together or upload 413s.

## Intranet vs SaaS
Prefer user-supplied URL: OpenAI-compatible, vLLM, Xinference, SQL, Redis, SSH, SMTP, HTTP Request **node** (builtin). Skip extra Google/Tavily/Exa unless asked. Official ids sometimes do not exist (`langgenius/vllm` → community vLLM plugin; `langgenius/time` → a datetime tool).

`langgenius/mineru` tool `parse-file` with `server_type=local` does **not** poll. If the local MinerU `/file_parse` is async (`task_id` only), wrap it in a reusable workflow: try the plugin, then fall back to the site's OpenAPI `submit_parse` / `task_status` / `task_result` loop. List first (`GET .../plugin/list`); do not install extra OCR plugins unless asked.
