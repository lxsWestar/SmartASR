# 嵌入指南

## 概述

SmartASR 的 STT 服务设计为可独立嵌入任意 Python 项目。

## 嵌入方式

### 方式一：复制 stt 目录

直接复制 `backend/app/services/stt/` 目录到你的项目：

```
your_project/
├── your_code.py
└── services/
    └── stt/          ← 复制整个目录
        ├── __init__.py
        ├── exceptions.py
        ├── dto.py
        ├── base.py
        ├── audio_utils.py
        ├── registry.py
        ├── config.py
        └── engines/
            └── ali_funasr.py  ← 只放需要的引擎
```

然后在代码中导入：

```python
from services.stt import transcribe, list_engines
```

### 方式二：作为依赖安装

```bash
pip install smartasr
```

```python
from backend.app.services.stt import transcribe
```

## 配置

### 环境变量

```bash
export STT_MODELS_DIR=/path/to/models
export STT_CACHE_DIR=/path/to/cache
export STT_DEFAULT_ENGINE=ali_funasr
export DASHSCOPE_API_KEY=your_key  # 云端引擎需要
```

### 代码配置

```python
from backend.app.services.stt.config import STTConfig, set_config
from pathlib import Path

config = STTConfig(
    models_dir=Path("/my/models"),
    default_engine="ali_funasr",
)
set_config(config)
```

## 最小依赖

STT 模块的核心依赖：

- Python >= 3.9
- FFmpeg (系统安装)

引擎特定依赖在安装引擎时自动引入。

## 注意事项

1. **FFmpeg 必须安装**：音频预处理依赖 FFmpeg
2. **模型文件**：本地引擎需要下载模型文件
3. **GPU 支持**：需要安装对应的 CUDA 版本
