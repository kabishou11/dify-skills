# Dify Operating Skills

[![Dify](https://img.shields.io/badge/Dify-1.17.0-1C64F2)](https://github.com/langgenius/dify)
[![Status](https://img.shields.io/badge/release-unreleased-lightgrey)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Self-hosted [Dify](https://github.com/langgenius/dify) 的可执行操作技能。给 Cursor / Grok Bot 这类助手用，不是 Dify 控制台里的「工作区 Skills」。

**当前跟踪：Dify 1.17.0（Community）。`main` 就是这条最新线。稳定 Release 还没有打。**

English: executable skills for operating self-hosted Dify. `main` always tracks the newest Dify. Each GitHub Release will pin one Dify version. No release has been published yet.

---

## Versioning

| 位置 | 含义 |
| --- | --- |
| [`VERSION`](VERSION) | 这份树当前对准的 Dify 版本和是否冻结 |
| `main` | **最新 Dify**。会继续改，不保证接口叙述冻结 |
| GitHub Release `vX.Y.Z` | 针对 **Dify `X.Y.Z`** 的稳定快照。一个 Dify 版本对应一个稳定 Release |

规则：

1. 版本号跟 Dify 走，不跟本仓库自己的 SemVer 走。Dify 出 `1.17.0`，稳定技能就是 `v1.17.0`。
2. 同一条 Dify 线只在冻结时打一次稳定 Release。补丁（例如 Dify `1.17.1`）再出 `v1.17.1`。
3. **现在不能创建 Release。** 1.17 仍在 `main` 上打磨，状态是 `unreleased`。
4. 不要把 `main` 上的提交当成已发布契约。要用冻结内容，等对应 Release。

```
main          ── 最新 Dify（现在 1.17.0，未冻结）
                  │
                  ▼  冻结后才打
v1.17.0       ── 对应 Dify 1.17.0 的稳定技能（尚未发布）
v1.18.0       ── 对应未来的 Dify 1.18.0
```

---

## 这套技能做什么

对照 Dify 1.17 源码 `api/controllers` 写成的操作手册：真实路径、鉴权、payload、失败模式。助手按 [dify-development](skills/dify-development/SKILL.md) 分流，不要自己编 HTTP。

覆盖：

- 控制台登录（Base64 密码 + CSRF）
- 插件安装 / 离线 uv
- 应用、工作流、DSL、触发器
- 知识库、RAG Pipeline、外挂知识库
- 模型供应商（OpenAI 兼容、vLLM、Xinference、通义）
- Agent 应用、工具、Agent Studio 花名册
- 工作区 Skills、Snippet、MCP、插件 Endpoint
- Service API `/v1`、WebApp `/api`、OpenAPI
- 内网 / 无外网
- 备份升级与排错

社区版限制按官方 env 调，不伪装 Enterprise。`/rbac`、`/billing`、部分 RAG 发布在社区版 403 是功能开关，不是 CSRF 坏了。

---

## Skills

从 [dify-development](skills/dify-development/SKILL.md) 进。

| Skill | 何时用 |
| --- | --- |
| [dify-development](skills/dify-development/SKILL.md) | 任何 Dify 工作的入口 / 分流 |
| [dify-api-catalog](skills/dify-api-catalog/SKILL.md) | 查前缀和鉴权：`/console/api`、`/v1`、`/api`、`/openapi/v1`、MCP、inner |
| [dify-console-api](skills/dify-console-api/SKILL.md) | 登录、CSRF、用控制台 API 操作实例 |
| [dify-plugin-install](skills/dify-plugin-install/SKILL.md) | 安装 / 修复 Marketplace 插件，含离线与 uv 失败 |
| [dify-plugin-development](skills/dify-plugin-development/SKILL.md) | 写、打包、调试 `.difypkg` |
| [dify-apps-and-workflows](skills/dify-apps-and-workflows/SKILL.md) | 应用、chatflow、workflow、DSL、画布发布 |
| [dify-knowledge-bases](skills/dify-knowledge-bases/SKILL.md) | 知识库、切片、召回、外挂 RAGFlow |
| [dify-model-providers](skills/dify-model-providers/SKILL.md) | LLM / embedding / rerank / ASR / vLLM |
| [dify-agents-and-tools](skills/dify-agents-and-tools/SKILL.md) | Agent 应用、工具、OpenAPI / workflow-as-tool |
| [dify-workspace-extras](skills/dify-workspace-extras/SKILL.md) | 工作区 Skills、Snippet、Agent 花名册、RAG Pipeline、MCP |
| [dify-service-api](skills/dify-service-api/SKILL.md) | 已发布应用的 `/v1`、API Key、WebApp |
| [dify-intranet](skills/dify-intranet/SKILL.md) | 内网、SSRF、无外网装插件、避免 SaaS |
| [dify-troubleshooting](skills/dify-troubleshooting/SKILL.md) | 登录、插件、模型、RAG、上传、容器失败 |
| [dify-backup-and-upgrade](skills/dify-backup-and-upgrade/SKILL.md) | 备份、恢复、升级、重启后拉起 |

---

## 使用

把需要的目录拷进助手的 skills 目录（本仓库每个子目录一份 `SKILL.md`）：

```bash
git clone https://github.com/kabishou11/dify-skills.git
cp -R dify-skills/skills/dify-* /path/to/your/skills/
```

或把本仓库当源，自己同步。不要提交 Dify 管理员密码、`SECRET_KEY`、应用 / 数据集 API Key。

跑质量检查：

```bash
python3 scripts/check-skills.py
```

---

## 稳定约定

1. **不编造路由。** 以 Dify 源码 `api/controllers` 和现场 `GET` 为准。
2. **前缀分清。** 控制台是 `/console/api`（Cookie + `X-CSRF-Token`）；已发布调用是 `/v1`（Bearer）。不要混用。
3. **密码是 Base64，不是 RSA。** 明文登录会 `401 Invalid encrypted data`。
4. **插件以 daemon 为准。** `plugin/list` 有名字不够，还要 `local runtime ready`。
5. **内网优先。** 能走内网模型 / SQL / HTTP 的，不要默认堆云搜索 SaaS。
6. **社区版就是社区版。** 不要设 `DEPLOYMENT_EDITION=ENTERPRISE` 来「解锁」。

完整变更见 [CHANGELOG](CHANGELOG.md)。贡献方式见 [CONTRIBUTING](CONTRIBUTING.md)。
