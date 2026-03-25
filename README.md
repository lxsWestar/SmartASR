# SmartASR

轻量级语音转文字服务

## 项目简介

SmartASR 是一个从 `pyvideotrans` 提取的独立语音识别服务，专注于 **音频输入 → 文字输出**。

### 📄 许可证

本项目采用 **MIT License**，可用于商业项目。

**关于 `pyvideotrans/` 文件夹：**
- 该文件夹内容来自 [pyvideotrans](https://github.com/jianchang512/pyvideotrans) 项目（GPL v3 协议）
- 此文件夹**仅作设计参考和测试对比**，不是 SmartASR 的运行时依赖
- SmartASR 核心代码（`backend/`）为**独立实现**，遵循 MIT 协议
- 如不需要参考功能，可安全删除 `pyvideotrans/` 文件夹

### 特性

- **单一职责** - 只做语音识别，不做字幕/视频处理
- **三种使用方式** - CLI 命令行 / HTTP API / Python 库
- **插件架构** - 引擎可热插拔，放文件即注册
- **三段式模型加载** - 本地 → 内网服务器 → 官方源
- **跨平台** - Windows / Linux / macOS

### 支持的引擎

| 引擎名 | 类型 | 特点 | 依赖 |
|--------|------|------|------|
| `ali_funasr` | 本地 | SenseVoiceSmall (多语言) / Paraformer (中文) | `pip install funasr torch` |
| `ali_qwen` | 云端 | 通义千问大模型，按量计费 | `pip install dashscope` + API Key |
| `qwen_local` | 本地 | Qwen3-ASR 大模型本地推理，高精度多语言 | `pip install qwen-asr soundfile torch` + 模型文件 |

---

## 快速开始

### 1. 下载与安装

```bash
# Step 1: 克隆仓库
git clone https://github.com/xxx/SmartASR.git
cd SmartASR
```

#### 方式 A: 使用 uv (推荐，更快)

```bash
# 安装 uv (如果没有)
pip install uv

# 创建虚拟环境并安装
uv venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
uv pip install -e ".[api,funasr]"    # 本地识别 + API服务
```

#### 方式 B: 使用 pip (传统)

```bash
# 创建虚拟环境
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -e ".[api,funasr]"    # 本地识别 + API服务
```

#### 安装选项说明

| 选项 | 说明 | 大小 |
|------|------|------|
| `.[api,funasr]` | 本地识别 (FunASR) + API服务 (推荐) | ~2-3GB |
| `.[api,qwen]` | 云端识别 (Qwen API) + API服务 | ~50MB |
| `.[api,qwen_local]` | 本地识别 (Qwen3-ASR) + API服务 | ~2-3GB |
| `.[all]` | 完整安装 (含开发工具) | ~3GB |

### 2. 验证安装

```bash
# 检查 CLI 可用
python -m backend.app.cli --help
```

### 2. 启动服务

```bash
# 方式 1: 使用快捷脚本 (推荐)
python run.py

# 方式 2: 使用 CLI
smartasr serve

# 方式 3: 直接调用模块
python -m backend.app.cli serve
```

启动后访问 **http://localhost:8000** 即可看到前端界面。

### 3. 选择使用方式

| 方式 | 适用场景 | 详细文档 |
|------|---------|---------|
| **CLI 命令行** | 脚本、批量处理、快速测试 | [CLI 文档](backend/app/cli/README.md) |
| **HTTP API** | Web 服务、微服务集成 | [API 文档](backend/app/api/README.md) |
| **Python 库** | 嵌入现有项目 | [库文档](backend/app/services/stt/README.md) |

#### 快速示例

```bash
# CLI
smartasr transcribe audio.mp3 -o result.srt

# API
curl -X POST http://localhost:8000/api/stt/audio/transcriptions -F "file=@audio.mp3"

# Python
from backend.app.services.stt import transcribe
result = transcribe("audio.mp3")
print(result.text)
```

---

## 初次配置

### 引擎配置

根据你的需求选择：

#### 方式 A: 云端模型 (无需下载)

```bash
# 设置 API Key
export DASHSCOPE_API_KEY="sk-xxxxxxxx"

# 使用
smartasr transcribe -e ali_qwen audio.mp3
```

#### 方式 B: 本地模型 (自动下载)

```bash
# 无需配置，首次运行自动下载
smartasr transcribe audio.mp3
```

#### 方式 C: 本地模型 (手动指定目录)

```bash
# 设置模型目录
export STT_MODELS_DIR="./models"   # 或 D:\models\funasr

# 目录结构
models/
├── SenseVoiceSmall/   # 多语言 (zh/en/ja/ko/yue)
├── paraformer-zh/     # 中文专用
├── fsmn-vad/          # VAD (可选)
└── ct-punc/           # 标点 (可选)
```

#### 方式 D: 内网服务器下载

```bash
# 配置内网模型服务器
export STT_MODEL_SERVER="http://192.168.1.100:8765"
```

### 模型加载优先级 (三段式)

```
┌─────────────────────────┐
│ 1. 本地目录              │  STT_MODELS_DIR
└───────────┬─────────────┘
            ↓ (未找到)
┌─────────────────────────┐
│ 2. 内网服务器            │  STT_MODEL_SERVER
└───────────┬─────────────┘
            ↓ (不可用)
┌─────────────────────────┐
│ 3. 官方源自动下载        │  ModelScope / HuggingFace
└─────────────────────────┘
```

### 环境变量一览

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `STT_MODELS_DIR` | 本地模型目录 | `./models` |
| `STT_MODEL_SERVER` | 内网模型服务 | `http://192.168.1.100:8765` |
| `DASHSCOPE_API_KEY` | 阿里云 API Key | `sk-xxxxxxxx` |
| `FUNASR_HUB` | 官方源选择 | `ms` (ModelScope) / `hf` (HuggingFace) |

---

## 项目结构

```
SmartASR/
├── README.md                    # 本文件 (项目概述)
├── backend/
│   └── app/
│       ├── cli/                 # 命令行工具
│       │   └── README.md        # CLI 详细文档
│       ├── api/                 # HTTP API 服务
│       │   └── README.md        # API 详细文档
│       └── services/stt/        # 核心库 (可独立嵌入)
│           └── README.md        # 库详细文档
├── frontend/                    # Web 前端界面
├── models/                      # 本地模型目录 (gitignore)
├── scripts/                     # 工具脚本
├── tests/                       # 测试用例
└── documents/                        # 额外文档
```

---

## 各模块详细文档

| 模块 | 说明 | 文档链接 |
|------|------|---------|
| **CLI** | 命令行工具，支持批量处理、多种输出格式 | [backend/app/cli/README.md](backend/app/cli/README.md) |
| **API** | RESTful API，支持同步/异步识别 | [backend/app/api/README.md](backend/app/api/README.md) |
| **库** | 核心 Python 库，可嵌入任意项目 | [backend/app/services/stt/README.md](backend/app/services/stt/README.md) |
| **前端** | Web 界面 | [frontend/README.md](frontend/README.md) |

---

## 开发

### 运行测试

```bash
pytest tests/unit/                    # 单元测试 (123 tests)
pytest tests/integration/             # 集成测试 (需要模型)
pytest tests/ --cov=backend           # 带覆盖率
```

### 开发新引擎

1. 复制 `backend/app/services/stt/engines/_template.py`
2. 实现抽象方法
3. 放入 `engines/` 目录，自动注册

详见 [引擎开发指南](documents/guides/engines.md)

---

## 许可证

MIT License

