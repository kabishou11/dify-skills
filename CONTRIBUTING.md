# Contributing

## Compatibility

Skills on `main` target the Dify version in [`VERSION`](VERSION). If you are writing against an older Dify, say so in the PR.

## Install

End users copy `skills/dify-*` with `scripts/install.sh`. Do not add machine-specific paths to `SKILL.md`. Details: [README](README.md#安装).

## Skill format

Each skill is `skills/<id>/SKILL.md`:

```yaml
---
name: Human-readable name
description: >-
  Use this when … (one paragraph, used by the assistant to decide)
---
# Body
```

- `description` must start with **Use this when**.
- Prefer Console API over the browser. Give real paths and payloads.
- Do not invent HTTP. Confirm in Dify source `api/controllers` or a live `GET`.
- No secrets, no machine-specific paths (`/workspace/...`, `/home/box/...`).
- Keep `DEPLOYMENT_EDITION=COMMUNITY`. Do not document pirated Enterprise flags.
- Intranet-capable tools first. Do not add SaaS search plugins unless the user asked.

## Checks

```bash
python3 scripts/check-skills.py
```

## Releases

Do not tag or publish a GitHub Release from a PR. Releases are cut only when a Dify line is frozen; the tag equals that Dify version (`v1.17.0` for Dify 1.17.0). See [README · 版本策略](README.md#版本策略). Install paths for Cursor / Claude Code / Codex are in [README · 安装](README.md#安装).
