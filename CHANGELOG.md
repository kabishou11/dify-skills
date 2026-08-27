# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Version numbers match **Dify**, not SemVer of this repo.

A GitHub Release is created only when a Dify line is frozen. Until then everything lives on `main` under **Unreleased**.

## [Unreleased] — Dify 1.17.0

Working tree on `main`. **No GitHub Release yet.**

### Added
- Router plus 13 domain skills covering console, plugins, apps, knowledge, models, agents, service API, intranet, backup, troubleshooting, API catalog, and workspace extras (Skills, snippets, Agent roster, RAG pipeline, MCP).
- Routes scanned from Dify 1.17.0 `api/controllers` (console, `/v1`, WebApp `/api`, OpenAPI, MCP, inner API).

### Notes
- Community edition only. RBAC / billing / some RAG publish endpoints 403 by design.
- Do not treat this tree as a frozen 1.17 snapshot until `v1.17.0` is released.
