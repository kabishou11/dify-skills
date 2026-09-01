# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Version numbers match **Dify**, not SemVer of this repo.

A GitHub Release is created only when a Dify line is frozen. Until then everything lives on `main` under **Unreleased**.

## [Unreleased] — Dify 1.17.0

Working tree on `main`. **No GitHub Release yet.**

### Added
- Triggers (schedule/webhook/plugin), public `/triggers/webhook/{id}` (not `/webhook/{id}`), plugin Endpoint vs trigger, code-node sandbox timeouts.
- Agent Studio runtime (sandbox files, build-draft, snapshot timeout). Dataset metadata, child chunks, hit-test. Workflow/conversation logs and stats.
- `dify-compose-and-config`: 1.17 `.env` / `docker/envs` injection, workers, timeout stack, dual-plane workflow caps, nginx recreate vs reload, postgres/redis, mail, community login gates.
- README rewritten: problem map, mermaid diagrams, per-skill usage, Cursor / Claude Code / Codex install paths, acknowledgements.
- `scripts/install.sh` copies `skills/dify-*` into `.cursor/skills`, `.claude/skills`, or `.agents/skills`.

- Router plus 13 domain skills covering console, plugins, apps, knowledge, models, agents, service API, intranet, backup, troubleshooting, API catalog, and workspace extras (Skills, snippets, Agent roster, RAG pipeline, MCP).
- Routes scanned from Dify 1.17.0 `api/controllers` (console, `/v1`, WebApp `/api`, OpenAPI, MCP, inner API).

### Changed
- OCR: reuse one published workflow-as-tool (`provider_type: workflow`); do not drop `langgenius/mineru` on every canvas. Plugin `parse-file` does not poll async MinerU `/file_parse` — fall back to OpenAPI submit/status/result + loop. End fields must not be named `text` (reserved). Code nodes cannot take File; optional file → if-else `not empty`. After OCR graph edits, publish then `workflow/update`.
- Triggers: no delay queue; `start` and `trigger-schedule` cannot share a graph (split ingest vs daily cron). Cron must be published. `draft/trigger/run` returns `waiting` until due — simulate with `draft/run` `inputs: {}` or `/v1/workflows/run`.
- Host iron (docs-backed boxes): one LLM :8001, DSL `json.dump`, `project/work/<project>/v1/`, do not publish frozen contract-review/kbqa apps.
- Folded generic lessons from 1.16.1 production ops into the 1.17 skills (no host secrets, IPs, or app ids):
  - Service API file ACL: same key + same stable `user`; file input is one object; prefer `blocking` with HTTP timeout ≥ 600s; `/v1/chat/completions` is often 404.
  - 1.17 api/worker/web load `.env` via `env_file`; nginx/ssrf/weaviate/db still need listed keys. `SSRF_PROXY_ALLOW_PRIVATE_IPS` is a CIDR list, not `true`. Canvas sync is Socket.IO `/socket.io/`.
  - Offline pack must include images, compose, `.env` (`SECRET_KEY`), both `dify` and `dify_plugin` dumps, `plugin_packages/`, `cwd/`, and vector volumes.
  - RAGFlow endpoint is `.../api/v1/dify` (Dify appends `/retrieval`); disable score_threshold because that path has no reranker.
  - DSL: `GET /app-dsl-version` (1.17 = `0.7.0`); every node needs top-level `type: custom`; Loop `break_conditions` need `id`+`varType` on loop vars; rerank needs four name fields; tools use OpenAPI `operationId`.
  - Intranet: `NO_PROXY` for SSRF, empty `CONSOLE_API_URL`/`APP_API_URL`/`CHECK_UPDATE_URL`, `MARKETPLACE_ENABLED=false`.
  - 1.17 `POST .../workflows/draft` no longer accepts `environment_variables` (`extra_forbidden`). Use `environment_variable_patch`. Do not mix OCR tool loops into a text-PDF app via if-else; keep OCR as a separate published app. Multiple inbound edges to one LLM are a join stall. Product backends run the published graph, not draft.
  - 1.17 Console **GET** requires `X-CSRF-Token`. Unauthenticated `/` → 307 `/signin`. Agent Studio is `GET /agent`, not `/apps`. Skip `GET /version` (422 without a `query` shape).
  - Upgrade: merge compose (never replace a customized file), pin image digests, rolling `--no-deps --force-recreate`, wait for worker Alembic, never `down -v`. Rollback after migration is `pg_restore` both DBs. Do not enable workflow/conversation log cleanup by accident. Do not nginx-reload while `api_websocket` is down.
  - Web SSR needs `SERVER_CONSOLE_API_URL=http://api:5001`; browser `CONSOLE_API_URL`/`APP_API_URL` stay empty. `plugin-daemon` tag is independent of api/web.
  - Same physical vLLM: two Dify rows (`agent_thought_support` supported vs not). Fast path = not_supported + `/no_think`. Display `name` may lag `served-model-name`.
  - `/v1` file ACL is per app key + `user`. Uploading with app A then running app B → `Invalid upload file`.
  - 1.17.0: treat workspace Skill file upload, FastMCP OAuth, QA-segment answer PATCH, Agent Studio tool calling, and Human Input inside Loop as unstable. Demo on classic workflow + `/v1`.

### Notes
- Community edition only. RBAC / billing / some RAG publish endpoints 403 by design.
- Do not treat this tree as a frozen 1.17 snapshot until `v1.17.0` is released.
