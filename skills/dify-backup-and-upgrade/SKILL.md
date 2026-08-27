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

## Upgrade (pin a GitHub tag, not `main`)

1. Read release notes (env renames: 1.17 `EDITION` → `DEPLOYMENT_EDITION`). Keep `COMMUNITY`.
2. Backup dumps + `.env` + compose + storage.
3. Record current image tags.
4. Pull/load new images. **Merge** new compose/env keys into yours — do not blindly overwrite custom `UPLOAD_*`, `NO_PROXY`, worker counts, nginx.
5. `compose down` then `up -d`. Watch api for migrations. `plugin-daemon` tag may stay if the notes say so.
6. Reload nginx. Hit `/console/api/setup`, `/`, and `/socket.io/` (not 308).
7. Log in, check providers still decrypt, plugin list, one dataset hit-test, one draft run.

Cross major versions: do not skip (1.16 → last 1.x → 2.x). Plugins may not load.

## Rollback

Stop new compose. Restore old compose + `.env`. If migrations ran: `dropdb`/`createdb` + `pg_restore` both databases, then `up -d` on the old images. Mixing new images with an old schema (or the reverse) breaks the console.
