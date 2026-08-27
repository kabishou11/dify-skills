---
name: Dify development
description: >-
  Use this first for any Dify work — routes to console, plugins, apps, RAG,
  models, agents, workspace extras, API catalog, intranet, debug, backup.
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
| Knowledge base, upload docs, retrieval, RAGFlow external | Dify knowledge bases |
| LLM / embedding / rerank / ASR / vLLM / OpenAI-compatible | Dify model providers |
| Agent-chat tools, OpenAPI tools, workflow-as-tool | Dify agents and tools |
| Agent Studio roster (`/agent`), bind Skills, composer | Dify workspace extras |
| Write or pack a `.difypkg` | Dify plugin development |
| App `404`, CSRF, plugin red, container can't pip, "everything failed" | Dify troubleshooting |
| Call `/v1/chat-messages` or `/v1/workflows/run`, API keys, WebApp | Dify service API |
| Backup, upgrade, volumes, `.env` drift | Dify backup and upgrade |
| Private network, no SaaS, SSRF, internal vLLM/SQL | Dify intranet |

## Hard rules (every Dify task)
1. Prefer Console API over the browser. Browser only for first `/install`, OAuth, captcha.
2. Never store passwords or `SECRET_KEY` in skills, git, or chat logs. Point at a secrets file.
3. Keep `DEPLOYMENT_EDITION=COMMUNITY` unless there is a real license.
4. If plugin_daemon / api cannot reach the internet, **do not** "fix" it with iptables FORWARD or a host CONNECT proxy. Host-side `.difypkg` + local PEP 503 index.
5. Intranet first — follow Dify intranet. Do not pile on cloud-search SaaS unless asked.
6. Judge plugins by `GET .../plugin/list` **and** `docker logs plugin_daemon` (`local runtime ready`). Clear failed-task UI with `POST .../plugin/tasks/delete_all`.
7. `/agent` is Agent Studio. `mode: agent-chat` is the classic app. Do not mix their URLs.
8. Community RBAC / billing / some RAG publish 403s are feature gates, not CSRF.

## Order of work for a new Dify box
1. Compose up, `GET /console/api/setup`
2. Login (Base64 password + CSRF)
3. Intranet model endpoint → default models
4. Plugins the user named
5. Knowledge base if they have files
6. App (workflow / chatflow / agent-chat) **or** Agent Studio roster
7. Publish + API key (or MCP server)

## If two skills overlap
Operate vs debug → troubleshooting when there is an error, console API when you are only fetching/changing config. Service API vs console → `/v1` is for *published* apps and external callers; `/console/api` is for you as admin. Catalog vs a domain skill → catalog picks the prefix; the domain skill has the payload.
