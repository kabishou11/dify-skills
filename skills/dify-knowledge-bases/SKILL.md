---
name: Dify knowledge bases
description: >-
  Use this when creating Dify knowledge bases, uploading documents, tuning retrieval, or attaching datasets (including external RAGFlow).
---
# Dify knowledge bases

Use this when creating, filling, or attaching Dify datasets. External RAGFlow notes below. Prefixes: [Dify API catalog](sand-workflow:dify-api-catalog).

## Create

`POST /console/api/datasets` with `name`, `indexing_technique` (`high_quality` or `economy`), embedding model when high_quality. Attach to an app via the knowledge node `dataset_ids` (UUIDs of **this** instance — remap when copying DSL).

## Upload / index

- Console: `POST /console/api/datasets/{id}/documents` (file or text). Batch: `BATCH_UPLOAD_LIMIT` / `UPLOAD_FILE_BATCH_LIMIT`.
- Size: set **both** `UPLOAD_FILE_SIZE_LIMIT` and `NGINX_CLIENT_MAX_BODY_SIZE` in compose env (and nginx). 413 is almost always nginx.
- Segment: `INDEXING_MAX_SEGMENTATION_TOKENS_LENGTH`, `TOP_K_MAX_VALUE` (web+API; recreate **web** for the canvas cap). Size knobs: [Dify compose and config](sand-workflow:dify-compose-and-config).
- Status: `GET /console/api/datasets/{id}/documents`. Hit-test: retrieve endpoint on the dataset.
- `high_quality` without a working embedding provider → indexing stuck / empty recall.

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
