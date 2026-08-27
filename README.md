# Dify 1.17 operating skills

Operational skills for self-hosted Dify 1.17 (community). Start at [`skills/dify-development`](skills/dify-development/SKILL.md); it routes to the rest.

These files are Cursor/Grok Bot skills (`SKILL.md` with YAML frontmatter). They are not Dify workspace Skills.

## Layout

```
skills/
  dify-development/          router
  dify-api-catalog/          HTTP prefixes and auth
  dify-console-api/          login, CSRF
  dify-workspace-extras/     workspace Skills, snippets, Agent roster, RAG pipeline, MCP
  dify-plugin-install/
  dify-plugin-development/
  dify-apps-and-workflows/
  dify-knowledge-bases/
  dify-model-providers/
  dify-agents-and-tools/
  dify-service-api/
  dify-troubleshooting/
  dify-backup-and-upgrade/
  dify-intranet/
```

## Use

Copy a folder into your assistant's skills directory, or keep this repo as the source of truth and sync from it.

Do not commit Dify admin passwords, `SECRET_KEY`, or API keys.

Scanned against Dify 1.17.0 (`api/controllers`, 2026-08-27).
