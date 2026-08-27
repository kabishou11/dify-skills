---
name: Dify intranet
description: >-
  Use this when Dify is on an intranet or air-gapped box — internal models, SQL, HTTP, SSRF, no-egress plugin installs, avoid SaaS.
---
# Dify intranet

Use this when Dify sits on a private network or air-gapped host. Plugin packs: [Dify plugin install](sand-workflow:dify-plugin-install). Offline move: [Dify backup and upgrade](sand-workflow:dify-backup-and-upgrade).

## Defaults

- Prefer tools that talk to **your** HTTP / SQL / OpenAI-compatible / vLLM / Xinference / RAGFlow. Do not add SaaS search/crawler plugins.
- Marketplace is usually unreachable. Set `MARKETPLACE_ENABLED=false` and `CHECK_UPDATE_URL=` (empty) so the UI stops probing the public catalog.
- Leave `CONSOLE_API_URL` and `APP_API_URL` **empty** so the browser uses relative `/console/api` through nginx. Pointing them at `http://api:5001` makes the user's browser talk to a Docker DNS name.
- `NEXT_PUBLIC_SOCKET_URL` must be a URL the **browser** can reach (the public/intranet host, not `ws://localhost` and not the container hostname). Canvas sync uses `/socket.io/` → `api_websocket`.
- `INTERNAL_FILES_URL=http://api:5001` is for **plugin containers** previewing files, not for the browser.

## SSRF proxy (Squid)

HTTP nodes, OpenAPI tools, and external knowledge all go through Dify's SSRF proxy. Private `10.`/`192.168.`/`172.16.` targets often 502.

Fix in compose (must appear under the api `environment:` list, not only `.env`):

- Add the internal hosts to **`NO_PROXY`** (and `no_proxy`) alongside `localhost,127.0.0.1,api,...`.
- And/or `SSRF_PROXY_ALLOW_PRIVATE_IPS=true` if your threat model allows it.

Then recreate **api + worker**, `nginx -s reload`. Verify with `docker exec <api> printenv NO_PROXY`.

## Models

Point OpenAI-compatible at the internal base URL (`http://host:port/v1`). Display `name` in Dify can differ from vLLM `served-model-name` — see [Dify model providers](sand-workflow:dify-model-providers). MiniMax / cloud keys do not work offline; do not leave them as the workspace default.

## Knowledge

External KB endpoint is the **Dify adapter prefix** (RAGFlow: `http://ragflow:9380/api/v1/dify`). Dify appends `/retrieval`. Disable score_threshold — RAGFlow's `/dify/retrieval` has no reranker. Internal SQL datasets / HTTP-fetched docs beat SaaS crawlers.

## Plugins

Host-downloaded `.difypkg` + local PEP 503 index. Do not open container egress with iptables. Pack `plugin_packages/` + `cwd/` + `dify_plugin` dump when cloning the instance.

## Compose traps that look like "intranet bugs"

- `.env` keys not listed in compose `environment:` never reach the process.
- After recreate, nginx 502 until `nginx -s reload`.
- Plugin icons 503: dedicated nginx location for `/console/api/workspaces/current/plugin/icon`.
- `MILVUS_USER`/`MILVUS_PASSWORD` required when using Milvus.

## Do not

Put hostnames, IPs, passwords, or `SECRET_KEY` into skills or git. `DEPLOYMENT_EDITION=ENTERPRISE` does not unlock RBAC.
