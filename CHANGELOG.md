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
- Folded generic lessons from 1.16.1 production ops into the 1.17 skills (no host secrets, IPs, or app ids):
  - Service API file ACL: same key + same stable `user`; file input is one object; prefer `blocking` with HTTP timeout ≥ 600s; `/v1/chat/completions` is often 404.
  - 1.17 api/worker/web load `.env` via `env_file`; nginx/ssrf/weaviate/db still need listed keys. `SSRF_PROXY_ALLOW_PRIVATE_IPS` is a CIDR list, not `true`. Canvas sync is Socket.IO `/socket.io/`.
  - Offline pack must include images, compose, `.env` (`SECRET_KEY`), both `dify` and `dify_plugin` dumps, `plugin_packages/`, `cwd/`, and vector volumes.
  - RAGFlow endpoint is `.../api/v1/dify` (Dify appends `/retrieval`); disable score_threshold because that path has no reranker.
  - DSL: `GET /app-dsl-version` (1.17 = `0.7.0`); every node needs top-level `type: custom`; Loop `break_conditions` need `id`+`varType` on loop vars; rerank needs four name fields; tools use OpenAPI `operationId`.
  - Intranet: `NO_PROXY` for SSRF, empty `CONSOLE_API_URL`/`APP_API_URL`/`CHECK_UPDATE_URL`, `MARKETPLACE_ENABLED=false`.

### Notes
- Community edition only. RBAC / billing / some RAG publish endpoints 403 by design.
- Do not treat this tree as a frozen 1.17 snapshot until `v1.17.0` is released.
