# Sprint Change Proposal — SmartASR 战略 Pivot

**日期：** 2026-03-04
**作者：** Bob（Scrum Master）
**项目：** SmartASR
**变更类型：** 重大（Major）— 战略定位轴转
**变更范围分类：** Major — 需要 PM / Architect 更新规划文档

---

## Section 1：问题陈述

### 触发背景

在执行 Phase 3 架构设计（step-03-stack）过程中，参照 Ollama 架构时发现：SmartASR 的核心价值不应是"Python 库 / 引擎 Protocol"，而应是"本地 ASR 运行时"——一个让任何开发者都能像用 Ollama 管理 LLM 一样管理 ASR 模型的工具。

随后完成市场调研（`market-research.md`）进一步验证：
- Ollama 官方明确 ASR 为 **Not planned**（Issue #7485），窗口期明确
- 所有现有竞品（faster-whisper-server、whisper.cpp server）提供了 API，**但无一实现模型管理体验**
- 全球开发者社区中对"可以 pull ASR 模型"的需求在 Ollama Issues 中白纸黑字

### 变更核心

| 维度 | 原 PRD 方向 | 新方向 |
|------|-----------|--------|
| **定位** | Python SDK / 引擎集成库 | 本地 ASR 运行时（Local AI Runtime） |
| **目标用户** | Python 开发者 | 所有开发者（任意语言通过 HTTP 接入） |
| **主接口** | `from smartasr import transcribe` | `smartasr serve` + `/api/transcribe` |
| **模型管理** | 无（用户自行处理） | `smartasr models pull/ls/rm`（CAS 存储） |
| **分发形式** | PyPI 包 | Docker 镜像（MVP）+ pip + 二进制（Roadmap） |
| **设计参照** | SpeechRecognition 现代化 | **Ollama** |

---

## Section 2：影响分析

### Epic 影响
**[N/A]** 项目尚在 Phase 3（规划阶段），无 Epic 被创建，无实施工作需回滚。

### 工件冲突

| 工件 | 状态 | 需要的动作 |
|------|------|----------|
| **PRD** | 🔴 冲突 | **编辑更新**——定位、MVP 范围、成功指标三处 |
| **Architecture** | 🟢 正确 | 已采用 Ollama 设计，**继续完成剩余步骤**即可 |
| **docs/**（棕地文档） | 🟡 过期 | 待架构确定后重新生成（Generate Project Context） |
| **现有代码（v0.1.0）** | 🟡 部分复用 | 引擎实现（FunASR/Qwen）可复用，外层结构需重构 |

### 技术影响

现有 v0.1.0 代码是 FastAPI monolith，符合新方向的部分：
- `engines/` — FunASR、Qwen 引擎实现可直接迁移
- STTEngine 接口抽象 — 作为内部引擎接口继续有效（如 Ollama 用 llama.cpp 作后端）

需要新增/重构的部分：
- `smartasr serve` 守护进程（引擎 keep_alive 生命周期管理）
- `~/.smartasr/` 用户目录 + CAS 存储（manifests + blobs）
- `smartasr models pull` 模型下载器（流式进度条，参照 ollama pull）
- ASRModelfile 解析器
- Python lib 客户端自动检测模式（embedded / HTTP）

---

## Section 3：推荐路径

**选择：Option 1 — 直接调整（Edit PRD + 完成 Architecture）**

**理由：**
1. 架构文档已经是正确方向，无需重做
2. PRD 核心洞察（协议反转、本地+云端统一、多源模型回退）仍然有效，只需调整定位语言和补充新 MVP 功能
3. 无实施工作需要回滚，风险极低
4. 参照系明确：Ollama。任何设计细节参照 Ollama 即可，无需反复决策

**风险评估：低**
- 唯一风险：Python 运行时的"守护进程"体验不如 Go 二进制流畅
- 缓解方案：MVP 阶段用 Docker 作为分发载体（`docker run smartasr serve`），长期再考虑二进制打包

---

## Section 4：具体变更提案

### 变更 A：更新 PRD 项目分类

**文件：** `_bmad-output/planning-artifacts/prd.md`

```
OLD:
| 项目类型 | Developer Tool / SDK Platform |
| 领域 | AI/ML Tooling — ASR 集成层 |
| 近期目标 | FunASR 完整链路跑通 + VAD 插拔框架就位 |
| 中期目标 | 引擎模板格式成为 ASR 集成社区标准 |
| 长期定位 | ASR 集成事实标准（FFmpeg 路径）；官方提供商适配 SmartASR 规范 |

NEW:
| 项目类型 | Local AI Runtime |
| 领域 | AI/ML Infrastructure — 本地 ASR 部署平台 |
| 近期目标 | smartasr serve + models pull + FunASR 完整链路跑通 |
| 中期目标 | 成为"本地 ASR 部署"的默认选择（开发者心智占领） |
| 长期定位 | ASR 生态基础设施（Ollama 路径）；厂商发布 SmartASR 兼容模型包 |
```

**理由：** 定位从"开发工具"升级为"运行时平台"，与 Ollama 坐标系一致。

---

### 变更 B：补充 MVP 范围

**文件：** `_bmad-output/planning-artifacts/prd.md`

```
在"MVP — v1.0 必须交付"中新增：

ADD:
- smartasr serve 守护进程
    - 引擎生命周期管理（keep_alive，默认 5m，参照 Ollama）
    - 后台运行，macOS launchd / Linux systemd 服务注册
- smartasr models 命令组
    - pull <model>    流式下载进度条（参照 ollama pull）
    - ls              本地已有模型列表（参照 ollama ls）
    - rm <model>      删除（参照 ollama rm）
    - show <model>    详情含 capabilities
- smartasr run <model>  交互转录模式（参照 ollama run）
- ASRModelfile          模型配置文件格式（参照 Ollama Modelfile）
- ~/.smartasr/ 用户目录
    - config.yaml     全局配置（API Key、默认引擎、keep_alive）
    - models/manifests/  模型清单（CAS 索引）
    - models/blobs/      内容寻址存储（sha256，多引擎共享）
- REST API /api/* 路由（参照 Ollama /api/*，非 /v1/）
    - POST /api/transcribe      同步转录
    - POST /api/transcribe/async 异步任务
    - GET  /api/models          本地模型列表
    - GET  /api/models/available 全部三态列表
    - POST /api/models/pull     流式下载
    - GET  /api/engines/ps      已加载引擎状态
- Docker 官方镜像（MVP 主要分发方式）

DEFER to v1.1+:
- OpenAI Whisper API 兼容层（/v1/audio/transcriptions）
- smartasr 二进制单文件分发
```

---

### 变更 C：更新 Executive Summary 定位语言

**文件：** `_bmad-output/planning-artifacts/prd.md`

```
OLD 第一句：
SmartASR 是一个面向开发者的开源 ASR（自动语音识别）集成底层库。

NEW:
SmartASR 是一个本地 ASR 运行时，让任何开发者都能像用 Ollama 管理大语言模型
一样，在本地管理和运行 ASR 模型——一条命令拉取模型、一行 API 开始转录、
任意语言的客户端通过 HTTP 接入。
```

---

### 变更 D：补充成功指标

**文件：** `_bmad-output/planning-artifacts/prd.md`

```
在"Measurable Outcomes"表中新增：

| smartasr models pull SenseVoiceSmall → 首次转录 | < 3 分钟 |
| 非 Python 语言（如 Node.js）通过 HTTP API 完成转录 | 零额外配置 |
| Docker 一键部署：docker run smartasr serve | < 5 分钟 |
```

---

## Section 5：实施交接

### 变更范围分类：**Major**

- PRD 是规划阶段核心文档，其定位变更需要 PM（John）审批和更新
- Architecture 需要 Architect（Winston）继续完成剩余步骤

### 交接计划

| 角色 | 动作 | 工具 |
|------|------|------|
| **PM（John）** | 执行上述 A/B/C/D 四处 PRD 变更 | `/bmad-bmm-edit-prd` |
| **Architect（Winston）** | 继续完成 Architecture 文档剩余步骤 | `/bmad-bmm-create-architecture`（resume） |
| **SM（Bob）** | Architecture 完成后执行 Epic/Story 创建 | `/bmad-bmm-create-epics-and-stories` |

### 成功标准

- [ ] PRD Executive Summary 反映 Ollama-style runtime 定位
- [ ] PRD MVP 范围包含 serve 守护进程、models 命令组、ASRModelfile
- [ ] Architecture 文档所有步骤完成（当前：3/N）
- [ ] PRD 与 Architecture 无方向冲突（可执行 `/bmad-bmm-check-implementation-readiness` 验证）

---

*由 Correct Course 工作流生成 | BMAD Method*
