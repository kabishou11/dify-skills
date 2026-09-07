# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Version numbers match **Dify**, not SemVer of this repo.

A frozen GitHub Release (`v1.17.0`) is created only when a Dify line is frozen. Until then everything lives on `main` under **Unreleased**. A **pre-release** may attach importable zips; that is not a freeze.

## 2026-09-07 — 发新版本禁止 delete-and-reimport（保住 api-key / test 记录）

- **apps-and-workflows**: 新增红线「NEVER delete-and-reimport to ship a new version」+ Publish checklist 第 8 项。`POST /apps/imports` 每次生成全新 `app_id`，而 Service API key、WebApp site、会话/运行日志（test 记录）、trigger 行都绑在旧 id 上——重导入即整体失联，表现为「每次发新版本 apikey 消失、test 记录没了」。正确做法是**同一 id 原地 draft 同步 + publish**；`ensure_app_key` 类 helper 必须先 GET 复用已有 key，不能重建。
- **service-api**: key 绑定的是 `app_id` 不是 DSL；交叉引用上述红线。

## 2026-09-06 — contract-tools 插件实战回灌（zhulei/contract-tools 0.1.4）

- **plugin-development**: 守护端 schema 校验细则（label/human_description 必须双语、含冒号值加引号、图标必须在 _assets、find|zip 打包防目录条目、manifest 需 runner/minimum_dify_version）；`model-selector` 复用 Dify 已配置模型实现插件零密钥（多模态消息构造示例）；File.blob 相对 `/files/` URL 修补；同 id 版本切换需卸载重装；PyMuPDF 中文渲染损坏 → pypdfium2。
- **plugin-install**: 上传字段名为 `pkg`；uninstall 端点与同 id 升级切换（symptom: 版本升级不生效）；plugin_daemon 重启窗口 `no available node`。
- **model-providers**: openai_api_compatible 能力标志陷阱（`document_support=support` 会发送 file 类型消息，多数网关 400 Invalid value: file）；`PUT models/credentials` 必须回传完整 api_key（GET 脱敏）。
- **troubleshooting**: 新增四条症状矩阵（渲染乱码/重启窗口/画布清单为空/版本不生效）。

## [Unreleased] — Dify 1.17.0

Working tree on `main`. **No frozen `v1.17.0` Release yet.** Preview zips may be published as `dify-1.17.0-skills-preview`.

### Added
- Dify 1.17 workspace Import packages: `scripts/package-dify-workspace.py` zips `skills/<name>/` with `SKILL.md` at the archive root into `dist/*.zip` (default: troubleshooting, compose-and-config, plugin-install, console-api).
- README: these are Agent Skills (`SKILL.md`) for operating self-hosted Dify Community 1.17 — not a substitute for in-app workspace Skills, but folders can be imported as drafts on the Skills page.

### Added (2026-09-01 field run, dify-server-01)
- **Files URL split**: `FILES_URL` = browser origin, `INTERNAL_FILES_URL` = container origin; browser downloads of tool files and plugin-fetching of Dify files are separate audiences (compose-and-config).
- **DSL proven facts 0.7.0**: `document-extractor` node name, unicode if-else operators, tool-parameter split by schema `form` (llm→`tool_parameters`, form→`tool_configurations`), `error_strategy` enum only `fail-branch|default-value`, SSE `draft/run`, KB `result` as JSON string, code-node chained JSON repair for LLM garbage (unescaped quotes, duplicated bare keys).
- **Knowledge-base 1.17 creation path**: `hierarchical_model` + `process_rule.mode: hierarchical` + `segmentation`/`subchunk_segmentation`; upload via `data_source`; node-level `multiple_retrieval_config.weights` must be rewritten on copy (empty results otherwise).
- **Model provider**: OpenAI-compatible per-model credential flow (`models/credentials` → `current_credential_id` → `models`), core-name vs display-name in default-model; plugin-level `add` needs `type: api-key`, key name from plugin yaml.
- **Plugin local patch pattern**: cwd source patches survive until the next upgrade; PaddleOCR VL refuses `outputFormats` (422). OCR fallback graph (default-value extractor → if-else text-layer threshold → OCR → clean LaTeX/img → merge).
- New-box **platform** tune (not custom tools): `dify-development` section 「新环境：Dify 平台基础配置」 plus compose-and-config tables (knob / clone-like example / recommend / why / recreate vs reload) covering workers/Celery/beat, timeout stack, uploads/413, workflow caps, sandbox, SSRF/NO_PROXY, Postgres/Redis, login/mail/marketplace, json-file logs, reverse-proxy URLs, and OpenAI-compatible wiring.
- Triggers (schedule/webhook/plugin), public `/triggers/webhook/{id}` (not `/webhook/{id}`), plugin Endpoint vs trigger, code-node sandbox timeouts.
- Agent Studio runtime (sandbox files, build-draft, snapshot timeout). Dataset metadata, child chunks, hit-test. Workflow/conversation logs and stats.
- `dify-compose-and-config`: 1.17 `.env` / `docker/envs` injection, workers, timeout stack, dual-plane workflow caps, nginx recreate vs reload, postgres/redis, mail, community login gates.
- README rewritten: problem map, mermaid diagrams, per-skill usage, Agent Skills install paths, maintainer contact.
- `scripts/install.sh` copies `skills/dify-*` into a target skills directory (`user` → `~/.agents/skills`, `project` → `./.agents/skills`, or `--dest`).

- Router plus 13 domain skills covering console, plugins, apps, knowledge, models, agents, service API, intranet, backup, troubleshooting, API catalog, and workspace extras (Skills, snippets, Agent roster, RAG pipeline, MCP).
- Routes scanned from Dify 1.17.0 `api/controllers` (console, `/v1`, WebApp `/api`, OpenAPI, MCP, inner API).

### Changed
- New-box scope is **Dify 1.17 Community itself**. Do not treat OpenAPI/PageIndex/MinerU-local/workflow-as-tool/pboc_dsl import as the platform checklist.
- Runtime vs files: customized compose often lists `environment:` or bind-mounts nginx/squid — `.env` and official `NGINX_*` can lie. Clone pitfalls documented: Celery autoscale to nproc, gunicorn 360 vs 7200, Loop on api only, plugin_daemon 50MiB vs api 500MiB, `CONSOLE_API_URL` on web, unpinned `:latest`.
- Host iron: one LLM :8001, Dense 27B **TP=4** ctx 262144, `--disable-custom-all-reduce`; obsolete “TP=1 / ctx 16384”; no MTP; no `compose down -v`; no unpinned `:latest`.
- OCR: reuse one published workflow-as-tool (`provider_type: workflow`); do not drop `langgenius/mineru` on every canvas. Plugin `parse-file` does not poll async MinerU `/file_parse` — fall back to OpenAPI submit/status/result + loop. End fields must not be named `text` (reserved). Code nodes cannot take File; optional file → if-else `not empty`. After OCR graph edits, publish then `workflow/update`.
- Triggers: no delay queue; `start` and `trigger-schedule` cannot share a graph (split ingest vs daily cron). Cron must be published. `draft/trigger/run` returns `waiting` until due — simulate with `draft/run` `inputs: {}` or `/v1/workflows/run`.
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
