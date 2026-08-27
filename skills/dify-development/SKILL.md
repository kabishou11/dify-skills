---
name: Dify development
description: >-
  Use this first for any Dify work — routes to console, plugins, apps, RAG,
  models, agents, workspace extras, API catalog, compose/env, intranet, debug, backup.
---
# Dify development (router)

Use this first when the user wants anything Dify-related. Pick one skill and follow it; do not reinvent HTTP.

| Situation | Skill |
|---|---|
| Login, CSRF, which URL, reboot, "just operate Dify" | Dify console API |
| Which prefix (`/console/api` vs `/v1` vs `/api` vs `/openapi/v1` vs MCP / inner) | Dify API catalog |
| Workspace Skills, snippets, Agent roster, RAG pipeline, MCP, members, tags, annotations, plugin endpoints, human input | Dify workspace extras |
| Install / repair / list plugins, Marketplace empty, uv failed | Dify plugin install |
| Create/edit chat, chatflow, workflow, DSL, publish canvas | Dify apps and workflows |
| Code-first DSL, Loop/Iteration, React #130, draft `hash`, `app-dsl-version` | Dify apps and workflows |
| Knowledge base, upload docs, retrieval, RAGFlow external | Dify knowledge bases |
| LLM / embedding / rerank / ASR / vLLM / OpenAI-compatible | Dify model providers |
| Agent-chat tools, OpenAPI tools, workflow-as-tool, `operationId` | Dify agents and tools |
| Agent Studio roster (`/agent`), bind Skills, composer | Dify workspace extras |
| Write or pack a `.difypkg` | Dify plugin development |
| App `404`, CSRF, plugin red, "同步数据中", nginx 502 after recreate | Dify troubleshooting |
| Call `/v1/chat-messages` or `/v1/workflows/run`, API keys, `Invalid upload file` | Dify service API |
| Backup, upgrade, air-gap pack, both Postgres DBs, `.env` drift | Dify backup and upgrade |
| Workers, timeouts, uploads, workflow/loop caps, nginx, postgres, mail, `.env` injection | Dify compose and config |
| Private network, no SaaS, SSRF, `NO_PROXY`, internal vLLM/SQL | Dify intranet |

## Hard rules (every Dify task)
1. Prefer Console API over the browser. Browser only for first `/install`, OAuth, captcha.
2. Never store passwords or `SECRET_KEY` in skills, git, or chat logs. Point at a secrets file.
3. Keep `DEPLOYMENT_EDITION=COMMUNITY` unless there is a real license.
4. If plugin_daemon / api cannot reach the internet, **do not** "fix" it with iptables FORWARD or a host CONNECT proxy. Host-side `.difypkg` + local PEP 503 index.
5. Intranet first — follow Dify intranet. Do not pile on cloud-search SaaS unless asked.
6. Judge plugins by `GET .../plugin/list` **and** `docker logs plugin_daemon` (`local runtime ready`). Clear failed-task UI with `POST .../plugin/tasks/delete_all`.
7. `/agent` is Agent Studio. `mode: agent-chat` is the classic app. Do not mix their URLs.
8. Community RBAC / billing / some RAG publish 403s are feature gates, not CSRF.
9. Service API: same API key + same stable `user` for upload and run. Console uploads are invalid on `/v1`.
10. DSL `version` comes from `GET /console/api/app-dsl-version` (1.17 = `0.7.0`). Never paste a 1.16 `0.1.5` export onto 1.17. Every canvas node needs top-level `type: "custom"` or the UI throws React #130.
11. 1.17 env: api/worker/web/plugin_daemon/sandbox load `.env` via `env_file` (optional knobs in `docker/envs/*.env`). nginx/ssrf/weaviate/db still need listed `environment:` / `command:`. After recreating api/web, `nginx -s reload`. Knobs: [Dify compose and config](sand-workflow:dify-compose-and-config).

## Order of work for a new Dify box
1. Compose up, `GET /console/api/setup`
2. Login (Base64 password + CSRF)
3. Intranet model endpoint → default models
4. Plugins the user named
5. Knowledge base if they have files
6. App (workflow / chatflow / agent-chat) **or** Agent Studio roster
7. Publish + API key (or MCP server)

## If two skills overlap
Operate vs debug → troubleshooting when there is an error, console API when you are only fetching/changing config. Service API vs console → `/v1` is for *published* apps and external callers; `/console/api` is for you as admin. Catalog vs a domain skill → catalog picks the prefix; the domain skill has the payload. Compose knobs vs a crash → compose-and-config to change a value, troubleshooting when it is already broken. Import vs edit → `POST /apps/imports` always creates a **new** app; in-place canvas edits are `POST .../workflows/draft` plus `hash`.
