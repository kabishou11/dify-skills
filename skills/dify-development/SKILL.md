---
name: Dify development
description: >-
  Use this first for any Dify work — routes to console, plugins, apps, RAG,
  models, agents, logs, sandbox, hit-test, workspace extras, API catalog, compose/env, intranet, debug, backup.
  Use this to tune a new isomorphic Dify 1.17 box: platform compose/.env/nginx/workers/timeouts (not custom tools).
---
# Dify development (router)

## Instructions

Use this first when the user wants anything Dify-related. Pick one skill and follow it; do not reinvent HTTP.

| Situation | Skill |
|---|---|
| Login, CSRF, which URL, reboot, "just operate Dify" | Dify console API |
| Which prefix (`/console/api` vs `/v1` vs `/api` vs `/openapi/v1` vs MCP / inner) | Dify API catalog |
| Workspace Skills, snippets, Agent roster, RAG pipeline, MCP, members, tags, annotations, plugin endpoints, human input | Dify workspace extras |
| Workflow / conversation logs, node traces, app statistics, annotations | Dify workspace extras |
| Agent Studio debug chat, logs, sandbox files | Dify workspace extras |
| Install / repair / list plugins, Marketplace empty, uv failed | Dify plugin install |
| Create/edit chat, chatflow, workflow, DSL, publish canvas | Dify apps and workflows |
| Workflow schedule (cron), webhook / plugin trigger, enable/disable, `TRIGGER_URL` | Dify apps and workflows |
| Reusable OCR workflow-as-tool, MinerU plugin vs async `/file_parse` | Dify agents and tools |
| Code-first DSL, Loop/Iteration, React #130, draft `hash`, `app-dsl-version` | Dify apps and workflows |
| Code node sandbox (`value_selector`, stdlib, `/dependencies`, timeouts) | Dify apps and workflows |
| Knowledge base, upload docs, retrieval, RAGFlow external | Dify knowledge bases |
| Dataset hit-test / retrieve | Dify knowledge bases |
| LLM / embedding / rerank / ASR / vLLM / OpenAI-compatible | Dify model providers |
| Agent-chat tools, OpenAPI tools, workflow-as-tool, `operationId` | Dify agents and tools |
| Agent Studio roster (`/agent`), bind Skills, composer | Dify workspace extras |
| Write or pack a `.difypkg` | Dify plugin development |
| App `404`, CSRF, plugin red, "同步数据中", nginx 502 after recreate | Dify troubleshooting |
| Call `/v1/chat-messages` or `/v1/workflows/run`, API keys, `Invalid upload file` | Dify service API |
| Backup, upgrade, air-gap pack, both Postgres DBs, `.env` drift | Dify backup and upgrade |
| Workers, timeouts, uploads, workflow/loop caps, sandbox, nginx, postgres, mail, json-file logs, `.env` injection, **new-box platform tune** | Dify compose and config |
| Private network, no SaaS, SSRF, `NO_PROXY`, internal vLLM/SQL | Dify intranet |
| Custom OpenAPI / workflow-as-tool / Agent tools (not platform tune) | Dify agents and tools |

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
11. 1.17 official compose: api/worker/web load `.env` via `env_file`. Customized clones often **list** keys in `environment:` (then `.env` alone is ignored) or bind-mount nginx/squid. Trust `printenv`. After recreating api/web, `nginx -s reload`. Knobs: [Dify compose and config](sand-workflow:dify-compose-and-config).
12. 1.17 `POST /apps/{id}/workflows/draft` is `graph`+`features`+`hash` (+ `conversation_variables`). Top-level `environment_variables` → 400 `extra_forbidden`. Env edits: `environment_variable_patch`.
13. 1.17 Console **GET** also needs `X-CSRF-Token` (cookie alone → 401). Unauthenticated `/` → 307 `/signin` is normal. Agent Studio is `GET /agent`, not `/apps`.
14. Ship **text-PDF** and **OCR** as separate apps. Prefer **one reusable OCR workflow published as a tool** over dropping MinerU on every canvas. An if-else “short text → OCR loop” still puts OCR on that canvas. Product backends (`/v1`) run **published**, not draft.
15. On 1.17.0, treat workspace Skill **file upload**, FastMCP OAuth, QA-segment answer PATCH, and Agent Studio **tool calling** as unstable until a patch release. Prefer classic workflow + `/v1` for anything a customer will demo.
16. Schedule Trigger cannot share a graph with `start`. File ingest and daily cron are two apps. Cron must be published. There is no one-shot delay queue.
17. Host iron (when host ops docs exist): **one** LLM on :8001 (Dense 27B TP=4, ctx 262144, `--disable-custom-all-reduce`; the old “TP=1 / ctx 16384” rule is obsolete). No second LLM. No MTP. Do not `compose down -v`. Do not `pull :latest` without a digest. Local wheels only; never `pip install torch` from PyPI. Do not publish frozen contract-review / kbqa product apps.

## 新环境：Dify 平台基础配置

This is **Dify 1.17 Community platform** tune (compose / `.env` / nginx / workers / timeouts / uploads / SSRF / DB). It is **not** custom OpenAPI tools, PageIndex, MinerU wrappers, or importing business DSL — those belong in other docs if the operator asks later.

Order:

1. Read **runtime** on a healthy clone (`docker exec … printenv`, `nginx -T`, db `command:`) — not the `.env` file alone.
2. Edit the **new** box. Tables and recreate vs reload: [Dify compose and config](sand-workflow:dify-compose-and-config).
3. Intranet URLs / Squid / `NO_PROXY` so api can reach `:8001` without opening the public net: [Dify intranet](sand-workflow:dify-intranet).
4. Register OpenAI-compatible LLM + embedding + rerank in Console (platform providers only): [Dify model providers](sand-workflow:dify-model-providers). `curl` `:8001/v1/models` first.
5. Recreate only the services that need it. Verify. Failures: [Dify troubleshooting](sand-workflow:dify-troubleshooting).

**Done:** console login; Dify can chat via the local LLM; large PDF does not 413; long workflows survive ≥7200s nginx/gunicorn/workflow caps; beat/schedule queues exist if you need cron; SSRF allows host models, not `*`; still one LLM, no MTP, no unpinned `:latest`.

## Order of work for a new Dify box
1. Compose up, `GET /console/api/setup`
2. Login (Base64 password + **cookie and CSRF on every later GET/POST**)
3. **Platform tune** (section above) — compose/intranet/models
4. Plugins the user named (offline `.difypkg`; do not install a second OCR stack unless asked)
5. Knowledge base / apps only if they asked — not part of platform tune

## If two skills overlap
Operate vs debug → troubleshooting when there is an error, console API when you are only fetching/changing config. Service API vs console → `/v1` is for *published* apps and external callers; `/console/api` is for you as admin. Catalog vs a domain skill → catalog picks the prefix; the domain skill has the payload. Compose knobs vs a crash → compose-and-config to change a value, troubleshooting when it is already broken. Import vs edit → `POST /apps/imports` always creates a **new** app; in-place canvas edits are `POST .../workflows/draft` plus `hash`. Platform tune vs tools → compose/intranet/model-providers; do not start with agents-and-tools.

## Examples

Operator: “new isomorphic box, tune Dify to best” → section **新环境：Dify 平台基础配置**, then compose-and-config tables. Do not import business graphs.

## Performance Notes

One LLM :8001. Cap Celery at 16. Workflow/nginx/gunicorn ≥ 7200s for long OCR/contract-class runs. json-file `50m×3` in compose.

## Troubleshooting

413 / timeout / CSRF / “同步数据中” → [Dify troubleshooting](sand-workflow:dify-troubleshooting). Compose drift (`.env` vs listed env vs bind-mount) → compose-and-config.
