# SmartASR API 参考

## 概述

SmartASR 提供两种使用方式：

1. **HTTP API 服务** - 独立运行的 REST API
2. **Python 库** - 直接导入到你的项目

## 快速示例

### Python 库方式

```python
from backend.app.services.stt import transcribe, list_engines

# 列出可用引擎
engines = list_engines()

# 执行语音识别
result = transcribe("audio.mp3", engine="ali_funasr")
print(result.text)
```

### HTTP API 方式

```bash
# 启动服务
python -m SmartASR.server --port 8080

# 调用 API
curl -X POST http://localhost:8080/api/v1/transcribe \
  -F "audio=@audio.mp3" \
  -F "engine=ali_funasr"
```

## API 端点

### POST /api/v1/transcribe

执行语音识别。

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| audio | file | 是 | 音频文件 |
| engine | string | 否 | 引擎名称，默认 ali_funasr |
| language | string | 否 | 语言代码，默认 auto |
| model | string | 否 | 模型名称 |

**响应示例：**

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
  "language_detected": "zh"
}
```

### GET /api/v1/engines

列出所有可用引擎。

**响应示例：**

```json
{
  "engines": [
    {
      "name": "ali_funasr",
      "display_name": "阿里 FunASR (本地)",
      "type": "local",
      "available": true
    }
  ]
}
```

### GET /api/v1/engines/{name}

获取引擎详细信息。

## 错误码

| 错误码 | 说明 |
|--------|------|
| FFMPEG_NOT_FOUND | FFmpeg 未安装 |
| ENGINE_NOT_FOUND | 引擎不存在 |
| MODEL_NOT_FOUND | 模型不存在 |
| API_KEY_MISSING | API Key 缺失 |
| TRANSCRIPTION_ERROR | 识别失败 |
| FILE_TOO_LARGE | 文件过大 |
| UNSUPPORTED_FORMAT | 不支持的格式 |
