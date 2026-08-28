---
name: Dify intranet
description: >-
  Use this when Dify is on an intranet or air-gapped box — internal models, SQL, HTTP, SSRF, no-egress plugin installs, avoid SaaS.
---
# Dify intranet

Use this when Dify sits on a private network or air-gapped host. Plugin packs: [Dify plugin install](sand-workflow:dify-plugin-install). Offline move: [Dify backup and upgrade](sand-workflow:dify-backup-and-upgrade). Compose knobs: [Dify compose and config](sand-workflow:dify-compose-and-config).

## Defaults

- Prefer tools that talk to **your** HTTP / SQL / OpenAI-compatible / vLLM / Xinference / RAGFlow. Do not add SaaS search/crawler plugins.
- Marketplace is usually unreachable. Set `MARKETPLACE_ENABLED=false` and `CHECK_UPDATE_URL=` (empty) so the UI stops probing the public catalog.
- Leave `CONSOLE_API_URL` and `APP_API_URL` **empty** so the browser uses relative `/console/api` through nginx. Pointing them at `http://api:5001` makes the user's browser talk to a Docker DNS name.
- 1.17 **web SSR** still needs `SERVER_CONSOLE_API_URL=http://api:5001` (container-to-container). Missing → “Server console API URL is not configured” on first paint.
- `NEXT_PUBLIC_SOCKET_URL` must be a URL the **browser** can reach (the public/intranet host, not `ws://localhost` and not the container hostname). Canvas sync uses `/socket.io/` → `api_websocket`.
- `INTERNAL_FILES_URL=http://api:5001` is for **plugin containers** previewing files, not for the browser.

## SSRF proxy (Squid)

HTTP nodes, OpenAPI tools, and external knowledge all go through Dify's SSRF proxy. Private `10.`/`192.168.`/`172.16.` targets often 502.

`SSRF_PROXY_ALLOW_PRIVATE_IPS` is a **CIDR list**, not a boolean (`10.0.0.0/8,172.16.0.0/12,192.168.0.0/16`). Hostnames go in `SSRF_PROXY_ALLOW_PRIVATE_DOMAINS`. Recreate **ssrf_proxy** (entrypoint writes Squid ACLs).

Also add internal hosts to api+worker **`NO_PROXY`** / `no_proxy` (`localhost,127.0.0.1,api,...`). Recreate api+worker. Verify `docker exec <api> printenv NO_PROXY` and `docker exec <ssrf_proxy> printenv SSRF_PROXY_ALLOW_PRIVATE_IPS`.

## Models

Point OpenAI-compatible at the internal base URL (`http://host:port/v1`). Display `name` in Dify can differ from vLLM `served-model-name` — see [Dify model providers](sand-workflow:dify-model-providers). MiniMax / cloud keys do not work offline; do not leave them as the workspace default.

## Knowledge

External KB endpoint is the **Dify adapter prefix** (RAGFlow: `http://ragflow:9380/api/v1/dify`). Dify appends `/retrieval`. Disable score_threshold — RAGFlow's `/dify/retrieval` has no reranker. Internal SQL datasets / HTTP-fetched docs beat SaaS crawlers.

## Plugins

Host-downloaded `.difypkg` + local PEP 503 index. Do not open container egress with iptables. Pack `plugin_packages/` + `cwd/` + `dify_plugin` dump when cloning the instance.

## Compose traps that look like "intranet bugs"

- 1.17 api/worker/web load `.env` via env_file; nginx/ssrf/weaviate/db still need listed keys. See compose-and-config.
- After recreate, nginx 502 until `nginx -s reload` (and `api_websocket` must already be up).
- Plugin icons 503: dedicated nginx location for `/console/api/workspaces/current/plugin/icon`.
- `MILVUS_USER`/`MILVUS_PASSWORD` required when using Milvus.

## Do not

Put hostnames, IPs, passwords, or `SECRET_KEY` into skills or git. `DEPLOYMENT_EDITION=ENTERPRISE` does not unlock RBAC.
