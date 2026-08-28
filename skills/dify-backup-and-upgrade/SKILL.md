---
name: Dify backup and upgrade
description: >-
  Use this when backing up, restoring, or upgrading self-hosted Dify, or bringing it back after a host reboot.
---
# Dify backup and upgrade

Use this when backing up, restoring, upgrading, or moving a self-hosted Dify (including air-gap). Do not `compose down -v`.

## What must move together

Offline copies that "only brought images + compose" fail. Pack **all** of:

| Piece | Typical path | If missing |
|---|---|---|
| Images | `docker save` matching compose tags | cannot start |
| Compose + nginx | `docker-compose.yaml`, `nginx/` | cannot orchestrate |
| `.env` | includes **`SECRET_KEY`** | model/tool credentials will not decrypt |
| Postgres `dify` | volume or `pg_dump -Fc` | apps/workflows/datasets gone |
| Postgres `dify_plugin` | same | plugin install records gone |
| `volumes/plugin_daemon/plugin_packages/` | `.difypkg` blobs | plugins vanish |
| `volumes/plugin_daemon/cwd/` | plugin venvs | plugins reinstall from scratch |
| Vector store | weaviate / milvus volumes | RAG empty |
| App storage | `volumes/app/storage` | uploads gone |

`SECRET_KEY` must stay **byte-identical**. Changing it logs everyone out and blank-decrypts providers. Plugin-daemon / sandbox **tags may not match** the api/web tag — copy whatever compose currently pins.

## Postgres dump (prefer this over copying `volumes/db` live)

```bash
docker compose exec -T db_postgres pg_dump -U postgres -d dify -Fc > dify.dump
docker compose exec -T db_postgres pg_dump -U postgres -d dify_plugin -Fc > dify_plugin.dump
pg_restore --list dify.dump | head
```

## Air-gap pack / restore

1. `compose stop` api worker worker_beat web plugin_daemon (keep db up for dump, or stop all for volume tar).
2. `docker save` every image in compose (api, web, plugin_daemon, sandbox, agent_*, nginx, postgres, redis, vector, minio/etcd/squid if present).
3. Tar `volumes/plugin_daemon` `volumes/app` vector volumes redis as needed.
4. Copy compose + `.env` + nginx.
5. Target: `docker load`, lay volumes at the **same relative compose paths**, `compose up -d`, wait until api logs `Application startup complete`, then `nginx -s reload`.
6. Air-gap env: `MARKETPLACE_ENABLED=false`, `CHECK_UPDATE_URL=` empty. Point models at an internal OpenAI-compatible URL.

Low-RAM targets: drop `SERVER_WORKER_AMOUNT`, `CELERY_MAX_WORKERS`, `POSTGRES_SHARED_BUFFERS` — those often live in compose `command:` / listed env, not only `.env`.

## Reboot / nested VM

Start `dockerd` if needed, confirm storage-driver, `compose up -d`, `GET /console/api/setup`.

## Upgrade (pin a GitHub tag + digest, not `:latest` / `main`)

Heavily customized compose (custom vector image, `NO_PROXY`, loop/time caps, upload limits) must **not** be replaced with the official file. Merge new keys into yours.

1. Read release notes (1.17: `EDITION` → `DEPLOYMENT_EDITION`; keep `COMMUNITY`. Leaving a leftover `EDITION=` in `.env` is fine).
2. Backup: `pg_dump -Fc` **both** `dify` and `dify_plugin`, plus `.env`, compose, nginx, `volumes/app/storage`, `plugin_packages/`. Write a rollback note **before** you migrate.
3. Record current image **tags and digests** (`docker inspect --format '{{.RepoDigests}}'`). Pull the new tag (or `name@sha256:…` through a mirror). Never un-pinned `:latest`.
4. Merge new env keys. Do **not** turn on `WORKFLOW_LOG_CLEANUP_ENABLED` or `ENABLE_CONVERSATION_CLEANUP_TASK` unless the operator asked — 1.17 ships them off; flipping them deletes run history.
5. Prefer rolling recreate, not a stack bounce: `compose up -d --no-deps --force-recreate <svc>`. Recreate **api first** (Alembic). Workers log `Running migrations` for 1–2 minutes — do not kill them. Then websocket / worker / beat / web / plugin_daemon / agent_*. `plugin-daemon` tag is **independent** of api/web; bump it only when the notes say the old daemon breaks model plugins.
6. Never `compose down -v`. `compose down` (no `-v`) is a last resort; volumes stay, but you still lose in-flight runs.
7. After recreating api/web: `nginx -s reload`. Do **not** reload nginx while `api_websocket` is down (`host not found in upstream` → whole console 502).
8. Web 1.17 SSR needs `SERVER_CONSOLE_API_URL=http://api:5001` (container DNS). Leave `CONSOLE_API_URL` / `APP_API_URL` empty for the browser.
9. Verify: `/console/api/setup`, `/` (unauth 307 to signin is OK), `/socket.io/` not 308, login, provider decrypt, plugin list + `local runtime ready`, one dataset hit-test, one **published** `/v1` run (draft-only does not prove the product).

Cross major versions: do not skip (1.16 → last 1.x → 2.x). Plugins may not load.

## Rollback

If Alembic already ran, swapping images back is **not** enough.

1. `compose stop` api/websocket/worker/beat/web/plugin_daemon/agent_* (not `down -v`).
2. `dropdb` / `createdb` `dify` and `dify_plugin`, `pg_restore` both dumps.
3. Restore the old compose + `.env`.
4. `up -d --no-deps` those app containers on the **old** image ids.
5. `nginx -s reload`.

Mixing new images with an old schema (or the reverse) breaks the console.
