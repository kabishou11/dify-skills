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

**QA segments.** 1.17.0 has a bug where updating a QA pair via API can **wipe `answer`**. Do not batch-PATCH QA answers until a patch; edit in the UI or wait.

Hit-test (`/hit-testing`) does **not** apply canvas metadata filters. To verify department isolation, run the knowledge-retrieval **node** (draft/run), not hit-test.

## Move / copy

`dataset_ids` in DSL are UUIDs. After import on a new instance they still point at the old ids unless you remap. External KB configs are per-workspace, not inside the DSL.

## 1.17 creation path (validated end-to-end)

- `doc_form` enum is `text_model` / `qa_model` / **`hierarchical_model`** (old `parent_model` → *Invalid doc_form*).
- `process_rule.mode`: `automatic` | `custom` | **`hierarchical`** (parent-child). Rules shape changed:
  `rules.parent_mode` (`paragraph`/`full-doc`) + `rules.segmentation` (parent: `separator`/`max_tokens`/`chunk_overlap`) + `rules.subchunk_segmentation` (child) — do not nest `parent_chunk`/`child_chunk` under segmentation (pydantic rejects with `max_tokens Field required`).
- Upload: `POST /console/api/datasets/{id}/documents` with a JSON body `{data_source: {info_list: {data_source_type: upload_file, file_info_list: {file_ids: [id]}}}, ...}` after `POST /console/api/files/upload`. There is **no** `create-by-text` console route in 1.17 (404) and plain-text body fails with `Data source is required`.
- `embedding_model` on create/upload must match an active row; a broken provider (e.g. 1113/1308 quota errors) leaves `indexing_status: error` — the dataset id stays valid, delete the failed document and re-upload after fixing the provider (no retry endpoint needed).
- Hybrid weights in `retrieval_model` for dataset create use the `{[{type: semantic|keyword, value}]}` shape at dataset level; workflow **node** `multiple_retrieval_config.weights` uses `{vector_setting: {embedding_provider_name/embedding_model_name/vector_weight}, keyword_setting: {keyword_weight}}` — the node config must be rewritten on import or the box's embeddings are silently never used (empty results).
- Parent-child hit-test returns `segment` (child) with `parent` attached; `child_chunks` included in workflow retrieval results.
