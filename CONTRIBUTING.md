# Contributing

先开 issue，再发 PR。`main` 上的 HTTP / compose / `.env` 事实必须能在 **Dify Community 1.17** 上对得上，不要凭记忆改路由。

Open an issue first, then a PR. Facts on `main` must match Dify Community 1.17.

## 发 PR 之前

1. **先开 issue。** 说清楚：对准的 Dify 版本、你在哪台自托管实例上复现、改的是哪份 `skills/<name>/SKILL.md`。不要直接丢一个「我觉得路由错了」的 PR。
2. **1.17 事实要现场核对。** Console / plugin / workflow 相关条目，对照目标机器上的 `docker-compose`（或等价编排）和 `.env`，必要时再对 Dify 源码 `api/controllers`。compose 里列出的 `environment:` 或 bind-mount 可能覆盖 `.env`；不要只改文档里的建议值。
3. **不要编造 HTTP。** 新路径、payload、错误文案必须来自现场响应或源码，而不是模型补全。
4. **不要把密钥写进 git。** 密码、`SECRET_KEY`、API Key、内网主机名、业务 UUID 一律不要出现在 skill、issue 截图或 commit 里。
5. 改完跑：

```bash
python3 scripts/check-skills.py
```

若你改的是可导入检查清单，再打一次包确认 `SKILL.md` 仍在 zip 根目录：

```bash
python3 scripts/package-dify-workspace.py
unzip -l dist/dify-troubleshooting.zip
```

## Compatibility

Skills on `main` target the Dify version in [`VERSION`](VERSION). If you are writing against an older Dify, say so in the PR.

## Install

End users copy `skills/dify-*` with `scripts/install.sh`, or import a packaged zip on the Dify 1.17 Skills page. Do not add machine-specific paths to `SKILL.md`. Details: [README](README.md#安装).

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
- 1.17 Console **GET** needs `X-CSRF-Token`, not only POST.
- Do not invent HTTP. Confirm in Dify source `api/controllers` or a live `GET`.
- Field-test on a real box, then **generalize**: no secrets, no machine IPs, no app ids, no tenant UUIDs, no `/data/...` paths.
- Keep `DEPLOYMENT_EDITION=COMMUNITY`. Do not document pirated Enterprise flags.
- Intranet-capable tools first. Do not add SaaS search plugins unless the user asked.
- Keep each `SKILL.md` body ≤ 500 lines.

## Checks

```bash
python3 scripts/check-skills.py
python3 scripts/package-dify-workspace.py
```

## Releases

Do not tag a **frozen** GitHub Release (`v1.17.0`) from a PR. That tag is cut only when a Dify line is frozen; it equals that Dify version. A **pre-release** such as `dify-1.17.0-skills-preview` may attach importable zips while `main` is still unreleased — that is not a freeze and not a 1.0. See [README · 版本策略](README.md#版本策略).
