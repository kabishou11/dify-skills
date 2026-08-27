---
name: Dify knowledge bases
description: >-
  Use this when creating Dify knowledge bases, uploading documents, tuning retrieval, hit-testing, or attaching datasets (including external RAGFlow).
---
# Dify knowledge bases

Use this when creating, filling, hit-testing, or attaching Dify datasets. External RAGFlow notes below. Prefixes: [Dify API catalog](sand-workflow:dify-api-catalog).

## Create

```http
POST /console/api/datasets
{"name":"发票知识库","description":"","indexing_technique":"high_quality","permission":"only_me","provider":"vendor"}
```

`indexing_technique`: `high_quality` (needs embedding default) or `economy`. `permission`: `only_me` | `all_team_members` | `partial_members`. External KB: `"provider":"external"` plus `external_knowledge_api_id` / `external_knowledge_id`. Attach to an app via the knowledge node `dataset_ids` (UUIDs of **this** instance — remap when copying DSL).

List: `GET /datasets?keyword=&page=1&limit=20`. Detail/update/delete: `/datasets/{id}`.

## Upload / index

- Console: `POST /console/api/datasets/{id}/documents` (file or text). Batch: `BATCH_UPLOAD_LIMIT` / `UPLOAD_FILE_BATCH_LIMIT`.
- Size: set **both** `UPLOAD_FILE_SIZE_LIMIT` and `NGINX_CLIENT_MAX_BODY_SIZE` in compose env (and nginx). 413 is almost always nginx.
- Segment: `INDEXING_MAX_SEGMENTATION_TOKENS_LENGTH`, `TOP_K_MAX_VALUE` (web+API; recreate **web** for the canvas cap). Size knobs: [Dify compose and config](sand-workflow:dify-compose-and-config).
- Status: `GET /console/api/datasets/{id}/documents`. `high_quality` without a working embedding provider → indexing stuck / empty recall.

## Hit-test

Console (session):

```http
POST /console/api/datasets/{id}/hit-testing
{"query":"发票抬头怎么填","retrieval_model":{"search_method":"semantic_search","reranking_enable":false,"top_k":5,"score_threshold_enabled":false}}
```

`query` max 250 chars. `search_method`: `semantic_search` | `full_text_search` | `hybrid_search` | `keyword_search`. With rerank:

```json
{"query":"...","retrieval_model":{"search_method":"semantic_search","reranking_enable":true,"reranking_mode":"reranking_model","reranking_model":{"reranking_provider_name":"<provider>","reranking_model_name":"<display-name>"},"top_k":5,"score_threshold_enabled":false}}
```

Hybrid may set `weights`. Optional `attachment_ids`. Response `records[]` (segment, score, child_chunks). Empty records → embedding down, threshold too high, or dataset still indexing (`dataset_not_initialized`).

Service API (dataset key; same body): `POST /v1/datasets/{id}/hit-testing` **or** `POST /v1/datasets/{id}/retrieve`.

External KB:

```http
POST /console/api/datasets/{id}/external-hit-testing
{"query":"...","external_retrieval_model":{"top_k":5,"score_threshold":0,"score_threshold_enabled":false}}
```

## Retrieval in the canvas

Knowledge node + LLM: put `{{#context#}}` in the **system** prompt. Export the node's `result` (or `output`) from `end` if you need citations on a **workflow** app — only chatflow puts `retriever_resources` on `/v1/chat-messages`.

Rerank needs **four** fields: `provider` + `model` (UI) and `reranking_provider_name` + `reranking_model_name` (engine). Missing either pair → "Rerank 模型不能为空".

## External knowledge (RAGFlow and friends)

Dify POSTs `{endpoint}/retrieval`. The endpoint you save must **already include** `/dify` (or the vendor's adapter prefix):

- Right: `http://ragflow-host:9380/api/v1/dify`
- Wrong: `http://ragflow-host:9380/api/v1` (404)

RAGFlow `/dify/retrieval` returns **raw hybrid scores** (often 0.01–0.3). There is **no reranker** on that path. If Dify `score_threshold` is 0.5, every chunk is dropped. Set threshold **off or 0**; judge by recall/order, not the number.

SSRF: private RAGFlow URLs need `NO_PROXY` (see [Dify intranet](sand-workflow:dify-intranet)).

API key for the external KB is stored encrypted under `SECRET_KEY` — changing the key blanks it.

## Metadata / tags / segments

Dataset metadata, document segments, tags: console `/datasets/{id}/...`. Service API dataset keys can do the same under `/v1`.

## Move / copy

`dataset_ids` in DSL are UUIDs. After import on a new instance they still point at the old ids unless you remap. External KB configs are per-workspace, not inside the DSL.
