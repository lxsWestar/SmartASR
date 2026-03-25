# 快速开始

## 安装

### 方式一：pip 安装

```bash
pip install smartasr
```

### 方式二：源码安装

```bash
git clone https://github.com/your-repo/SmartASR.git
cd SmartASR
pip install -e .
```

## 基本使用

### 1. 作为 Python 库

```python
from backend.app.services.stt import transcribe, list_engines

# 查看可用引擎
print(list_engines())

# 执行识别
result = transcribe(
    audio_path="your_audio.mp3",
    engine="ali_funasr",
    language="zh"
)

print(f"识别结果: {result.text}")
print(f"时长: {result.duration_ms / 1000:.1f}秒")
```

### 2. 作为 HTTP 服务

```bash
# 启动服务
python run.py
# 或
python -m backend.app.api.main

# 调用 API
curl -X POST http://localhost:8000/api/stt/audio/transcriptions \
  -F "file=@test.mp3"
```

## 引擎选择

| 引擎名 | 类型 | 特点 | 适用场景 |
|--------|------|------|----------|
| `ali_funasr` | 本地 | 免费，支持 GPU，多语言 | 大量处理、离线场景 |
| `ali_qwen` | 云端 | 高精度，按量计费 | 高质量要求、无需本地 GPU |
| `qwen_local` | 本地 | Qwen3 大模型本地推理，高精度多语言 | 需要最高精度的离线场景 |

## 下一步

- [完整 API 文档](../api/README.md)
- [嵌入到现有项目](embedding.md)
- [开发自定义引擎](engines.md)

