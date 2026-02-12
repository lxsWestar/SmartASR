# SmartASR API 连接与集成指南

本文档描述 SmartASR 项目的 API 端点、数据结构和集成方式，与 [TODO.md](../TODO.md) 保持一致。

---

## 1. 架构概览

SmartASR 是一个轻量级语音转文字微服务，支持三种使用方式：

| 方式 | 描述 | 示例 |
|------|------|------|
| **A. 独立 HTTP 服务** | 作为 RESTful API 服务运行 | `python -m SmartASR.server --port 8080` |
| **B. Python 库导入** | 嵌入现有 Python 项目 | `from SmartASR import transcribe` |
| **C. 目录复制** | 复制 `stt/` 目录到任意项目 | 只保留需要的引擎文件 |

### 核心目录结构
```
backend/app/services/stt/
├── __init__.py           # 统一导出: transcribe, list_engines
├── exceptions.py         # 异常类
├── dto.py                # 数据对象: STTRequest, STTResponse, EngineMetadata
├── base.py               # 引擎基类 BaseSTTEngine
├── audio_utils.py        # 音频预处理 (FFmpeg)
├── registry.py           # 引擎注册中心 (装饰器自动注册)
├── config.py             # 配置管理
└── engines/              # 引擎目录 (放文件即注册)
    ├── __init__.py       # 自动扫描
    ├── _template.py      # 开发模板
    ├── ali_funasr.py     # FunASR 本地引擎
    └── ali_qwen.py       # Qwen-ASR 云端引擎
```

---

## 2. 支持的 STT 引擎

| 引擎标识 | 显示名称 | 类型 | 依赖库 | 特点 |
|----------|----------|------|--------|------|
| `ali_funasr` | 阿里 FunASR (本地) | local | `funasr` | SenseVoiceSmall/Paraformer，免费，支持 GPU |
| `ali_qwen` | 阿里百炼 Qwen-ASR (云端) | cloud | `dashscope` | 通义千问大模型，按量计费 |

### 插件机制
```
放文件 = 注册引擎
删文件 = 移除引擎
无需修改任何其他代码
```

---

## 3. API 端点总览

基础路径: `/api/stt`

### 3.1 引擎管理 API

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/engines` | 获取所有可用引擎列表 |
| `GET` | `/engines/{engine_name}` | 获取单个引擎详情 (含参数规格) |
| `GET` | `/engines/{engine_name}/models` | 获取引擎支持的模型列表 |
| `GET` | `/engines/{engine_name}/models/{model_name}` | 获取模型详细参数 |

### 3.2 转写 API

| 方法 | 路径 | 描述 |
|------|------|------|
| `POST` | `/transcribe` | 同步识别 (短音频) |
| `POST` | `/transcribe/async` | 异步识别 (长音频) |
| `POST` | `/transcribe/batch` | 批量识别 |
| `GET` | `/tasks/{task_id}` | 查询异步任务状态 |
| `GET` | `/tasks` | 列出所有任务 |
| `DELETE` | `/tasks/{task_id}` | 取消/删除任务 |

### 3.3 批量处理 API

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/batches/{batch_id}` | 查询批次状态 |
| `GET` | `/batches` | 列出所有批次 |
| `DELETE` | `/batches/{batch_id}` | 取消整个批次 |

### 3.4 模型管理 API (本地引擎)

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/models/status` | 获取模型加载状态 |
| `POST` | `/models/preload` | 预加载模型到显存 |
| `DELETE` | `/models/unload` | 卸载模型释放显存 |
| `POST` | `/models/download` | 下载模型 (不加载) |

### 3.5 文件管理 API

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/files` | 列出已上传的临时文件 |
| `DELETE` | `/files/{file_id}` | 删除文件 |
| `POST` | `/files/cleanup` | 清理过期文件 |

### 3.6 配置与监控 API

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/config` | 获取服务配置 |
| `PUT` | `/config` | 更新服务配置 |
| `PUT` | `/config/api-keys/{engine_name}` | 设置引擎 API Key |
| `DELETE` | `/config/api-keys/{engine_name}` | 删除引擎 API Key |
| `GET` | `/stats` | 使用量统计 |
| `GET` | `/metrics` | Prometheus 格式指标 |
| `GET` | `/health` | 健康检查 |

### 3.7 Webhook API

| 方法 | 路径 | 描述 |
|------|------|------|
| `GET` | `/webhooks` | 列出已注册的 webhook |
| `POST` | `/webhooks/test` | 测试 webhook 连通性 |

---

## 4. 数据结构 (DTO)

### STTRequest - 识别请求
```python
@dataclass
class STTRequest:
    audio_path: Path              # 音频文件路径
    language: str = "auto"        # 语言: zh/en/ja/auto
    engine: str = "ali_funasr"    # 引擎名称
    model: Optional[str] = None   # 模型名称
    options: Dict[str, Any] = {}  # 引擎特定参数
    callback_url: Optional[str] = None  # Webhook 回调
```

### STTResponse - 识别结果
```python
@dataclass  
class STTResponse:
    text: str                     # 完整文本
    segments: List[STTSegment]    # 分段结果
    duration_ms: int              # 音频时长
    engine: str                   # 使用的引擎
    model: str                    # 使用的模型
    language_detected: Optional[str] = None
```

### STTSegment - 识别片段
```python
@dataclass
class STTSegment:
    start_ms: int     # 开始时间 (毫秒)
    end_ms: int       # 结束时间 (毫秒)
    text: str         # 识别文本
```

### EngineMetadata - 引擎元数据
```python
@dataclass
class EngineMetadata:
    name: str                     # 引擎标识
    display_name: str             # 显示名称
    type: str                     # "local" 或 "cloud"
    description: str              # 引擎描述
    version: str = "1.0.0"
    supported_languages: List[str] = []
    models: List[ModelInfo] = []
    requires_api_key: bool = False
    parameters: List[ParameterSpec] = []
```

---

## 5. API 请求/响应示例

### 5.1 获取引擎列表
```bash
GET /api/stt/engines
```
```json
{
  "engines": [
    {
      "name": "ali_funasr",
      "display_name": "阿里 FunASR (本地)",
      "type": "local",
      "models": ["SenseVoiceSmall", "paraformer-zh"]
    },
    {
      "name": "ali_qwen",
      "display_name": "阿里百炼 Qwen-ASR (云端)",
      "type": "cloud",
      "models": ["qwen-audio-asr"]
    }
  ]
}
```

### 5.2 同步转写
```bash
POST /api/stt/transcribe
Content-Type: multipart/form-data
```
| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `file` | File | ✓ | 音频文件 |
| `engine` | string | | 引擎名称，默认 `ali_funasr` |
| `model` | string | | 模型名称 |
| `language` | string | | 语言，默认 `auto` |
| `options` | JSON string | | 引擎特定参数 |

响应:
```json
{
  "text": "识别的完整文本",
  "segments": [
    {"start_ms": 0, "end_ms": 2000, "text": "你好"}
  ],
  "duration_ms": 10000,
  "engine": "ali_funasr",
  "model": "SenseVoiceSmall",
  "language_detected": "zh"
}
```

### 5.3 异步转写
```bash
POST /api/stt/transcribe/async
```
响应:
```json
{
  "task_id": "uuid-xxxx-xxxx",
  "status": "pending",
  "message": "任务已提交"
}
```

查询状态:
```bash
GET /api/stt/tasks/{task_id}
```
```json
{
  "task_id": "uuid-xxxx-xxxx",
  "status": "completed",
  "progress": 1.0,
  "result": { ... }
}
```

### 5.4 Webhook 回调
异步任务支持 `callback_url` 参数，任务完成时会 POST:
```json
{
  "event": "task.completed",
  "task_id": "uuid-xxxx",
  "status": "completed",
  "result": { ... }
}
```

### 5.5 健康检查
```bash
GET /api/stt/health
```
```json
{
  "status": "healthy",
  "ffmpeg": {"available": true, "version": "6.0"},
  "engines": {
    "ali_funasr": {"available": true, "cuda": true},
    "ali_qwen": {"available": true, "api_key_configured": true}
  }
}
```

---

## 6. 错误响应格式

所有错误返回统一格式:
```json
{
  "error": {
    "code": "ENGINE_NOT_FOUND",
    "message": "引擎 'xxx' 不存在",
    "details": {},
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req-uuid"
  }
}
```

### 错误码列表

| 错误码 | HTTP 状态 | 描述 |
|--------|-----------|------|
| `ENGINE_NOT_FOUND` | 404 | 引擎不存在 |
| `MODEL_NOT_FOUND` | 404 | 模型不存在 |
| `MODEL_NOT_LOADED` | 400 | 模型未加载 |
| `FILE_TOO_LARGE` | 413 | 文件过大 |
| `UNSUPPORTED_FORMAT` | 415 | 不支持的格式 |
| `API_KEY_MISSING` | 401 | 缺少 API Key |
| `API_KEY_INVALID` | 401 | API Key 无效 |
| `TRANSCRIPTION_FAILED` | 500 | 识别失败 |
| `TASK_NOT_FOUND` | 404 | 任务不存在 |
| `TASK_CANCELLED` | 400 | 任务已取消 |
| `BATCH_NOT_FOUND` | 404 | 批次不存在 |
| `WEBHOOK_FAILED` | 500 | Webhook 回调失败 |
| `NO_ENGINES_AVAILABLE` | 503 | 无可用引擎 |
| `FFMPEG_NOT_FOUND` | 500 | FFmpeg 未安装 |
| `QUOTA_EXCEEDED` | 429 | 配额耗尽 (云端引擎) |

---

## 7. 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `STT_DEFAULT_ENGINE` | `ali_funasr` | 默认引擎 |
| `STT_DEFAULT_LANGUAGE` | `auto` | 默认语言 |
| `STT_MAX_FILE_SIZE_MB` | `100` | 最大文件大小 |
| `STT_TEMP_DIR` | 系统临时目录 | 临时文件目录 |
| `STT_MODEL_DIR` | `./models` | 模型存储目录 |
| `QWEN_API_KEY` | - | 阿里百炼 API Key (ali_qwen 引擎) |
| `HF_ENDPOINT` | `https://hf-mirror.com` | HuggingFace 镜像 |

---

## 8. 依赖库

### 核心依赖
```
flask>=2.0
flask-cors
```

### 引擎依赖 (按需安装)

| 引擎 | 依赖 |
|------|------|
| `ali_funasr` | `funasr`, `torch`, `torchaudio` |
| `ali_qwen` | `dashscope` |

### 音频处理
```
ffmpeg (系统安装)
```

---

## 9. Python 库使用方式

```python
from backend.app.services.stt import transcribe, list_engines

# 查看可用引擎
engines = list_engines()
print(engines)

# 识别音频
result = transcribe(
    audio_path="test.mp3",
    engine="ali_funasr",
    model="SenseVoiceSmall",
    language="auto"
)
print(result.text)
print(result.segments)
```

---

## 10. 添加新引擎

1. 复制 `engines/_template.py` 并重命名 (如 `whisper.py`)
2. 实现必要方法:
   - `get_metadata()` - 返回引擎元数据
   - `check_available()` - 检查依赖
   - `transcribe()` - 执行识别
3. 放入 `engines/` 目录，自动注册

详见 [TODO.md](../TODO.md) 中的引擎模板示例。
