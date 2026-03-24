---
stepsCompleted: ['step-01-init', 'step-02-context', 'step-03-stack']
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - 'docs/index.md'
  - 'docs/project_overview.md'
  - 'docs/architecture.md'
  - 'docs/tech_stack.md'
  - 'docs/api_contracts.md'
  - 'docs/source_tree.md'
  - 'docs/dev_ops.md'
workflowType: 'architecture'
project_name: 'SmartASR'
user_name: 'lsc'
date: '2026-03-04'
designReference: 'ollama'
---

# SmartASR 架构决策文档

_全面参照 Ollama 设计哲学，适配「内容转文字」底层框架定位。_

---

## 一、设计哲学与定位

### 参照系：Ollama 的成功路径

Ollama 将复杂的 LLM 推理能力通过三个设计决策变得极易使用：
1. **Docker 类比**：pull/run/ps/rm — 零学习成本的模型管理
2. **Server-Client 分离**：serve 进程统一管理生命周期，CLI/API/lib 都是客户端
3. **统一接口掩盖差异**：本地 llama.cpp 和云端 kimi2.5:cloud，CLI 体验完全一致

SmartASR 继承这三个决策，适配「内容转文字」场景。

### 定位扩展：从 ASR 到「内容转文字」框架

受 Ollama 支持 OCR 模型（图片→文字）的启发，SmartASR 重新定位：

```
SmartASR = 任何内容 → 文字 的底层框架

当前 v1.0：
  音频文件  → 文字（ASR，FunASR / Qwen-ASR）

未来扩展（通过 capabilities 标签自然扩展）：
  图片文件  → 文字（OCR，参照 Ollama OCR 模型支持）
  视频文件  → 文字（视频 ASR + 关键帧 OCR）
```

这与 FFmpeg 路径高度一致：FFmpeg 不只做转码，是通用媒体处理框架。
SmartASR 不只做语音识别，是通用「内容转文字」框架。

---

## 二、整体架构分层（Ollama 对照）

```
┌─────────────────────────────────────────────────────────────┐
│                      用户接口层                               │
│  smartasr CLI      Python lib      第三方 HTTP 客户端         │
│  (Typer)           (embedded/HTTP) (任意语言)                 │
└──────────────┬──────────────┬───────────────────────────────┘
               │              │ auto-detect: serve 在线则 HTTP
               │              │ 否则 embedded in-process
┌──────────────▼──────────────▼───────────────────────────────┐
│                    服务器层（可选）                            │
│  smartasr serve  →  FastAPI  →  /api/*                       │
│  引擎生命周期管理（keep_alive / expires_at）                   │
│  异步任务队列（UUID tracking / FIFO eviction）                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  引擎抽象层（STTEngine Protocol）              │
│                                                              │
│  本地引擎                    云端引擎                          │
│  ┌─────────────────┐        ┌──────────────────────┐        │
│  │ FunASR Engine   │        │ Qwen-ASR Engine       │        │
│  │ (in-process)    │        │ (DashScope API)       │        │
│  └─────────────────┘        │ 类比 kimi2.5:cloud    │        │
│                              └──────────────────────┘        │
│  未来扩展                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐      │
│  │ OCR Engine   │  │ Whisper Eng. │  │ 第三方引擎     │      │
│  └──────────────┘  └──────────────┘  └───────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    存储层（CAS 设计）                          │
│  ~/.smartasr/models/                                         │
│  ├── manifests/  （模型清单：名称 → blob 列表）                │
│  └── blobs/      （sha256 内容寻址，多引擎共享）               │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  来源层（三层回退）                            │
│  本地目录  →  内网 registry  →  ModelScope / HuggingFace     │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、核心 Protocol 定义

### STTEngine Protocol（公开契约 v1.0）

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class STTEngine(Protocol):
    """
    SmartASR 引擎公开契约 v1.0

    实现者无需 import 或继承 SmartASR，只需满足以下方法签名。
    参照 Ollama 的推理后端抽象（llama.cpp / MLX / CUDA）。
    """

    PROTOCOL_VERSION: tuple[int, int] = (1, 0)

    def transcribe(self, request: "STTRequest") -> "STTResponse":
        """核心转录方法 — 必须实现"""
        ...

    def get_metadata(self) -> "EngineMetadata":
        """引擎元数据（名称、版本、支持的输入类型）— 必须实现"""
        ...

    def get_models(self) -> list["ModelInfo"]:
        """模型列表（三态：LOCAL_READY / LOCAL_INSTALLABLE / CLOUD_API）— 必须实现"""
        ...

    def check_available(self) -> bool:
        """引擎是否可用（模型已加载 / API Key 有效）— 必须实现"""
        ...

    def get_capabilities(self) -> list[str]:
        """
        可选能力声明 — 有默认实现，不覆盖也能注册

        标准能力标签：
          "asr"                 语音识别（音频→文字）
          "ocr"                 光学字符识别（图片→文字）
          "streaming"           流式输出
          "timestamps"          词级时间戳
          "diarization"         说话人分离
          "language_detection"  自动语言检测
          "cloud_api"           云端 API 引擎（需 API Key + 超时配置）
        """
        return ["asr"]  # 默认声明 ASR 能力
```

### 核心数据类型

```python
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# ── 模型状态三态（参照 Ollama ls / available / ps） ──────────────
class ModelStatus(Enum):
    LOCAL_READY       = "local_ready"       # 本地已有，可立即使用
    LOCAL_INSTALLABLE = "local_installable" # 可安装，需先 pull
    CLOUD_API         = "cloud_api"         # 云端 API，无本地文件

# ── 模型信息（参照 Ollama ModelInfo + ModelDetails） ─────────────
@dataclass
class ModelDetails:
    family: str                        # 模型系列：funasr / qwen / whisper
    parameter_size: str | None = None  # 参数量：350M / 7B
    format: str = "unknown"            # 格式：funasr-bin / gguf / api

@dataclass
class ModelInfo:
    name: str                       # 用户可感知名称：SenseVoiceSmall
    model_id: str                   # Hub ID：iic/SenseVoiceSmall
    status: ModelStatus             # 三态
    languages: list[str]            # 支持语言：[zh, en, ja]
    capabilities: list[str]         # 能力标签：[asr, timestamps]
    details: ModelDetails
    size_mb: int | None = None      # 磁盘大小，云端为 None
    digest: str | None = None       # sha256 哈希（CAS 寻址）
    local_path: Path | None = None  # LOCAL_READY 才有值
    source_hub: str | None = None   # modelscope / huggingface
    api_region: str | None = None   # 云端引擎：cn-hangzhou 等

# ── 引擎元数据 ────────────────────────────────────────────────────
@dataclass
class EngineMetadata:
    name: str                          # funasr / qwen / whisper
    version: str                       # 引擎版本
    description: str
    supported_input: list[str]         # audio / image / video
    is_cloud: bool = False             # 云端 API 引擎标志
    requires_api_key: bool = False     # 需要 API Key
    default_timeout_s: int = 30        # 云端引擎默认更长

# ── 请求 / 响应 ───────────────────────────────────────────────────
@dataclass
class STTRequest:
    input_path: Path                   # 音频 / 图片 / 视频文件
    model: str | None = None           # 指定模型，None 则引擎自选
    language: str | None = None        # 指定语言，None 则自动检测
    keep_alive: str = "5m"             # 参照 Ollama keep_alive
    timeout_s: int | None = None       # None 则用引擎 default_timeout_s
    options: dict = field(default_factory=dict)  # 引擎特定参数

@dataclass
class STTSegment:
    start: float
    end: float
    text: str
    speaker: str | None = None         # 说话人分离结果

@dataclass
class STTResponse:
    text: str
    segments: list[STTSegment]
    language: str
    duration_s: float
    engine: str
    model: str
    digest: str | None = None          # 使用的模型 digest
```

---

## 四、云端引擎设计（Ollama kimi2.5:cloud 参照）

### 云端引擎的特殊性

Ollama 最新支持 `kimi2.5:cloud` 这类云端模型，CLI 体验与本地模型完全一致，但内部有三个差异：

| 维度 | 本地引擎（FunASR） | 云端引擎（Qwen-ASR） |
|------|-----------------|-------------------|
| **模型文件** | 本地 blob | 无（API 调用） |
| **API Key** | 不需要 | 必须，从配置读取 |
| **超时时间** | 短（30s） | 长（120s~300s，长音频） |
| **`check_available()`** | 检查本地模型文件 | 检查 API Key 有效性 |
| **`get_models()`** | LOCAL_READY / LOCAL_INSTALLABLE | CLOUD_API |
| **`keep_alive`** | 保持模型在内存 | 保持 HTTP session |

### API Key 管理

```yaml
# ~/.smartasr/config.yaml（参照 Ollama 的配置文件）
engines:
  qwen:
    api_key: "${DASHSCOPE_API_KEY}"  # 支持环境变量
    timeout_s: 180                   # 长音频超时
    region: cn-hangzhou

  azure_speech:
    api_key: "${AZURE_SPEECH_KEY}"
    endpoint: "https://xxx.cognitiveservices.azure.com"
    timeout_s: 120

model_dir: "~/.smartasr/models"
default_engine: funasr
keep_alive: "5m"
```

优先级：`options 参数` > `环境变量` > `config.yaml` > `默认值`

---

## 五、ASRModelfile（参照 Ollama Modelfile）

```dockerfile
# ASRModelfile — 自定义模型配置（类 Dockerfile 语法）

# 必填：基础模型来源
FROM iic/SenseVoiceSmall              # ModelScope ID
# FROM huggingface/openai/whisper-large-v3
# FROM /local/path/to/model/          # 本地目录

# 引擎选择
ENGINE funasr

# 推理参数
PARAMETER compute_type float16
PARAMETER batch_size 10
PARAMETER beam_size 5

# VAD 配置
PARAMETER vad_model fsmn-vad
PARAMETER vad_threshold 0.5

# 默认语言（可被请求覆盖）
PARAMETER language zh

# 元数据
DESCRIPTION "SenseVoiceSmall 中文企业会议优化配置"
LANGUAGES zh yue
CAPABILITIES asr timestamps language_detection
```

CLI 使用：
```bash
# 创建自定义模型配置（参照 ollama create）
smartasr models create meeting-zh -f ./ASRModelfile

# 使用自定义配置
smartasr run meeting-zh
smartasr transcribe audio.wav --model meeting-zh
```

---

## 六、CLI 完整命令体系

```
smartasr
│
├── run <engine|model> [--stream] [--format text|json|srt|vtt]
│     交互模式（参照 ollama run）
│     支持本地引擎和云端引擎，体验完全一致
│
│     $ smartasr run funasr
│     已加载: FunASR (SenseVoiceSmall) — 本地
│     >>> meeting.wav
│     转录中... ████████ 100%
│     这是会议内容...
│     >>> /model paraformer-zh
│     >>> /bye
│
│     $ smartasr run qwen              ← 云端引擎，体验一致
│     已加载: Qwen-ASR (qwen-asr-v1) — 云端 API
│     >>> interview.mp3
│     转录中... (云端处理中，预计 15s)
│     这是采访内容...
│
├── transcribe <file> [选项]           ← 单次调用（脚本/管道）
│     --engine funasr|qwen
│     --model SenseVoiceSmall
│     --format text|json|srt|vtt
│     --output <file>
│     --timeout 180
│
├── models
│   ├── list                           ← 本地已有（参照 ollama ls）
│   │   NAME              ENGINE  SIZE     MODIFIED     DIGEST
│   │   SenseVoiceSmall   funasr  1.2 GB   2 hours ago  sha256:abc...
│   │
│   ├── available                      ← 全部（本地+可装+云端）
│   │   NAME              ENGINE  SIZE    LANGUAGES  STATUS    CAPABILITIES
│   │   SenseVoiceSmall   funasr  1.2GB   zh en ja   本地已有  asr timestamps
│   │   paraformer-zh     funasr  900MB   zh         可安装    asr timestamps
│   │   qwen-asr-v1       qwen    —       zh en      云端 API  asr
│   │
│   ├── pull <model>                   ← 下载（流式进度，参照 ollama pull）
│   │   pulling manifest
│   │   pulling sha256:abc...  ████████████  45%  540MB/1.2GB
│   │
│   ├── rm <model>                     ← 删除（参照 ollama rm）
│   ├── show <model>                   ← 详情含 capabilities
│   └── create <name> -f <ASRModelfile>  ← 自定义（参照 ollama create）
│
├── engines
│   ├── ps                             ← 已加载引擎（参照 ollama ps）
│   │   ENGINE  MODEL              SIZE    TYPE   UNTIL
│   │   funasr  SenseVoiceSmall    1.2GB   本地   9 minutes from now
│   │   qwen    qwen-asr-v1        —       云端   session active
│   │
│   └── list                           ← 已注册引擎列表
│
└── serve [--port 8765]                ← 启动后台服务（参照 ollama serve）
```

---

## 七、REST API（参照 Ollama /api/*）

```
GET  /api/version

# 模型管理
GET    /api/models                     ← 本地已有（参照 /api/tags）
GET    /api/models/available           ← 全部三类
POST   /api/models/pull                ← 流式下载进度
DELETE /api/models/{name}

# 引擎状态（参照 /api/ps）
GET    /api/engines/ps

# 核心转录（参照 /api/generate）
POST   /api/transcribe                 ← 同步（短音频）
POST   /api/transcribe/stream          ← 流式（未来）
POST   /api/transcribe/async           ← 异步任务（长音频 / 云端）
GET    /api/tasks/{id}                 ← 任务状态轮询
```

### POST /api/transcribe 请求结构

```json
{
  "input": "base64_encoded_audio_or_path",
  "engine": "funasr",
  "model": "SenseVoiceSmall",
  "keep_alive": "5m",
  "timeout": 180,
  "options": {
    "language": "zh",
    "compute_type": "float16"
  }
}
```

### GET /api/engines/ps 响应（参照 /api/ps）

```json
{
  "engines": [
    {
      "name": "funasr",
      "loaded_model": "SenseVoiceSmall",
      "size_mb": 1200,
      "type": "local",
      "expires_at": "2026-03-04T15:30:00Z"
    },
    {
      "name": "qwen",
      "loaded_model": "qwen-asr-v1",
      "size_mb": null,
      "type": "cloud_api",
      "expires_at": null
    }
  ]
}
```

---

## 八、Python lib 双模式（Embedded vs HTTP）

```python
# ── Embedded 模式（默认，无需 smartasr serve）─────────────────────
from smartasr import transcribe
result = transcribe("meeting.wav")          # in-process 直接调用

# ── HTTP 客户端模式（smartasr serve 运行时）────────────────────────
from smartasr import Client
client = Client("http://localhost:8765")
result = client.transcribe("meeting.wav")

# ── 自动检测模式（推荐，与 Ollama 相同设计）──────────────────────
from smartasr import transcribe
# 自动检测：localhost:8765 有服务 → HTTP 模式
# 否则 → embedded 模式
result = transcribe("meeting.wav")

# ── 云端引擎使用体验一致 ─────────────────────────────────────────
result = transcribe("meeting.wav", engine="qwen")
# 内部：从 config.yaml 读取 API Key，超时自动用 default_timeout_s=180
```

---

## 九、模型存储结构（CAS 参照 Ollama）

```
~/.smartasr/
├── config.yaml                          # 全局配置（API Key、默认引擎等）
│
└── models/
    ├── manifests/                       # 模型清单（名称 → blob 列表）
    │   ├── modelscope/
    │   │   └── iic/
    │   │       └── SenseVoiceSmall/
    │   │           └── latest           # JSON：{blobs, size_mb, capabilities}
    │   └── local/
    │       └── meeting-zh/
    │           └── v1                   # ASRModelfile 生成的自定义配置
    │
    └── blobs/                           # 内容寻址存储（sha256）
        ├── sha256-abc123...             # 模型权重（多引擎可共享）
        └── sha256-def456...             # 配置文件
```

---

## 十、包分发结构（extras 架构）

```
pip install smartasr                    # 核心（零依赖）
pip install smartasr[funasr]            # + FunASR 本地引擎
pip install smartasr[qwen]              # + Qwen 云端引擎
pip install smartasr[serve]             # + FastAPI 服务器
pip install smartasr[cli]               # + Typer CLI
pip install smartasr[all]               # 完整功能
```

**核心包内容（零依赖，纯 Python）：**
```
smartasr/
├── __init__.py          # transcribe() + Client 类（自动模式检测）
├── protocols/
│   ├── engine.py        # STTEngine Protocol
│   └── vad.py           # VADBackend Protocol
├── types.py             # ModelInfo / STTRequest / STTResponse 等数据类
├── registry.py          # @register_engine 装饰器 + 引擎发现
├── models/
│   ├── resolver.py      # ModelResolver（三层回退）
│   ├── store.py         # CAS 存储管理
│   └── modelfile.py     # ASRModelfile 解析
└── errors.py            # SmartASRError 层次
```

---

## 十一、错误处理（语义一致 + 格式灵活）

```python
class SmartASRError(Exception):
    code: str            # "ERR_ENGINE_NOT_AVAILABLE"
    user_message: str    # "引擎 funasr 不可用，请检查安装"
    developer_message: str

class EngineNotAvailable(SmartASRError): ...
class ModelNotFound(SmartASRError): ...
class ModelNotReady(SmartASRError):
    """用户尝试使用 LOCAL_INSTALLABLE 模型时抛出"""
    # user_message: "模型 'paraformer-zh' 尚未下载。
    #                运行 `smartasr models pull paraformer-zh` 安装（约 900MB）。"
class AudioFormatUnsupported(SmartASRError): ...
class APIKeyMissing(SmartASRError): ...     # 云端引擎专用
class CloudAPITimeout(SmartASRError): ...   # 云端引擎专用
```

---

## 十二、多 Agent 实现边界

| Agent | 负责模块 | 依赖 |
|-------|---------|------|
| **Dev-Core** | `smartasr/protocols/` + `smartasr/types.py` + `smartasr/errors.py` | 无 |
| **Dev-Registry** | `smartasr/registry.py` + `smartasr/models/` | Core |
| **Dev-Engine-FunASR** | `engines/funasr/` | Core + Registry |
| **Dev-Engine-Qwen** | `engines/qwen/` | Core + Registry |
| **Dev-Serve** | `smartasr_serve/` | Core + Registry |
| **Dev-CLI** | `smartasr_cli/` | Core + Serve（HTTP 客户端） |
| **Dev-QA** | `tests/compliance/` + `tests/integration/` | 全部 |

---

## 十三、未来扩展路径（capabilities 驱动）

```
v1.0  asr                    音频 → 文字（FunASR + Qwen）
v1.1  ocr                    图片 → 文字（参照 Ollama OCR 模型支持）
v1.2  streaming              流式转录
v1.3  diarization            说话人分离
v2.0  video                  视频 → 文字（ASR + 关键帧 OCR）
长期  vendor_protocol        厂商实现 SmartASR Protocol（FFmpeg 路径）
```

每个新能力通过 `get_capabilities()` 标签声明，不破坏现有 Protocol。
