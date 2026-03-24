# SmartASR — 棕地上下文文档索引

> 由 document-project 工作流（BMAD）生成 | 扫描级别: exhaustive | 生成日期: 2026-03-02
>
> **用途：** 为 AI 编码助手（Claude/Copilot/Cursor 等）提供项目上下文，
> 支持 Sprint 规划、架构决策、代码生成和 Story 实现。

---

## 文档目录

### 核心上下文文档（优先阅读）

| 文档 | 路径 | 说明 |
|------|------|------|
| **项目概述** | [project_overview.md](./project_overview.md) | 项目定位、核心概念、快速开始 |
| **架构文档** | [architecture.md](./architecture.md) | 系统架构图、数据流、设计决策 |
| **技术栈** | [tech_stack.md](./tech_stack.md) | 所有技术依赖、版本、用途说明 |
| **API 契约** | [api_contracts.md](./api_contracts.md) | 完整 REST API 端点、DTO、错误码 |
| **源码目录树** | [source_tree.md](./source_tree.md) | 含注释的文件树、模块边界说明 |
| **开发运营** | [dev_ops.md](./dev_ops.md) | 安装、运行、测试、添加引擎指南 |

### 工作流状态

| 文档 | 路径 | 说明 |
|------|------|------|
| **扫描状态** | [project-scan-report.json](./project-scan-report.json) | 断点续传状态文件 |

---

## 项目快速摘要

```
项目：SmartASR
版本：0.1.0 (Alpha)
类型：单体仓库（Python 后端 + 静态 Web 前端）
语言：Python 3.10+（主）/ JavaScript（前端）
框架：FastAPI + Uvicorn + Typer
许可：MIT
```

**三句话描述：**
SmartASR 是一个统一的语音识别服务，通过插件化引擎架构支持 FunASR 本地引擎和通义千问云端引擎。
提供 REST API（FastAPI）和 CLI 工具（Typer），共享同一 STT Service Layer。
核心服务层可独立嵌入其他 Python 项目使用。

---

## Agent 职责索引（迅捷开发用）

以下是为 Sprint 开发规划的 Agent 职责边界：

| Agent | 负责目录/文件 | 主要接口 |
|-------|-------------|---------|
| **Dev-API** | `backend/app/api/` | FastAPI 路由、Pydantic 响应模型 |
| **Dev-STT-Core** | `backend/app/services/stt/`（非 engines） | BaseSTTEngine、DTO、Registry、Config |
| **Dev-Engine-Local** | `backend/app/services/stt/engines/ali_funasr.py` | FunASREngine（implements BaseSTTEngine） |
| **Dev-Engine-Cloud** | `backend/app/services/stt/engines/ali_qwen.py` | QwenASREngine（implements BaseSTTEngine） |
| **Dev-CLI** | `backend/app/cli/` | CLI 命令、输出格式化器 |
| **Dev-Frontend** | `frontend/` | Web UI、Fetch API 调用 |
| **Dev-QA** | `tests/` | pytest 测试套件 |

**跨域规则：**
- 每个 Dev Agent 只能修改自己负责的目录
- 接口变更必须通知相关 Agent（Architect 审批）
- 引擎插件只能导入 `stt/` 内部模块，不能导入 `api/` 或 `cli/`

---

## 关键文件快速导航

| 需要做的事 | 去哪里看 |
|-----------|---------|
| 了解项目是什么 | `README.md` / `docs/project_overview.md` |
| 理解系统架构 | `docs/architecture.md` |
| 查看 API 端点 | `docs/api_contracts.md` |
| 找到某个文件 | `docs/source_tree.md` |
| 添加新引擎 | `docs/dev_ops.md` + `backend/app/services/stt/engines/_template.py` |
| 运行测试 | `docs/dev_ops.md` + `tests/README.md` |
| 查看 TODO | `TODO.md`、`TODO-milestones.md`、`TODO-api.md` 等 |
| VAD 插件化计划 | `documents/【计划】vad-plugin/vad-plugin-plan.md` |

---

## 已有原始文档（非 AI 生成）

以下文档由开发者手工维护，是设计意图的权威来源：

| 文档 | 路径 |
|------|------|
| 后端架构说明 | `backend/README.md` |
| API 说明 | `backend/app/api/README.md` |
| CLI 使用文档 | `backend/app/cli/README.md` |
| STT 库文档 | `backend/app/services/stt/README.md` |
| 引擎开发指南 | `backend/app/services/stt/engines/README.md` |
| 架构设计（原始） | `documents/design/architecture.md` |
| 快速开始 | `documents/guides/quickstart.md` |
| 嵌入式使用 | `documents/guides/embedding.md` |
| 引擎指南 | `documents/guides/engines.md` |
| 模型下载 | `documents/guides/model-download.md` |
| 许可证合规 | `COMPLIANCE.md` |
| AI 协作规范 | `AGENTS.md` |
| VAD 插件计划 | `documents/【计划】vad-plugin/` |

---

## 文档生成信息

```
workflow:     document-project
scan_level:   exhaustive
mode:         initial_scan
generated_by: Analyst Mary (BMAD document-project workflow)
files_read:   ~40 个源文件
duration:     全量扫描
```

---

*如需更新此文档，运行：`document-project 工作流（选择 resume 模式）`*
