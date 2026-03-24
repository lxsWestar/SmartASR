# SmartASR 架构文档

> 由 document-project 工作流生成 | 扫描级别: exhaustive | 日期: 2026-03-02

---

## 系统概述

SmartASR 是一个**轻量级语音识别（ASR）中间层服务**，设计目标：

1. **统一接口** — 不同 ASR 引擎（本地/云端）通过同一 API/CLI 调用
2. **插件化引擎** — 新增引擎只需实现接口并放入 `engines/` 目录，无需修改核心代码
3. **可嵌入** — `backend/app/services/stt/` 可独立作为 Python 库嵌入其他项目
4. **离线优先** — 支持本地模型、内网模型服务器、离线部署

---

## 整体架构图

```
┌──────────────────────────────────────────────────────────────┐
│                       客户端层                                │
│                                                              │
│  ┌─────────────────┐          ┌────────────────────────────┐ │
│  │  Web 浏览器       │          │   HTTP 客户端 / 其他应用    │ │
│  │  (frontend/)     │          │   (curl/httpx/etc.)        │ │
│  └────────┬────────┘          └───────────────┬────────────┘ │
└───────────┼───────────────────────────────────┼──────────────┘
            │ HTTP + multipart/form-data         │
            ▼                                   ▼
┌──────────────────────────────────────────────────────────────┐
│                     FastAPI 应用层                            │
│         (backend/app/api/main.py + routers/)                 │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  CORS 中间件 (allow_origins=["*"])                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │/transcribe │  │ /tasks/* │  │/engines/*│  │/config/* │  │
│  │(同步+异步)  │  │(CRUD+   │  │(引擎查询) │  │(配置读写)│  │
│  │            │  │ 进度追踪)│  │          │  │          │  │
│  └─────┬──────┘  └──┬───────┘  └──────────┘  └──────────┘  │
│        │            │                                        │
│        │   BackgroundTasks                                   │
│        │   (异步识别)                                         │
└────────┼────────────┼───────────────────────────────────────┘
         │            │
         ▼            ▼
┌──────────────────────────────────────────────────────────────┐
│                    STT 服务层（可嵌入）                       │
│            (backend/app/services/stt/)                       │
│                                                              │
│  ┌──────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  DTOs        │  │  Registry   │  │  Config / Compat     │ │
│  │  STTRequest  │  │  @register_ │  │  STTConfig           │ │
│  │  STTResponse │  │  engine     │  │  ModelSourceConfig   │ │
│  │  STTSegment  │  │  create_    │  │  get_cache_dir()     │ │
│  │  EngineMetadata│  │  engine()  │  │  to_ffmpeg_path()   │ │
│  └──────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                              │
│  ┌──────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  AudioUtils  │  │  VADUtils   │  │  Exceptions          │ │
│  │  convert_to_ │  │  silero →   │  │  12种异常类型         │ │
│  │  16k_wav()   │  │  funasr →   │  │  统一错误码体系       │ │
│  │  check_ffmpeg│  │  pydub      │  │                      │ │
│  └──────────────┘  └─────────────┘  └─────────────────────┘ │
└────────────────────────────┬─────────────────────────────────┘
                             │ BaseSTTEngine 接口
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌─────────────────────────┐   ┌─────────────────────────────┐
│    ali_funasr（本地引擎）  │   │   ali_qwen（云端引擎）       │
│                         │   │                             │
│  ┌─────────────────────┐│   │  ┌─────────────────────────┐│
│  │ SenseVoiceSmall     ││   │  │  qwen3-asr-flash         ││
│  │ (多语言，需funasr)   ││   │  │  qwen3-asr-turbo         ││
│  ├─────────────────────┤│   │  └─────────────────────────┘│
│  │ paraformer-zh       ││   │                             │
│  │ (中文+说话人分离)    ││   │  VAD策略（不下载模型）:       │
│  └─────────────────────┘│   │  silero → pydub → 固定切分  │
│                         │   │                             │
│  VAD: fsmn-vad (FunASR) │   │  API: DashScope             │
│  本地模型加载            │   │  DASHSCOPE_API_KEY 必需      │
└─────────────────────────┘   └─────────────────────────────┘
```

---

## 命令行层架构

```
smartasr（CLI 入口）
├── transcribe <file>           # 语音识别（最常用）
├── serve [--host] [--port]     # 启动 API 服务
├── engines
│   ├── list                    # 列出可用引擎
│   └── info <engine_id>        # 查看引擎详情
└── config
    ├── get [key]               # 查看配置
    └── set <key> <value>       # 修改配置
```

CLI 层**不通过 HTTP** 调用 API，而是**直接调用** STT Service Layer，避免依赖服务启动。

---

## 异步任务处理架构

```
POST /api/stt/transcribe/async
        │
        ▼
   创建 Task（UUID）
   存入 TaskManager（内存字典）
        │
        ▼
   FastAPI BackgroundTasks.add_task()
   立即返回 {task_id, status: "pending"}
        │
        ▼（后台执行）
   _run_transcription_task()
   ├── 预处理音频（FFmpeg → 16kHz WAV）
   ├── 创建引擎实例
   ├── engine.transcribe(request)
   │   └── progress_callback → TaskManager.update_task()
   ├── 更新 Task.status = "completed" + result
   └── 发送 Webhook 回调（如果有 callback_url）

GET /api/stt/tasks/{task_id}
   └── 读取 TaskManager 中的 Task 对象
       └── 返回进度、结果或错误信息
```

**当前限制：**
- 任务存储在内存中，服务重启后丢失
- 无并发控制，多任务并行执行
- 最多保存 1000 个任务（FIFO 淘汰）

---

## 引擎插件系统

```
引擎注册流程：
──────────────

engines/ 目录下的 .py 文件
        │
        ▼ discover_engines() 自动导入
        │ （跳过 _ 开头的文件）
        ▼
@register_engine 装饰器触发
        │
        ▼
_engine_registry[engine.name] = EngineClass
```

**接口契约（BaseSTTEngine 抽象方法）：**

| 方法 | 签名 | 说明 |
|------|------|------|
| `transcribe` | `(STTRequest) -> STTResponse` | 执行识别（核心方法） |
| `get_metadata` | `() -> EngineMetadata` | 返回引擎描述（类方法） |
| `get_models` | `() -> List[str]` | 返回支持模型列表 |
| `check_available` | `() -> Tuple[bool, str]` | 检查依赖是否就绪 |

**可重写的非必须方法：**
- `load_model(model_name)` — 预加载模型
- `unload_model()` — 释放模型
- `cleanup()` — 释放全部资源

---

## 模型管理架构

```
get_config() → STTConfig
        │
        └── model_source: ModelSourceConfig
                │
                ▼ get_model_path(model_name)
                │
           按优先级尝试：
           │
           ├──(1) local_dir/ 中查找
           │       ├── {model_name}/
           │       ├── hub/iic/{model_name}/
           │       └── ... 多种目录格式
           │
           ├──(2) network_server 下载
           │       └── GET {server}/models/{model_name}
           │           解压至 local_dir/
           │
           └──(3) 返回 None
                   └── 让 FunASR 从官方源自动下载
                       （FUNASR_HUB=ms/hf 控制来源）
```

---

## VAD 系统架构

```
detect_speech_segments(audio_path, method="auto")
        │
        ▼ _select_best_method("auto")
        │
   按优先级检测可用方法：
   ├──(1) silero → from faster_whisper.vad import get_speech_timestamps
   │              无需下载模型，精度高，推荐
   ├──(2) funasr → AutoModel("fsmn-vad")
   │              需要下载 ~100MB 模型，精度高
   └──(3) pydub  → detect_nonsilent()
                  无额外依赖，精度较低，最后回退
```

---

## 音频处理管道

```
上传的音频文件（任意格式）
        │
        ▼ _preprocess_audio()
        │
   check_ffmpeg() ──✗──► HTTPException 500
        │ ✓
        ▼
   convert_to_16k_wav()
   ffmpeg -i input -ac 1 -ar 16000 -c:a pcm_s16le output.wav
        │
        ▼
   16kHz mono PCM WAV
        │
   ┌────┴──────────────────────────┐
   │                               │
   ▼ (SenseVoiceSmall)            ▼ (paraformer-zh)
VAD 分段                       直接送入模型
fsmn-vad → N 段                （模型内置 VAD）
   │
   ▼
逐段识别 → STTSegment[]
   │
   ▼
rich_transcription_postprocess()
+ CJK 去空格
   │
   ▼
拼合 STTResponse
```

---

## 前后端集成架构

```
frontend/index.html（浏览器加载）
        │
        ▼ app.js 初始化
        │
   GET /api/stt/engines → 填充引擎选择框
        │
   用户选择引擎 → GET /api/stt/engines/{id} → 动态显示模型/参数选项
        │
   用户点击识别
        │
   ┌────┴────────────────────────────────────┐
   │ 短音频（用户可选）                        │ 长音频（用户可选）
   ▼                                         ▼
POST /api/stt/transcribe                POST /api/stt/transcribe/async
        │                                      │
   同步等待结果                           获得 task_id
        │                                      │
   显示结果                              轮询 GET /api/stt/tasks/{id}
                                              │（每 2 秒）
                                         进度条更新
                                              │
                                         任务完成 → 显示结果
```

---

## 数据流图（识别请求）

```
客户端 → POST multipart/form-data（含音频文件）
   │
   ▼ FastAPI 接收
   │ UploadFile → _save_upload_file() → cache/uploads/
   │
   ▼ 音频预处理
   │ convert_to_16k_wav() → cache/uploads/xxx_16k.wav
   │
   ▼ 引擎实例化
   │ create_engine("ali_funasr") → FunASREngine()
   │
   ▼ 可用性检查
   │ engine.check_available() → (True, "funasr 1.x.x 已安装")
   │
   ▼ 构建请求
   │ STTRequest(audio_path, language, engine, model, options)
   │
   ▼ 执行识别
   │ engine.transcribe(request) → STTResponse
   │
   ▼ 清理临时文件
   │ _cleanup_files(upload_path, processed_path)
   │
   ▼ 返回响应
   TranscribeResponse（Pydantic 模型 → JSON）
```

---

## 关键设计决策

### 1. 为什么使用 dataclass 而非 Pydantic 作为 DTO？

STT Service Layer 设计为**可独立嵌入**的 Python 库，不强依赖 FastAPI/Pydantic。使用标准库 `dataclasses` 减少外部依赖。API 层有自己的 Pydantic 响应模型作为外部契约。

### 2. 为什么任务存储在内存而非数据库？

v0.1 轻量化设计，避免引入 Redis/SQLite 等额外依赖。生产环境扩展路径已在代码注释中标注（`TaskManager` 类文档）。

### 3. 为什么不使用 Celery 做任务队列？

对于单机部署的 ASR 工具，FastAPI `BackgroundTasks` 足够。未来如需分布式部署，可以将 `_run_transcription_task` 换为 Celery 任务，接口无需改变。

### 4. 为什么 CLI 不调用本地 HTTP API？

CLI 应该在 API 服务**未启动时**也能运行。直接调用 STT Service Layer 是正确的分层方式。

### 5. VAD 三级降级策略的目的？

不同部署环境有不同的可用依赖：
- 完整 GPU 环境：silero（最精确）
- 只有 FunASR 的环境：funasr fsmn-vad
- 仅基础环境：pydub 静音检测
三级降级保证了最大兼容性。

---

## 未来架构演进方向

### 短期（Sprint 1-2）

```
当前：
  inline TaskManager（内存）
  ↓
目标：
  可插拔存储后端（内存 / SQLite / Redis）
  TaskStore 接口抽象
```

### 中期（Sprint 3-4）

```
当前：
  FunASR 内置 VAD（耦合在引擎内）
  ↓
目标：
  VAD 插件化（已有计划文档：documents/【计划】vad-plugin/）
  VADPlugin 接口 + 引擎可声明所需 VAD
```

### 长期

```
容器化部署（Docker Compose）
WebSocket 实时流式识别
多工作进程（Gunicorn + Uvicorn workers）
认证和限流中间件
```
