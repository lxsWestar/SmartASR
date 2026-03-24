# SmartASR 源码目录树

> 由 document-project 工作流生成 | 扫描级别: exhaustive | 日期: 2026-03-02

---

## 完整目录结构（含注释）

```
SmartASR/
│
├── 📄 pyproject.toml              # 项目根配置：setuptools 构建、依赖组、工具配置
├── 📄 config.json                 # 运行时配置（本地，不提交 git）
├── 📄 config.example.json         # 配置模板（提交 git，供参考）
├── 📄 run.py                      # 简单启动入口（等同于 smartasr serve）
├── 📄 README.md                   # 项目总览文档
├── 📄 LICENSE                     # MIT 许可证
├── 📄 COMPLIANCE.md               # 第三方许可证合规说明（GPL/MIT/Apache）
├── 📄 AGENTS.md                   # AI 协作规范（Claude/Copilot 等）
│
├── 📁 backend/                    # ━━━ 后端核心模块 ━━━
│   ├── 📄 __init__.py
│   ├── 📄 README.md               # 后端架构概述
│   │
│   └── 📁 app/
│       ├── 📄 __init__.py
│       │
│       ├── 📁 api/                # FastAPI 应用层
│       │   ├── 📄 __init__.py
│       │   ├── 📄 main.py         # FastAPI 应用工厂（create_app()），注册所有路由和中间件
│       │   ├── 📄 README.md       # API 层文档
│       │   │
│       │   └── 📁 routers/        # 路由分组
│       │       ├── 📄 __init__.py
│       │       ├── 📄 transcribe.py   # POST /transcribe（同步）& /transcribe/async
│       │       ├── 📄 tasks.py        # 任务 CRUD + TaskManager（内存存储）
│       │       ├── 📄 engines.py      # 引擎列表和详情查询
│       │       ├── 📄 files.py        # 上传文件管理
│       │       ├── 📄 config_api.py   # 配置读写接口
│       │       └── 📄 health.py       # 健康检查（含 FFmpeg/引擎状态）
│       │
│       ├── 📁 cli/                # 命令行接口层（Typer）
│       │   ├── 📄 __init__.py     # 导出 main() 入口
│       │   ├── 📄 __main__.py     # python -m backend.app.cli 支持
│       │   ├── 📄 main.py         # CLI 应用创建、全局选项（--version/-v）
│       │   ├── 📄 README.md       # CLI 使用文档
│       │   │
│       │   ├── 📁 commands/       # 子命令实现
│       │   │   ├── 📄 __init__.py
│       │   │   ├── 📄 transcribe.py   # smartasr transcribe <file>
│       │   │   ├── 📄 serve.py        # smartasr serve（启动 API 服务）
│       │   │   ├── 📄 engines.py      # smartasr engines list/info
│       │   │   └── 📄 config.py       # smartasr config get/set
│       │   │
│       │   ├── 📁 formatters/     # 输出格式化器
│       │   │   ├── 📄 __init__.py
│       │   │   ├── 📄 base.py         # 格式化器基类
│       │   │   ├── 📄 txt.py          # 纯文本输出
│       │   │   ├── 📄 json_fmt.py     # JSON 输出
│       │   │   ├── 📄 srt.py          # SRT 字幕格式
│       │   │   ├── 📄 vtt.py          # WebVTT 字幕格式
│       │   │   └── 📄 tsv.py          # TSV（制表符分隔）
│       │   │
│       │   └── 📁 utils/
│       │       ├── 📄 __init__.py
│       │       └── 📄 console.py      # Rich 控制台实例、VERBOSE 全局变量
│       │
│       └── 📁 services/
│           ├── 📄 __init__.py
│           │
│           └── 📁 stt/            # ━━━ STT 核心服务库 ━━━（可独立嵌入）
│               ├── 📄 __init__.py # 公共 API 导出（STTRequest/STTResponse/create_engine 等）
│               ├── 📄 README.md   # STT 库文档
│               │
│               ├── 📄 base.py     # BaseSTTEngine 抽象基类（定义引擎接口契约）
│               ├── 📄 dto.py      # 数据传输对象：STTRequest/STTResponse/STTSegment/UsageInfo/EngineMetadata
│               ├── 📄 exceptions.py   # 完整异常类体系（12 种异常类型）
│               ├── 📄 registry.py # 引擎注册中心（@register_engine 装饰器，discover_engines()）
│               ├── 📄 config.py   # STTConfig + ModelSourceConfig（三级模型来源策略）
│               ├── 📄 audio_utils.py  # FFmpeg 封装：check_ffmpeg/convert_to_16k_wav/get_duration
│               ├── 📄 vad_utils.py    # 多后端 VAD 系统（silero/funasr/pydub 三级降级）
│               └── 📄 compat.py       # 跨平台兼容层（Windows 路径/缓存目录/环境变量）
│               │
│               └── 📁 engines/    # 引擎插件目录
│                   ├── 📄 __init__.py
│                   ├── 📄 _template.py    # 新引擎开发模板（以 _ 开头，不自动加载）
│                   ├── 📄 ali_funasr.py   # FunASR 本地引擎（SenseVoiceSmall + paraformer-zh）
│                   └── 📄 ali_qwen.py     # 通义千问云端引擎（qwen3-asr-flash/turbo）
│
├── 📁 frontend/                   # ━━━ 前端 Web UI ━━━
│   ├── 📄 index.html              # 主页面（文件上传、引擎选择、结果展示）
│   ├── 📄 app.js                  # 全部前端逻辑（22KB，零依赖）
│   ├── 📄 style.css               # 样式文件
│   ├── 📄 favicon.svg             # 网站图标
│   └── 📄 README.md               # 前端使用说明
│
├── 📁 tests/                      # ━━━ 测试套件 ━━━
│   ├── 📄 conftest.py             # pytest fixtures（temp_dir/sample_audio_path/project_root）
│   ├── 📄 README.md               # 测试运行说明
│   ├── 📄 quick_test.py           # 快速冒烟测试
│   ├── 📄 test_qwen_japanese.py   # 日语识别专项测试
│   │
│   ├── 📁 unit/                   # 单元测试
│   ├── 📁 integration/            # 集成测试
│   └── 📁 e2e/                    # 端到端测试
│
├── 📁 scripts/                    # ━━━ 工具脚本 ━━━
│   ├── 📄 README.md               # 脚本说明（客户端 vs 服务端区分）
│   ├── 📄 download_sensevoice.py              # SenseVoice 完整下载脚本
│   ├── 📄 download_sensevoice_small_files.py  # SenseVoiceSmall 下载
│   ├── 📄 download_cosyvoice2_small_files.py  # CosyVoice2 TTS 下载（非必需）
│   ├── 📄 model_server.py                     # 服务端：内网模型 HTTP 服务（简单版）
│   └── 📄 model_file_server.py                # 服务端：内网模型 HTTP 服务（完整版）
│
├── 📁 models/                     # ━━━ 模型缓存/配置 ━━━
│   ├── 📄 README.md               # 模型目录说明
│   ├── 📁 SenseVoiceSmall/        # SenseVoice 元信息
│   ├── 📁 paraformer-zh/          # Paraformer 元信息
│   ├── 📁 fsmn-vad/               # FSMN-VAD 元信息
│   └── 📁 ct-punc/                # CT-Punc 元信息
│
├── 📁 SenseVoiceSmall/            # 预下载的 SenseVoice 模型文件（config.yaml 等）
│
├── 📁 documents/                  # ━━━ 原始设计文档 ━━━
│   ├── 📄 README.md               # 文档索引
│   ├── 📁 design/                 # 架构设计
│   │   └── 📄 architecture.md
│   ├── 📁 api/                    # API 参考
│   │   ├── 📄 README.md
│   │   └── 📄 API_CONNECTIONS.md
│   ├── 📁 guides/                 # 用户指南
│   │   ├── 📄 quickstart.md
│   │   ├── 📄 embedding.md        # 嵌入式使用指南
│   │   ├── 📄 engines.md          # 引擎开发指南
│   │   ├── 📄 model-download.md
│   │   └── 📄 manual-download.md
│   └── 📁 【计划】vad-plugin/     # VAD 插件化开发计划
│       ├── 📄 vad-plugin-plan.md
│       ├── 📄 vad-plugin-analysis.md
│       └── 📄 vad-plugin-tasks.md
│
├── 📁 docs/                       # ━━━ AI 上下文文档（本目录）━━━
│   ├── 📄 index.md                # 文档主索引（由工作流生成）
│   ├── 📄 project-scan-report.json  # 扫描状态文件
│   ├── 📄 tech_stack.md           # 技术栈分析
│   ├── 📄 api_contracts.md        # API 契约（本文件）
│   ├── 📄 source_tree.md          # 源码目录树（本文件）
│   ├── 📄 architecture.md         # 架构文档
│   ├── 📄 dev_ops.md              # 开发运营指南
│   └── 📄 project_overview.md     # 项目概述
│
├── 📁 TODO 文件集（根目录）
│   ├── 📄 TODO.md                 # 主要待办事项
│   ├── 📄 TODO-api.md             # API 层待办
│   ├── 📄 TODO-milestones.md      # 里程碑计划
│   ├── 📄 TODO-overview.md        # 总览
│   ├── 📄 TODO-reference.md       # 参考资料
│   ├── 📄 TODO-future.md          # 未来功能
│   ├── 📄 TODO-vad.md             # VAD 相关待办
│   └── 📄 TODO-model-loading.md   # 模型加载待办
│
├── 📁 .github/                    # GitHub 配置
│   ├── 📄 copilot-instructions.md # Copilot 协作指令
│   └── 📁 instructions/           # 各类 AI 助手指令
│
├── 📁 _bmad/                      # BMAD 工作流框架
├── 📁 pyvideotrans/               # 参考代码库（GPL v3，不参与运行时）
└── 📁 smartasr.egg-info/          # pip 构建元数据（自动生成）
```

---

## 关键文件快速索引

| 功能 | 文件 |
|------|------|
| FastAPI 应用入口 | `backend/app/api/main.py:create_app()` |
| CLI 入口函数 | `backend/app/cli/main.py:main()` |
| 引擎基类（接口契约） | `backend/app/services/stt/base.py:BaseSTTEngine` |
| 引擎注册装饰器 | `backend/app/services/stt/registry.py:register_engine()` |
| 新增引擎的模板 | `backend/app/services/stt/engines/_template.py` |
| 所有 DTO 定义 | `backend/app/services/stt/dto.py` |
| 配置管理 | `backend/app/services/stt/config.py:get_config()` |
| 音频预处理 | `backend/app/services/stt/audio_utils.py:convert_to_16k_wav()` |
| VAD 工具 | `backend/app/services/stt/vad_utils.py:detect_speech_segments()` |
| 任务管理器 | `backend/app/api/routers/tasks.py:TaskManager` |
| 同步识别端点 | `backend/app/api/routers/transcribe.py:transcribe_sync()` |
| 异步识别端点 | `backend/app/api/routers/transcribe.py:transcribe_async()` |
| 前端主逻辑 | `frontend/app.js` |

---

## 模块边界说明

```
┌─────────────────────────────────────┐
│            CLI Layer                │
│   (backend/app/cli/)                │
│   Typer + Rich                      │
└──────────────┬──────────────────────┘
               │ 直接调用
               ▼
┌─────────────────────────────────────┐
│            API Layer                │
│   (backend/app/api/)                │
│   FastAPI + Pydantic                │
└──────────────┬──────────────────────┘
               │ 调用 create_engine() + STTRequest
               ▼
┌─────────────────────────────────────┐
│         STT Service Layer           │
│   (backend/app/services/stt/)       │
│   base / dto / registry / config    │
└──────────────┬──────────────────────┘
               │ 插件化接口
        ┌──────┴──────┐
        ▼             ▼
┌────────────┐  ┌────────────┐
│ ali_funasr │  │  ali_qwen  │
│ (本地引擎)  │  │ (云端引擎)  │
└────────────┘  └────────────┘
```

**跨层调用规则：**
1. CLI 和 API 均可直接调用 STT Service Layer
2. 引擎插件只能调用 STT 层内部的 dto / exceptions / config / compat
3. 引擎插件**不能**直接导入 API 层或 CLI 层
4. 前端只通过 HTTP API 与后端通信，不直接调用任何 Python 代码
