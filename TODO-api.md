# SmartASR: API 端点设计与实现状态

> 🔧 本文件详细描述所有 API 端点的设计规范和实现状态。

---

## API 概览

| 分类 | 端点数 | 状态 |
|------|--------|------|
| 引擎管理 | 4 | ✅ 已完成 |
| 转写 API | 5 | ✅ 已完成 |
| Webhook | 3 | ⏳ 部分完成 |
| 批量处理 | 4 | 🔲 待开发 |
| 模型管理 | 4 | 🔲 待开发 |
| 文件管理 | 5 | ✅ 已完成 |
| 配置管理 | 5 | ✅ 已完成 |
| 健康检查 | 3 | ✅ 已完成 |
| 统计指标 | 2 | 🔲 待开发 |

---

## 1. 引擎管理 API ✅

### GET /api/stt/engines
- [x] 返回所有可用引擎列表
- 响应示例:
```json
{
  "engines": [
    {
      "name": "ali_funasr",
      "display_name": "阿里 FunASR (本地)",
      "type": "local",
      "models": ["SenseVoiceSmall", "paraformer-zh"]
    }
  ]
}
```

### GET /api/stt/engines/{engine_name}
- [ ] 返回单个引擎详细信息
- 响应示例:
```json
{
  "name": "ali_funasr",
  "display_name": "阿里 FunASR (本地)",
  "type": "local",
  "available": true,
  "models": ["SenseVoiceSmall", "paraformer-zh"],
  "default_model": "SenseVoiceSmall",
  "supported_languages": ["zh", "en", "ja", "ko", "auto"],
  "parameters": {...}
}
```

### GET /api/stt/engines/{engine_name}/models
- [x] 返回引擎支持的模型列表

### GET /api/stt/engines/{engine_name}/models/{model_name}
- [x] 返回单个模型的详细参数

---

## 2. 转写 API ✅

### POST /api/stt/transcribe
- [x] 同步识别 (适合短音频)
- 请求: `multipart/form-data`
  - `file`: 音频文件 (必填)
  - `engine`: 引擎名称 (可选)
  - `model`: 模型名称 (可选)
  - `language`: 语言 (可选)
  - `options`: JSON 字符串 (可选)
- 响应:
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

### POST /api/stt/transcribe/async
- [x] 异步识别 (适合长音频)
- 响应:
```json
{
  "task_id": "uuid-xxxx-xxxx",
  "status": "pending",
  "message": "任务已提交"
}
```

### GET /api/stt/tasks/{task_id}
- [x] 查询异步任务状态
- 响应 (进行中):
```json
{
  "task_id": "uuid-xxxx",
  "status": "processing",
  "progress": 0.45
}
```
- 响应 (完成):
```json
{
  "task_id": "uuid-xxxx",
  "status": "completed",
  "progress": 1.0,
  "result": {...}
}
```

### GET /api/stt/tasks
- [x] 列出所有任务
- 查询参数: `status`, `limit`, `offset`

### DELETE /api/stt/tasks/{task_id}
- [x] 取消/删除任务

---

## 3. Webhook 回调 ⏳

### POST /api/stt/transcribe/async (扩展)
- [x] 增加 `callback_url` 参数
- 请求扩展:
```json
{
  "callback_url": "https://your-server.com/webhook",
  "callback_headers": {"Authorization": "Bearer xxx"}
}
```
- 任务完成时回调:
```json
{
  "event": "task.completed",
  "task_id": "uuid-xxxx",
  "status": "completed",
  "result": {...}
}
```

### GET /api/stt/webhooks
- [ ] 列出已注册的 webhook

### POST /api/stt/webhooks/test
- [ ] 测试 webhook 连通性

---

## 4. 批量处理 API 🔲

### POST /api/stt/transcribe/batch
- [ ] 批量提交多个文件
- 请求: `multipart/form-data`
  - `files[]`: 多个音频文件
  - `engine`, `model`, `language`: 共享参数
  - `callback_url`: 批次完成回调 (可选)
- 响应:
```json
{
  "batch_id": "batch-uuid-xxxx",
  "tasks": [
    {"task_id": "task-1", "filename": "audio1.mp3"},
    {"task_id": "task-2", "filename": "audio2.mp3"}
  ],
  "total": 2
}
```

### GET /api/stt/batches/{batch_id}
- [ ] 查询批次状态

### GET /api/stt/batches
- [ ] 列出所有批次

### DELETE /api/stt/batches/{batch_id}
- [ ] 取消整个批次

---

## 5. 模型管理 API (本地引擎) 🔲

### GET /api/stt/models/status
- [ ] 获取所有模型加载状态
- 响应:
```json
{
  "models": [
    {
      "engine": "ali_funasr",
      "model": "SenseVoiceSmall",
      "loaded": true,
      "device": "cuda:0",
      "memory_mb": 1200
    }
  ]
}
```

### POST /api/stt/models/preload
- [ ] 预加载模型到内存/显存
- 请求:
```json
{
  "engine": "ali_funasr",
  "model": "SenseVoiceSmall",
  "device": "cuda"
}
```

### DELETE /api/stt/models/unload
- [ ] 卸载模型释放内存

### POST /api/stt/models/download
- [ ] 下载模型 (不加载)

---

## 6. 文件管理 API ✅

### GET /api/stt/files
- [x] 列出已上传的临时文件
- 查询参数: `status`, `before`, `after`, `limit`, `offset`
- 响应:
```json
{
  "files": [
    {
      "file_id": "uuid",
      "filename": "audio.mp3",
      "size_mb": 5.2,
      "uploaded_at": "2024-01-01T00:00:00Z",
      "expires_at": "2024-01-02T00:00:00Z",
      "status": "available"
    }
  ],
  "total_count": 10,
  "total_size_mb": 50.5
}
```

### GET /api/stt/files/{file_id}
- [x] 获取单个文件信息

### DELETE /api/stt/files/{file_id}
- [x] 手动删除文件

### POST /api/stt/files/cleanup
- [x] 清理过期文件
- 支持 `dry_run` 预览模式

### GET /api/stt/files/stats
- [x] 获取文件统计信息

---

## 7. 配置管理 API ✅

### GET /api/stt/config
- [x] 获取当前服务配置
- 响应:
```json
{
  "default_engine": "ali_funasr",
  "default_language": "auto",
  "max_file_size_mb": 500,
  "api_timeout": 300,
  "supported_formats": ["mp3", "wav", ...],
  "models_dir": "/path/to/models",
  "api_keys": {
    "ali_qwen": {"configured": true, "masked": "sk-***xxx"}
  }
}
```

### PUT /api/stt/config
- [x] 更新服务配置

### PUT /api/stt/config/api-keys/{engine_name}
- [x] 设置引擎 API Key

### DELETE /api/stt/config/api-keys/{engine_name}
- [x] 删除引擎 API Key

### GET /api/stt/config/api-keys
- [x] 获取所有 API Key 状态

---

## 8. 健康检查 ✅

### GET /api/stt/health
- [x] 服务健康状态
- 响应:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-01-26T...",
  "ffmpeg": {"available": true, "version": "6.0"},
  "system": {"cuda_available": true, "cuda_device_count": 1},
  "engines": {
    "ali_funasr": {"available": true},
    "ali_qwen": {"available": true}
  }
}
```

### GET /api/stt/health/simple
- [x] 快速存活检查 (负载均衡器)

### GET /api/stt/health/ready
- [x] 就绪检查 (Kubernetes)

---

## 9. 使用统计 🔲

### UsageInfo 数据结构 (已实现)
```python
@dataclass
class UsageInfo:
    audio_duration_ms: int = 0
    processing_time_ms: int = 0
    api_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    characters: int = 0
```

### 引擎返回的 Usage 差异

| 引擎 | 能返回的字段 |
|------|-------------|
| **ali_qwen** | audio_duration_ms, processing_time_ms, api_calls, input_tokens, output_tokens, characters |
| **ali_funasr** | audio_duration_ms, processing_time_ms, characters |

### 响应示例
```json
{
  "text": "识别的完整文本...",
  "segments": [...],
  "usage": {
    "audio_duration_ms": 60000,
    "processing_time_ms": 3500,
    "api_calls": 6,
    "input_tokens": 12000,
    "output_tokens": 500,
    "characters": 850
  }
}
```

### GET /api/stt/stats
- [ ] 使用量统计 (需要存储支持)

### GET /api/stt/metrics
- [ ] Prometheus 格式指标

---

## 10. 错误处理

### 统一错误响应格式
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
| 错误码 | 说明 |
|--------|------|
| `ENGINE_NOT_FOUND` | 引擎不存在 |
| `MODEL_NOT_FOUND` | 模型不存在 |
| `MODEL_NOT_LOADED` | 模型未加载 |
| `FILE_TOO_LARGE` | 文件过大 |
| `UNSUPPORTED_FORMAT` | 不支持的格式 |
| `API_KEY_MISSING` | 缺少 API Key |
| `API_KEY_INVALID` | API Key 无效 |
| `TRANSCRIPTION_FAILED` | 识别失败 |
| `TASK_NOT_FOUND` | 任务不存在 |
| `TASK_CANCELLED` | 任务已取消 |
| `BATCH_NOT_FOUND` | 批次不存在 |
| `WEBHOOK_FAILED` | Webhook 回调失败 |
| `NO_ENGINES_AVAILABLE` | 无可用引擎 |
| `FFMPEG_NOT_FOUND` | FFmpeg 未安装 |
| `QUOTA_EXCEEDED` | 配额耗尽 |
