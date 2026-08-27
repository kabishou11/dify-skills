---
name: Dify knowledge bases
description: >-
  Use this when creating Dify knowledge bases, uploading documents, tuning
  retrieval, or attaching datasets (including external RAGFlow).
---
# Dify knowledge bases

Use this when creating datasets, uploading docs, tuning retrieval, or attaching knowledge to an app. Models first: [Dify model providers](sand-workflow:dify-model-providers). RAG **pipeline** canvas: [Dify workspace extras](sand-workflow:dify-workspace-extras).

## Create
`POST /console/api/datasets` with:

- `name`
- `indexing_technique`: `high_quality` (embeddings) or `economy` (keyword only)
- embedding provider + model (required for `high_quality`)
- retrieval: vector / keyword / hybrid; optional rerank model
- permission: workspace vs only me

List `GET /datasets`. One: `GET/PATCH/DELETE /datasets/{id}`. `GET .../use-check`, `.../related-apps`, `.../indexing-status`, `.../error-docs`, `.../queries`.

No embedding configured → high_quality create/index fails. Hit-test before wiring an app: `POST /datasets/{id}/hit-testing`. External: `POST .../external-hit-testing`. Retrieval defaults: `GET /datasets/retrieval-setting`.

## Documents
`POST /datasets/{id}/documents` — upload, raw text, or crawl. Init empty: `POST /datasets/init`.

- Rules: `GET /datasets/process-rule` (`automatic` vs `custom` chunk size / overlap / separators). Chinese: smaller chunks than English prose if using character/GSE tokenization.
- Status: `GET /datasets/{id}/documents/{doc_id}/indexing-status` or `.../batch/{batch}/indexing-status`
- Pause / resume: `PATCH .../documents/{doc_id}/processing/pause` and `.../resume`. Batch status: `PATCH .../documents/status/{action}/batch`. Retry: `POST .../retry`. Rename: `POST .../rename`.
- Download: `GET .../documents/{doc_id}/download`, zip `.../documents/download-zip`.
- Pipeline log: `GET .../documents/{doc_id}/pipeline-execution-log`. Summary: `POST .../documents/generate-summary`.

## Segments (console)
`GET /datasets/{id}/documents/{doc_id}/segments`. Add: `POST .../segment`. Patch one: `PATCH .../segments/{segment_id}`. Batch enable/disable: `PATCH .../segment/{action}`. Batch import: `POST .../segments/batch_import`. Child chunks: `POST .../segments/{segment_id}/child_chunks`, delete `.../child_chunks/{id}`.

Metadata: `POST /datasets/{id}/metadata`, `PATCH .../metadata/{id}`, built-in `GET /datasets/metadata/built-in`, bind on docs `POST .../documents/metadata`.

## In an app
Chatflow/workflow: **Knowledge retrieval** node → dataset ids, top_k, score, rerank. Basic chat: attach in `model-config`.

External KB (intranet RAGFlow, custom HTTP, Bedrock): install the plugin, then `GET/POST /datasets/external-knowledge-api` and create an **external** dataset (`/datasets/external`). Example plugin id `witmeng/ragflow-api`.

## RAG pipeline
For a visual ingest graph (datasource → process → index), do **not** only POST `/datasets`. Use `/rag/pipeline/dataset` or `/rag/pipeline/empty-dataset`, then the `/rag/pipelines/{id}/workflows/draft` loop in workspace extras. Publish may 403 on community (`knowledge_pipeline.publish_enabled`). Convert an existing dataset: `POST /rag/pipelines/transform/datasets/{dataset_id}`.

Website crawl: `POST /website/crawl`, poll `GET /website/crawl/status/{job_id}`. Notion: `/data-source/integrates`, `/notion/pre-import/pages`.

## Chinese / Weaviate
On compose Weaviate: `WEAVIATE_TOKENIZATION=character` and `WEAVIATE_ENABLE_TOKENIZER_GSE=true` help CJK. Embedding model must also be CJK-capable.

## Size / parsers
Capped by `UPLOAD_FILE_SIZE_LIMIT` **and** `NGINX_CLIENT_MAX_BODY_SIZE` — raise both. PDFs: MinerU plugin or Unstructured (`ETL_TYPE`). 413 = nginx, not the dataset API.

## Service ingest
Dataset API key (`GET/POST /datasets/api-keys`, per-dataset `/datasets/{id}/api-keys`) + `POST /v1/datasets/{id}/document/create-by-file` (or create-by-text). See Dify service API.
