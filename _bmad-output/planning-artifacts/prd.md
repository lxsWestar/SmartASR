---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain-skipped', 'step-06-innovation', 'step-07-project-type']
inputDocuments:
  - 'docs/index.md'
  - 'docs/project_overview.md'
  - 'docs/architecture.md'
  - 'docs/tech_stack.md'
  - 'docs/api_contracts.md'
  - 'docs/source_tree.md'
  - 'docs/dev_ops.md'
  - 'TODO.md'
  - 'TODO-milestones.md'
  - 'TODO-api.md'
  - 'TODO-future.md'
  - 'TODO-vad.md'
  - 'TODO-model-loading.md'
workflowType: 'prd'
documentCounts:
  briefs: 0
  research: 0
  brainstorming: 0
  projectDocs: 7
  todoFiles: 6
projectType: 'brownfield'
classification:
  projectType: 'developer_tool_sdk_platform'
  domain: 'ai_ml_tooling'
  complexity: 'medium'
  projectContext: 'brownfield'
  differentiators:
    - '本地+云端 ASR 统一抽象层（无现成开源替代品）'
    - 'lib + CLI + REST API 三合一暴露'
    - '模型来源三层回退（本地目录→内网服务器→官方Hub）'
    - '中国生态原生支持（FunASR、ModelScope、Qwen-ASR）'
prdMode: 'streamlined'
---

# Product Requirements Document - SmartASR

**Author:** lsc
**Date:** 2026-03-02

---

## Executive Summary

SmartASR 是一个本地 ASR 运行时（Local ASR Runtime），让任何开发者都能像用 Ollama 管理大语言模型一样，在本地管理和运行 ASR 模型——一条命令拉取模型、一行 API 开始转录、任意语言的客户端通过 HTTP 接入。它统一了本地 ASR 模型（FunASR、SenseVoiceSmall 等）和云端 ASR 服务（Qwen-ASR、DashScope 等）的使用体验，通过守护进程（`smartasr serve`）、CLI 工具、REST API 和 Python 库四种形式暴露，使任何项目都能以最小接入成本使用任意 ASR 能力。

**目标用户：** 任何需要在本地或私有环境运行 ASR 能力的开发者——无论使用 Python、Node.js、Go 还是其他语言；以及需要私有化部署语音识别服务的企业用户（金融、医疗、政务等数据不出境场景）。

**核心问题：** ASR 能力高度分散——本地模型、云端 API 各自接入方式不同，无统一抽象；现有方案（SpeechRecognition 等）设计过时，不支持服务化、不支持异步任务、不支持模型来源管理，且对中国生态（FunASR、ModelScope）原生支持缺失。

**项目定位：** 本地 ASR 运行时平台，设计参照 Ollama。核心价值是**模型管理体验**（pull/run/serve）和**统一 HTTP 接口**，使任意语言的项目都能通过标准 API 接入 ASR 能力。内部引擎接口（`STTEngine` Protocol）作为插件契约，供引擎开发者使用；长期目标：ASR 提供商发布 SmartASR 兼容模型包，如同 Ollama 生态中厂商发布 GGUF 模型一样。

### What Makes This Special

**市场空白：** 无任何现有开源项目同时实现「本地+云端统一抽象 + lib/CLI/API 三形态暴露 + 可插拔引擎注册表 + 多源模型管理」的完整组合。

**核心差异点：**
- **引擎规范优先：** 基于 `typing.Protocol` 的 `STTEngine` 接口构成公开约定，任何语言/平台均可实现兼容引擎，无需继承 SmartASR 基类
- **三形态统一：** 同一核心代码路径，`pip install` 作库用、`smartasr transcribe` 作 CLI 用、`smartasr serve` 作 API 用
- **模型来源三层回退：** 本地目录 → 内网自定义服务器 → 官方 Hub（HuggingFace/ModelScope），支持离线/受限网络/东亚网络环境部署
- **中国生态原生：** FunASR、SenseVoiceSmall、ModelScope、Qwen-ASR 一等公民支持
- **平台无关扩展路径：** 零依赖核心 + Protocol 规范，为 MicroPython / 固件 / IoT 设备集成保留可能性——只要有足够小的本地模型即可运行

**设计哲学：** 框架结构决定代码质量——优先定义清晰的模块边界和插件规范，实现细节自然随之收敛。核心包不引入任何重依赖，FastAPI/Typer/pydantic 均为可选 extra，引擎层独立分发。

## Project Classification

| 维度 | 值 |
|------|----|
| 项目类型 | Local AI Runtime |
| 领域 | AI/ML Infrastructure — 本地 ASR 部署平台 |
| 复杂度 | Medium-High |
| 项目上下文 | Brownfield（v0.1.0 Alpha 基础） |
| 近期目标 | `smartasr serve` 守护进程 + `models pull` + FunASR 完整链路跑通 |
| 中期目标 | 成为"本地 ASR 部署"开发者心智的默认选择 |
| 长期定位 | ASR 生态基础设施（Ollama 路径）；厂商发布 SmartASR 兼容模型包 |

---

## Success Criteria

### User Success

- 开发者从 `pip install smartasr[funasr]` 到第一次成功转录，用时 < 5 分钟
- 零配置可运行：`transcribe("audio.wav")` 自动选用第一个可用引擎、自动检测模型最优语言（fallback 英语），无需任何参数
- 切换引擎只需改一个参数，不重写集成代码
- `smartasr transcribe audio.wav` CLI 一行可用，行为与库一致
- 阻塞式调用（同步）为默认；异步长音频场景通过 REST API `/transcribe/async` + 轮询或库层 `atranscribe()` 支持

### Technical Success

- **FunASR 完整链路：** 音频输入 → VAD 分割 → 逐段识别 → 合并输出，端到端无断点
- **三接口同源：** lib / CLI / REST API 调用同一核心代码路径，行为一致
- **引擎可切换：** FunASR ↔ Qwen-ASR 通过单一参数切换，零代码变更
- **VAD 插拔框架：** `VADBackend` 接口定义就位；至少一个实现可用；新增 VAD 无需修改核心
- **模型来源回退：** 本地目录 → 内网服务器 → 官方 Hub，每层独立可测
- **零依赖核心：** `pip install smartasr` 不拉取 torch/fastapi/typer；各能力通过 extra 引入
- **测试覆盖：** 核心转录路径有 unit + integration 测试；引擎接口合规性测试覆盖所有 Protocol 方法

### Open Source Success

- `STTEngine` Protocol 稳定到第三方开发者无需指导即可编写兼容引擎
- 写一个新引擎适配所需时间 < 1 小时（有文档引导）
- Protocol 版本化，有 changelog

### Measurable Outcomes

| 指标 | MVP 目标 |
|------|---------|
| 首次转录成功用时（pip 安装路径） | < 5 分钟 |
| 首次转录成功用时（Docker 路径） | < 3 分钟 |
| `smartasr models pull` → 可用模型 | < 2 分钟（网络正常） |
| 非 Python 语言（Node.js/curl）通过 HTTP API 完成转录 | 零额外配置 |
| 引擎切换代码改动量 | 1 个参数 |
| 新引擎适配用时 | < 1 小时 |
| 核心路径测试覆盖 | > 80% |
| 核心包安装大小（无 extra） | < 50KB |

---

## Product Scope

### MVP — v1.0 必须交付

**运行时核心（新增）：**
- `smartasr serve` 守护进程
  - 引擎生命周期管理（`keep_alive`，默认 5m，参照 Ollama）
  - 后台运行，支持 macOS launchd / Linux systemd 服务注册
- `smartasr run <model>` 交互转录模式（参照 `ollama run`）
- ASRModelfile 模型配置文件格式（参照 Ollama Modelfile）
- `~/.smartasr/` 用户目录
  - `config.yaml` — 全局配置（API Key、默认引擎、keep_alive）
  - `models/manifests/` — 模型清单（CAS 索引）
  - `models/blobs/` — 内容寻址存储（sha256，多引擎共享）
- Docker 官方镜像（MVP 主要分发方式之一）

**模型管理 CLI（新增）：**
- `smartasr models pull <model>` — 流式下载进度条（参照 `ollama pull`）
- `smartasr models ls` — 本地已有模型列表（参照 `ollama ls`）
- `smartasr models rm <model>` — 删除（参照 `ollama rm`）
- `smartasr models show <model>` — 详情含 capabilities
- `smartasr models available` — 全部三态列表（LOCAL_READY / LOCAL_INSTALLABLE / CLOUD_API）
- `smartasr engines ps` — 已加载引擎状态（参照 `ollama ps`）

**REST API /api/*（更新，参照 Ollama /api/*）：**
- `POST /api/transcribe` — 同步转录
- `POST /api/transcribe/async` — 异步任务（长音频 / 云端）
- `GET  /api/tasks/{id}` — 任务状态轮询
- `GET  /api/models` — 本地模型列表（参照 `/api/tags`）
- `GET  /api/models/available` — 全部三态
- `POST /api/models/pull` — 流式下载
- `DELETE /api/models/{name}` — 删除
- `GET  /api/engines/ps` — 已加载引擎状态（参照 `/api/ps`）
- `GET  /api/version`

**保留原有（调整定位）：**
- FunASR 引擎（SenseVoiceSmall + paraformer-zh）
- Qwen-ASR 引擎（DashScope API）
- VAD：`VADBackend` 插拔框架到位，至少一个实现
- Python lib embedded / HTTP 双模式（参照 Ollama Python SDK 自动检测）
- `STTEngine` Protocol 与 `VADBackend` Protocol 版本化定义（内部引擎插件契约）
- 核心包零重依赖，extras 分层：`[funasr]` `[qwen]` `[serve]` `[cli]` `[all]`
- 核心路径测试覆盖

### Growth — Post-MVP

- OpenAI Whisper API 兼容层（`POST /v1/audio/transcriptions`）—— 生态适配器，低成本附加
- smartasr 单文件二进制分发（GitHub Releases）
- 流式识别（`STTEngine.stream()`）
- 说话人分离
- 多语言自动检测
- 更多 VAD 实现
- 内网模型 Registry 参考实现
- `atranscribe()` 异步库接口

### Vision — 长期

- 独立引擎包发布（`smartasr-engine-funasr`、`smartasr-engine-qwen`）
- 官方提供商适配 SmartASR Protocol
- Azure / Google / 讯飞等第三方云端引擎
- MicroPython / IoT 兼容层
- Web UI 参考实现

---

## User Journeys

### Journey A — Python 开发者首次集成（核心路径）

**用户：** 后端开发者，项目需要给上传的音频生成文字记录。

```
安装
└── pip install smartasr[funasr]
    └── 首次运行自动提示下载模型（或从本地目录加载）

首次使用（零配置）
└── from smartasr import transcribe
    result = transcribe("meeting.wav")
    └── 自动选用第一个可用引擎
        自动检测模型最优语言
        返回 STTResponse（text, segments, duration）

切换引擎（云端对比）
└── result = transcribe("meeting.wav", engine="qwen")
    └── 一个参数切换，代码其余部分不变

长音频处理
└── 同步调用超时？→ 使用 atranscribe() 或改走 REST API
    └── 错误信息明确指引到正确接口
```

**揭示的需求：** 简洁的 lib API 入口、自动引擎发现、模型自动下载提示、清晰的错误信息、`STTResponse` 结构统一。

---

### Journey B — 引擎开发者添加新引擎（Protocol 路径）

**用户：** 开发者想集成 Whisper 本地模型或自己公司的 ASR API。

```
了解规范
└── 阅读 STTEngine Protocol 文档
    └── 4 个方法：transcribe() / get_metadata() / get_models() / check_available()
        每个方法有明确的输入输出类型定义和语义说明

实现引擎
└── class WhisperEngine:  # 无需 import smartasr
    def transcribe(self, request: STTRequest) -> STTResponse: ...
    def get_metadata(self) -> EngineMetadata: ...
    def get_models(self) -> list[ModelInfo]: ...
    def check_available(self) -> bool: ...

注册引擎
└── @register_engine("whisper")
    └── 或放入 engines/ 目录自动发现

验证
└── smartasr engines list  → 显示 whisper 已注册
    transcribe("test.wav", engine="whisper")  → 成功
```

**揭示的需求：** Protocol 文档完整、`STTRequest`/`STTResponse` 类型定义公开稳定、`@register_engine` 装饰器简洁、自动发现机制可靠、引擎合规性测试工具。

---

### Journey C — REST API 消费者异步转录（API 路径）

**用户：** 前端开发者或非 Python 项目，通过 HTTP 调用转录服务。

```
启动服务
└── smartasr serve --port 8000
    └── 服务就绪，可接受请求

同步转录（短音频）
└── POST /transcribe  {file: audio.wav, engine: "funasr"}
    └── 等待 → 200 OK  {text: "...", segments: [...]}

异步转录（长音频）
└── POST /transcribe/async  {file: long_audio.wav}
    └── 202 Accepted  {task_id: "uuid-xxx"}

    轮询状态
    └── GET /tasks/uuid-xxx
        └── {status: "processing", progress: 0.4}
        └── {status: "completed", result: {text: "..."}}

错误场景
└── 引擎不可用 → 503 + 明确错误信息
    文件格式不支持 → 400 + 支持格式列表
    任务不存在 → 404
```

**揭示的需求：** `/transcribe` 同步端点、`/transcribe/async` 异步端点、`/tasks/{id}` 状态查询、明确的错误码体系、服务启动 CLI 命令。

---

### Journey Requirements Summary

| 能力 | 来源旅程 |
|------|---------|
| `transcribe()` 零配置入口函数 | Journey A |
| 引擎自动发现与注册 | Journey A, B |
| `STTRequest` / `STTResponse` 稳定类型 | Journey A, B, C |
| `STTEngine` Protocol 文档化 + 版本化 | Journey B |
| 模型自动下载 / 本地路径加载 | Journey A |
| `@register_engine` 装饰器 + 目录自动发现 | Journey B |
| REST API 同步 + 异步端点 | Journey C |
| 任务状态轮询接口 | Journey C |
| 统一错误码与错误信息规范 | Journey A, C |
| `smartasr serve` CLI 命令 | Journey C |

---

## Innovation & Novel Patterns

### Detected Innovation Areas

**1. 协议反转（Protocol Inversion）**

传统 ASR 集成模式：开发者适配每个 ASR 提供商的 SDK。SmartASR 反转这一关系：定义公开的 `STTEngine` Protocol 规范，提供商实现规范以被生态系统采用。这与 OpenAI API 格式成为 LLM 事实标准的路径同构，但应用于 ASR 领域，且在协议层（`typing.Protocol`）而非 HTTP 层做统一。

**2. 本地+云端统一抽象（Unified Local/Cloud Abstraction）**

市场调研确认：无任何现有开源库在单一接口下同时抽象本地推理引擎和云端 API。`SpeechRecognition`（2014）是最接近的先例，但不支持服务化、异步或模型生命周期管理。SmartASR 是这一概念的现代实现。

**3. 多源模型分发策略（Multi-Source Model Distribution）**

`本地目录 → 内网服务器 → 官方 Hub` 的三层回退链，是针对受限网络环境（东亚、企业内网、离线设备）的原创解决方案。无现有 ASR 框架实现过此模式。

### Market Context & Competitive Landscape

市场调研（2026-03）确认：17 个主流 ASR 项目中，无一同时满足「本地+云端统一 + 多接口暴露 + 插拔引擎注册表 + 多源模型管理」的完整组合。最接近竞品 `SpeechRecognition` 缺失服务化、异步、模型管理三大能力。

### Validation Approach

- **Protocol 验证：** 第三方开发者无需指导即可在 1 小时内实现兼容引擎
- **集成验证：** FunASR 链路端到端测试通过，三接口行为一致性测试通过
- **生态验证：** 至少一个外部项目将 SmartASR 作为直接依赖使用

### Risk Mitigation

- **协议稳定性风险：** Protocol 版本化 + changelog，有破坏性变更时提供迁移路径
- **生态冷启动风险：** 内置两个高质量参考引擎实现（FunASR + Qwen）降低采用门槛
- **FFmpeg 路径过度乐观：** 代码质量和 Protocol 稳定性是可控因素，社区采用是结果而非目标

---

## Developer Tool SDK Platform — 特定需求

### Language & Platform Support

- **Primary Language:** Python 3.10+
- **Type Hints:** Full `typing` module annotations + `.pyi` stub files for IDE completion
- **IDE Integration:** Mypy-compatible, Pylint/Flake8 clean, VSCode/PyCharm IntelliSense support
- **Python Versions:** 3.10, 3.11, 3.12, 3.13（CI/CD 测试矩阵）

### Installation & Distribution

- **Package Manager:** PyPI (pip install smartasr)
- **Extras Architecture:**
  ```
  pip install smartasr                  # core only（零依赖）
  pip install smartasr[funasr]          # + FunASR 引擎
  pip install smartasr[qwen]            # + Qwen 引擎
  pip install smartasr[api]             # + FastAPI 服务器
  pip install smartasr[cli]             # + Typer CLI
  pip install smartasr[all]             # 完整功能
  ```
- **Core Dependencies:** 零重依赖（纯 Python）
- **Distribution:** Wheel + Source distribution on PyPI，支持所有标准 Python 版本

### API Surface & Developer Experience

- **Main Entry Point:** `from smartasr import transcribe`（零配置优先设计）
- **Type Stubs:** 完整 `.pyi` 文件，支持 mypy `strict` 模式，完整类型覆盖
- **Documentation:** Google 风格 docstrings，Protocol 规范完整文档化
- **Error Messages:** 明确指引到解决方案或文档链接，不止错误码
- **Configuration:** 环境变量 → 配置文件 → 参数（三层优先级，支持覆盖）

### Code Examples & Learning Resources

**入门示例（README）：**
```python
from smartasr import transcribe
result = transcribe("audio.wav")
print(result.text)
```

**高级示例（完整文档）：**
- 切换引擎、自定义模型路径、异步调用、错误处理、自定义 VAD 实现
- 编写引擎适配（参考 Journey B）
- 部署 REST API 服务、多模型管理

**示例项目：** GitHub `examples/` 目录覆盖：lib 用法 / CLI 用法 / API 服务 / 自定义引擎

### Versioning & Migration

- **API 稳定性：** `STTEngine` Protocol、`STTRequest`/`STTResponse`、所有公开类型冻结长期 API 兼容
- **破坏性变更：** 允许在主版本号变化时，CHANGELOG.md 明确记录，提供迁移指南
- **v0.x → v1.0 迁移路径：** 一页迁移指南，记录 ABC → Protocol、import 变更等核心区别

