---
name: Dify backup and upgrade
description: >-
  Use this when backing up, restoring, or upgrading self-hosted Dify, or
  bringing it back after a host reboot.
---
# Dify backup and upgrade

Use this when backing up, restoring, or upgrading a self-hosted Dify, or after a host reboot.

## What to back up
From the compose `docker/` directory (never commit secrets):

- `.env` (and `envs/**/*.env` overrides)
- `docker-compose.yaml` **and** any `docker-compose.override.yaml`
- `volumes/` (postgres, redis, weaviate, app storage, plugin_daemon)
- generated secrets file if you keep one beside `.env`

```bash
cd "$DIFY_DOCKER"
sudo docker compose stop
tar -cvf "/backup/dify-volumes-$(date +%Y%m%d).tgz" volumes .env
sudo docker compose up -d
```

Do **not** `docker compose down -v`.

## Reboot / nested VM
1. Start `dockerd` if systemd did not (common on nested boxes).
2. Confirm storage-driver still matches `/etc/docker/daemon.json` (some environments need `fuse-overlayfs`).
3. `cd docker && sudo docker compose up -d`
4. Wait until `api` / `db_postgres` / `redis` healthy; `GET /console/api/setup`.

## Upgrade (tagged release only)
Do not track `main`. Pin a GitHub **tag** (example: `1.17.0`).

1. Read that tag's release notes (migrations, env renames).
2. Backup compose + `.env` + volumes.
3. `git fetch --tags && git checkout <tag>` (or unpack the release tarball).
4. Diff `.env.example` / `envs/*.env.example` into your `.env`. From 1.17.0: `EDITION` → **`DEPLOYMENT_EDITION`**. Keep `COMMUNITY`.
5. Re-apply override files (ports, plugin PyPI mirror, memory).
6. `docker compose up -d` (API runs migrations when `MIGRATION_ENABLED=true`).
7. If a release says so: `docker compose exec api uv run flask db upgrade` and plugin migration commands from that release — do not invent extra flask commands.

## Plugin daemon data
`volumes/plugin_daemon/` holds installed plugins, the local PyPI mirror, and uv cache. Back it up with volumes. After restore, if plugins fail to start, clear `cwd/.uv-cache/simple-v24` only — do not delete `plugin/` packages.

## Postgres
Default compose user/db are in `.env`. Changing `DB_PASSWORD` after first boot will not rotate the existing volume; keep the original or dump/restore.

## Rollback
Stop compose, restore the `volumes` tarball and the old `.env` + compose files, start again. Mixing a new image with an old DB without migrations (or vice versa) breaks the console.
