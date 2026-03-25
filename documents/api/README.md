# SmartASR API 参考

SmartASR 是一个标准 RESTful API 服务。外部系统通过 HTTP 调用本服务完成语音识别，**无需关心内部实现**。

**Base URL**: `http://<host>:8000`  
**API 前缀**: `/api/stt`

---

## 端点速览

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/stt/transcribe` | 同步语音识别（适合 <1 分钟音频） |
| `POST` | `/api/stt/transcribe/async` | 异步语音识别（适合长音频） |
| `GET`  | `/api/stt/engines` | 列出所有引擎 |
| `GET`  | `/api/stt/engines/{name}` | 引擎详情（含可用状态） |
| `GET`  | `/api/stt/engines/{name}/models` | 引擎支持的模型列表 |
| `GET`  | `/api/stt/engines/{name}/models/{model}` | 单个模型详情 |
| `GET`  | `/api/stt/tasks/{task_id}` | 查询异步任务状态 |
| `GET`  | `/api/stt/health` | 健康检查 |

---

## 引擎说明

服务当前内置三个引擎：

| 引擎名 | display_name | type | vendor | 说明 |
|--------|-------------|------|--------|------|
| `ali_funasr` | FunASR（本地） | `local` | `Alibaba` | 本地推理，支持多语言，需要 torch + funasr |
| `ali_qwen` | Qwen-ASR（云端） | `cloud` | `Alibaba` | 阿里云 API，按量计费，需要 DASHSCOPE_API_KEY |
| `qwen_local` | Qwen3-ASR（本地） | `local` | `Alibaba` | 本地 Qwen3 大模型推理，需要 qwen-asr 包 + 模型文件 |

> **type 字段含义**: `local` = 本地推理（模型在本机），`cloud` = 调用远程 API。

---

## 语言代码

请求时 `language` 字段使用以下 ISO 639-1 代码（服务内部自动转换为各引擎所需格式）：

| 代码 | 语言 |
|------|------|
| `auto` | 自动检测（默认） |
| `zh` | 中文（普通话） |
| `en` | 英文 |
| `ja` | 日文 |
| `ko` | 韩文 |
| `yue` | 粤语 |

---

## 端点详情

### GET /api/stt/engines

列出所有已注册引擎及其基本信息。

```bash
curl http://localhost:8000/api/stt/engines
```

**响应：**
```json
{
  "engines": [
    {
      "name": "ali_funasr",
      "display_name": "FunASR（本地）",
      "type": "local",
      "vendor": "Alibaba",
      "models": ["SenseVoiceSmall", "paraformer-zh"]
    },
    {
      "name": "ali_qwen",
      "display_name": "Qwen-ASR（云端）",
      "type": "cloud",
      "vendor": "Alibaba",
      "models": ["paraformer-realtime-v2", "paraformer-v2"]
    },
    {
      "name": "qwen_local",
      "display_name": "Qwen3-ASR（本地）",
      "type": "local",
      "vendor": "Alibaba",
      "models": ["Qwen3-ASR-0.6B", "Qwen3-ASR-7B"]
    }
  ]
}
```

---

### GET /api/stt/engines/{name}

获取引擎详细信息，包括当前可用状态、支持的参数和模型。

```bash
curl http://localhost:8000/api/stt/engines/ali_funasr
```

**响应（部分）：**
```json
{
  "name": "ali_funasr",
  "display_name": "FunASR（本地）",
  "type": "local",
  "description": "阿里 FunASR 本地语音识别引擎",
  "version": "1.0.0",
  "available": true,
  "available_reason": "就绪",
  "supported_languages": ["zh", "en", "ja", "ko", "yue", "auto"],
  "requires_api_key": false,
  "default_model": "SenseVoiceSmall",
  "models": [...],
  "parameters": [...]
}
```

> **重要**：`available: false` 时代表依赖未安装或配置缺失，调用 `/transcribe` 会返回 503。先检查此字段再决定是否使用该引擎。

---

### POST /api/stt/transcribe

同步语音识别，上传音频文件，直接返回识别结果。适合 **1 分钟以内**的音频。

**请求（multipart/form-data）：**

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `file` | file | ✅ | - | 音频文件（见支持格式） |
| `engine` | string | ❌ | `ali_funasr` | 引擎名称 |
| `model` | string | ❌ | 引擎默认值 | 模型名称 |
| `language` | string | ❌ | `auto` | 语言代码 |
| `options` | string（JSON） | ❌ | `{}` | 引擎特定参数 |

**支持的音频格式**：mp3、wav、flac、ogg、m4a、aac、webm、mp4、mkv、avi

**示例：**
```bash
# 基础调用（自动检测语言，使用默认引擎）
curl -X POST http://localhost:8000/api/stt/transcribe \
  -F "file=@audio.mp3"

# 指定引擎和语言
curl -X POST http://localhost:8000/api/stt/transcribe \
  -F "file=@audio.mp3" \
  -F "engine=ali_funasr" \
  -F "language=ja"

# 使用云端引擎（需先设置 DASHSCOPE_API_KEY）
curl -X POST http://localhost:8000/api/stt/transcribe \
  -F "file=@audio.mp3" \
  -F "engine=ali_qwen" \
  -F "model=paraformer-v2"

# 使用本地 Qwen3-ASR 引擎
curl -X POST http://localhost:8000/api/stt/transcribe \
  -F "file=@audio.mp3" \
  -F "engine=qwen_local" \
  -F "model=Qwen3-ASR-0.6B" \
  -F "language=ja"

# 传入引擎参数（JSON）
curl -X POST http://localhost:8000/api/stt/transcribe \
  -F "file=@audio.mp3" \
  -F "engine=ali_funasr" \
  -F 'options={"use_itn": true, "max_speakers": 2}'
```

**响应：**
```json
{
  "text": "识别出的完整文本",
  "segments": [
    {
      "start_ms": 0,
      "end_ms": 1500,
      "text": "识别出的"
    },
    {
      "start_ms": 1500,
      "end_ms": 3000,
      "text": "完整文本"
    }
  ],
  "duration_ms": 3000,
  "engine": "ali_funasr",
  "model": "SenseVoiceSmall",
  "language_detected": "ja"
}
```

---

### POST /api/stt/transcribe/async

异步语音识别，立即返回 task_id，通过轮询任务状态获取结果。适合**长音频或批量处理**。

```bash
# 提交任务
curl -X POST http://localhost:8000/api/stt/transcribe/async \
  -F "file=@long_audio.mp3" \
  -F "engine=ali_funasr"
```

**响应：**
```json
{
  "task_id": "abc123",
  "status": "pending",
  "message": "任务已提交"
}
```

```bash
# 轮询任务状态
curl http://localhost:8000/api/stt/tasks/abc123
```

**任务状态响应：**
```json
{
  "task_id": "abc123",
  "status": "completed",
  "result": {
    "text": "识别出的完整文本",
    "segments": [...],
    "duration_ms": 60000,
    "engine": "ali_funasr",
    "model": "SenseVoiceSmall",
    "language_detected": "zh"
  }
}
```

`status` 取值：`pending`（排队中）、`processing`（识别中）、`completed`（已完成）、`failed`（失败）

---

### GET /api/stt/health

健康检查，返回服务状态和依赖信息。

```bash
curl http://localhost:8000/api/stt/health
```

---

## 错误响应

所有错误返回标准 HTTP 状态码 + JSON 详情：

```json
{
  "detail": "错误说明"
}
```

| HTTP 状态码 | 含义 |
|-------------|------|
| `400` | 请求参数错误（如 options 非法 JSON） |
| `404` | 引擎或模型不存在 |
| `500` | 服务器错误（如 FFmpeg 未安装） |
| `503` | 引擎不可用（依赖未安装、API Key 缺失等） |

---

## 启动服务

```bash
# 方式 1：快捷脚本
python run.py

# 方式 2：直接启动（可自定义端口）
python -m backend.app.api.main

# 方式 3：uvicorn（开发模式，热重载）
uvicorn backend.app.api.main:app --host 0.0.0.0 --port 8000 --reload

# 方式 4：Docker
docker run -p 8000:8000 \
  -e STT_MODELS_DIR=/data/models \
  -e DASHSCOPE_API_KEY=sk-xxx \
  -v /path/to/models:/data/models \
  gijiroku-smartasr:latest
```

服务启动后 Swagger 文档可访问：`http://localhost:8000/docs`

---

## 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `STT_MODELS_DIR` | 本地模型目录 | `/data/models` |
| `DASHSCOPE_API_KEY` | 阿里云 API Key（ali_qwen 引擎必需） | `sk-xxxxxxxx` |
| `STT_MODEL_SERVER` | 内网模型服务地址 | `http://192.168.1.100:8765` |
| `FUNASR_HUB` | FunASR 模型来源 | `ms`（ModelScope）/ `hf`（HuggingFace） |
