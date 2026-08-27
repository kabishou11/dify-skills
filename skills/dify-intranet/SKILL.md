---
name: Dify intranet
description: >-
  Use this when Dify is on an intranet or air-gapped box — internal models, SQL,
  HTTP, SSRF, no-egress plugin installs, avoid SaaS.
---
# Dify intranet

Use this when the Dify box sits on a private network, containers cannot reach the public internet, or the user wants tools that work without SaaS keys.

## Decision tree
1. **Need a model?** Configure `openai_api_compatible` / vLLM / Xinference with an **internal base URL**. Do not start with `api.openai.com`.
2. **Need HTTP to an internal service?** Built-in **HTTP Request** node. If it fails to `10.`/`172.`/`192.168.`, add that CIDR to `SSRF_PROXY_ALLOW_PRIVATE_IPS` and restart api/worker.
3. **Need code?** Built-in **Code** node (sandbox). Optional local sandbox plugin only if they asked.
4. **Need SQL / Redis / files / SSH / mail?** Plugins: `db_query` / `database` / `db_client_node` / `sqlite` / `eft/redis` / excel+pdf+md_exporter / `stvlynn/ssh|sftp` / `langgenius/email`. Point at internal hosts.
5. **Need RAG?** Local dataset + intranet embedding, or external KB plugin (e.g. RAGFlow API) to an internal RAGFlow.
6. **Need search?** Self-host SearXNG and use `langgenius/searxng`. Do not add Tavily/Google unless asked.
7. **Need ASR?** `langgenius/funasr` against a local SenseVoice/FunASR server.

## Plugin install on a no-egress daemon
Follow [Dify plugin install](sand-workflow:dify-plugin-install): host downloads `.difypkg`, local PEP 503 index for uv, never iptables to "fix" egress.

## Files inside Docker
Set `INTERNAL_FILES_URL=http://api:5001` so plugin_daemon can fetch uploads. Humans still need a browser-reachable `FILES_URL` (often empty → auto from request on single-domain nginx).

## What not to add
Cloud web search, weather, stocks, hosted crawl (Firecrawl/Jina) — fine if already installed, do not pile more on. Tongyi/Zhipu/Moonshot/Minimax need vendor keys; only add when the user has keys or an internal gateway that pretends to be them.

## Sanity
`curl` the internal model/SQL endpoint **from the api container** (`docker compose exec api wget -qO- ...`) as well as from the host. Host-ok / container-fail is DNS or SSRF, not a wrong API key.
