# SmartASR API 契约文档

> 由 document-project 工作流生成 | 扫描级别: exhaustive | 日期: 2026-03-02

---

## API 基础信息

| 属性 | 值 |
|------|---|
| Base URL | `http://localhost:8000` |
| API 前缀 | `/api/stt` |
| 文档地址 | `http://localhost:8000/documents` |
| OpenAPI | `http://localhost:8000/openapi.json` |
| 认证方式 | 无（DASHSCOPE_API_KEY 通过请求参数传入） |
| CORS | 允许所有来源（需生产环境限制） |

---

## 端点完整列表

### 系统端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 返回 API 基本信息 |
| GET | `/health` | 简单健康检查（兼容旧接口） |
| GET | `/api/stt/health` | 详细健康检查 |

### 语音识别

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/stt/transcribe` | 同步识别（短音频 < 1 分钟） |
| POST | `/api/stt/transcribe/async` | 异步识别（长音频，返回 task_id） |

### 任务管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stt/tasks` | 列出所有任务（支持分页和状态过滤） |
| GET | `/api/stt/tasks/{task_id}` | 获取任务详情（含结果和进度） |
| DELETE | `/api/stt/tasks/{task_id}` | 取消 / 删除任务 |

### 引擎管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stt/engines` | 列出所有已注册引擎 |
| GET | `/api/stt/engines/{engine_id}` | 获取引擎详情（含模型列表和参数规格） |

### 文件管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stt/files` | 列出上传文件 |
| DELETE | `/api/stt/files/{file_id}` | 删除上传文件 |

### 配置管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stt/config` | 获取当前配置 |
| PUT | `/api/stt/config` | 更新配置 |

---

## 数据模型（DTO）

### STTRequest

语音识别请求对象（内部使用，不直接暴露为 HTTP Body）：

```python
@dataclass
class STTRequest:
    audio_path: Path              # 音频文件路径（服务器本地路径）
    language: str = "auto"        # 语言: zh/en/ja/ko/yue/auto
    engine: str = "ali_funasr"    # 引擎名称
    model: Optional[str] = None   # 模型名称，None 使用引擎默认值
    options: Dict[str, Any] = {}  # 引擎特定参数
    callback_url: Optional[str] = None  # Webhook 回调 URL
    progress_callback: Optional[Callable] = None  # 进度回调函数
```

### STTResponse

识别结果对象：

```python
@dataclass
class STTResponse:
    text: str                          # 完整识别文本
    segments: List[STTSegment]         # 分段结果（带时间戳）
    duration_ms: int                   # 音频总时长（毫秒）
    engine: str                        # 使用的引擎名称
    model: str                         # 使用的模型名称
    language_detected: Optional[str]   # 检测到的语言
    usage: Optional[UsageInfo]         # 使用量统计（含 API 调用次数）
```

### STTSegment

识别片段（带时间戳）：

```python
@dataclass
class STTSegment:
    start_ms: int   # 开始时间（毫秒）
    end_ms: int     # 结束时间（毫秒）
    text: str       # 片段文本
```

### UsageInfo

使用量统计：

```python
@dataclass
class UsageInfo:
    audio_duration_ms: int    # 音频时长（毫秒）
    processing_time_ms: int   # 处理耗时（毫秒）
    api_calls: int            # API 调用次数（云端引擎）
    input_tokens: int         # 输入 token（云端引擎）
    output_tokens: int        # 输出 token（云端引擎）
    characters: int           # 识别字符数
```

### EngineMetadata

引擎自描述元数据：

```python
@dataclass
class EngineMetadata:
    name: str                         # 引擎标识（如 "ali_funasr"）
    display_name: str                 # 显示名称
    type: str                         # "local" 或 "cloud"
    description: str
    version: str
    supported_languages: List[str]
    models: List[ModelInfo]
    requires_api_key: bool
    parameters: List[ParameterSpec]   # 引擎级参数规格
```

### Task（任务对象）

```python
@dataclass
class Task:
    task_id: str                      # UUID 字符串
    status: TaskStatus                # pending/processing/completed/failed/cancelled
    engine: str
    model: Optional[str]
    audio_path: str
    callback_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    progress: float                   # 0.0 ~ 1.0
    progress_current: int             # 当前已处理段数
    progress_total: int               # 总段数
    progress_message: str             # 可读进度描述
    result: Optional[Dict]            # 完成时包含 STTResponse.to_dict()
    error: Optional[str]              # 失败时的错误信息
```

---

## HTTP API 响应格式

### POST /api/stt/transcribe

**请求体（multipart/form-data）：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | File | 是 | 音频文件（支持 mp3/wav/flac/ogg/m4a/aac/webm/mp4/mkv/avi） |
| `engine` | string | 否 | 引擎名称，默认 `ali_funasr` |
| `model` | string | 否 | 模型，默认引擎内置默认值 |
| `language` | string | 否 | 语言，默认 `auto` |
| `options` | string(JSON) | 否 | 引擎特定参数，JSON 字符串 |

**成功响应（200）：**

```json
{
  "text": "完整识别文本",
  "segments": [
    {"start_ms": 0, "end_ms": 2500, "text": "第一段文本"},
    {"start_ms": 3000, "end_ms": 5500, "text": "第二段文本"}
  ],
  "duration_ms": 5500,
  "engine": "ali_funasr",
  "model": "SenseVoiceSmall",
  "language_detected": "zh"
}
```

**错误响应：**

| 状态码 | 触发条件 |
|--------|---------|
| 400 | options 不是有效 JSON |
| 404 | 引擎或模型不存在 |
| 500 | FFmpeg 未安装 / 识别失败 |
| 503 | 引擎不可用（依赖未安装） |

---

### POST /api/stt/transcribe/async

**请求体（multipart/form-data）：**（同上，额外支持 `callback_url`）

| 额外字段 | 类型 | 必填 | 说明 |
|---------|------|------|------|
| `callback_url` | string | 否 | 完成时 POST 结果到该 URL |

**成功响应（200）：**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "任务已提交"
}
```

---

### GET /api/stt/tasks/{task_id}

**成功响应（200）：**

```json
{
  "task_id": "550e8400-...",
  "status": "processing",
  "engine": "ali_funasr",
  "model": "SenseVoiceSmall",
  "created_at": "2026-03-02T10:00:00",
  "updated_at": "2026-03-02T10:01:30",
  "progress": 0.6,
  "progress_current": 6,
  "progress_total": 10,
  "progress_message": "识别第 6/10 段",
  "result": null,
  "error": null
}
```

---

## Webhook 回调格式

当任务完成后，若提供了 `callback_url`，系统会 POST 以下格式：

```json
{
  "event": "task.completed",
  "task_id": "550e8400-...",
  "status": "completed",
  "result": { /* STTResponse.to_dict() 内容 */ }
}
```

失败时：

```json
{
  "event": "task.failed",
  "task_id": "550e8400-...",
  "status": "failed",
  "error": "[TRANSCRIPTION_ERROR] 识别失败原因"
}
```

---

## 错误码体系

| 错误码 | 触发类 | 描述 |
|--------|--------|------|
| `STT_ERROR` | STTException | 基础 STT 错误 |
| `FFMPEG_NOT_FOUND` | FFmpegNotFoundError | FFmpeg 未安装 |
| `ENGINE_NOT_FOUND` | EngineNotFoundError | 引擎不存在或未注册 |
| `MODEL_NOT_FOUND` | ModelNotFoundError | 模型不存在 |
| `MODEL_DOWNLOAD_ERROR` | ModelDownloadError | 模型下载失败 |
| `MODEL_NOT_LOADED` | ModelNotLoadedError | 模型未加载 |
| `API_KEY_MISSING` | APIKeyMissingError | API Key 未配置 |
| `TRANSCRIPTION_ERROR` | TranscriptionError | 识别失败 |
| `TASK_NOT_FOUND` | TaskNotFoundError | 任务不存在 |
| `TASK_CANCELLED` | TaskCancelledError | 任务已取消 |
| `FILE_TOO_LARGE` | FileTooLargeError | 文件超过限制（默认 500MB） |
| `UNSUPPORTED_FORMAT` | UnsupportedFormatError | 不支持的音频格式 |

---

## 引擎参数规格

### ali_funasr 引擎参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `use_itn` | boolean | true | 逆文本正则化（数字/符号转换） |
| `max_speakers` | integer | -1 | 说话人分离数（-1 禁用，仅 paraformer 支持） |

**可选值 max_speakers：** -1, 2, 3, 4, 5

### ali_qwen 引擎参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `api_key` | string | null | DashScope API Key（覆盖环境变量） |
| `enable_lid` | boolean | true | 启用语种自动识别 |
| `enable_itn` | boolean | false | 启用逆文本正则化 |
