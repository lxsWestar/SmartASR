# SmartASR 技术栈分析

> 由 document-project 工作流生成 | 扫描级别: exhaustive | 日期: 2026-03-02

---

## 概览

SmartASR 是一个**单体仓库（Monolith）**，包含两个独立的功能模块：

| 模块 | 路径 | 类型 |
|------|------|------|
| 后端核心 | `backend/` | Python FastAPI 语音识别服务 |
| 前端 UI | `frontend/` | 静态 HTML/CSS/JavaScript Web 应用 |

---

## 后端技术栈

### 核心框架

| 技术 | 版本要求 | 用途 |
|------|---------|------|
| **Python** | >=3.10 | 主要语言 |
| **FastAPI** | >=0.115.0 | REST API 框架 |
| **Uvicorn** | >=0.23.0 | ASGI 服务器 |
| **Pydantic** | 内置于 FastAPI | 请求/响应模型验证 |
| **Starlette** | >=0.40.0 | FastAPI 底层框架 |

### 核心依赖（必装）

| 技术 | 版本要求 | 用途 |
|------|---------|------|
| **Typer** | >=0.9.0 | CLI 框架（基于 Click） |
| **Rich** | >=13.0.0 | 终端美化输出 |
| **python-multipart** | >=0.0.18 | 文件上传支持 |
| **httpx** | >=0.24.0 | 异步 HTTP 客户端（Webhook 回调） |

### 可选依赖 — 按安装组分组

#### `pip install smartasr[api]` — API 服务组

满足 FastAPI 服务运行的依赖（已列于核心框架）。

#### `pip install smartasr[funasr]` — 本地引擎组

| 技术 | 版本要求 | 用途 |
|------|---------|------|
| **FunASR** | >=1.0.0 | 阿里达摩院本地 ASR 框架 |
| **PyTorch** | >=2.0.0 | 深度学习运行时（GPU/CPU） |
| **TorchAudio** | >=2.0.0 | 音频处理 |
| **pydub** | >=0.25.0 | 音频切分、格式转换 |

**隐式依赖（运行时检测）：**
- **FFmpeg** — 系统级依赖，音频格式转换（mp3/m4a/mkv → 16kHz WAV）
- **faster-whisper** — 可选，用于 silero-VAD（更精确的语音段检测）

#### `pip install smartasr[qwen]` — 云端引擎组

| 技术 | 版本要求 | 用途 |
|------|---------|------|
| **DashScope** | >=1.10.0 | 阿里云通义千问 API SDK |

#### `pip install smartasr[dev]` — 开发工具组

| 技术 | 版本要求 | 用途 |
|------|---------|------|
| **pytest** | >=7.0.0 | 测试框架 |
| **pytest-asyncio** | >=0.21.0 | 异步测试支持 |
| **pytest-cov** | >=4.0.0 | 测试覆盖率 |
| **black** | >=23.0.0 | 代码格式化 |
| **isort** | >=5.12.0 | import 排序 |
| **mypy** | >=1.5.0 | 静态类型检查 |

---

## 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **HTML5** | 原生 | 页面结构 |
| **CSS3** | 原生 | 样式布局 |
| **JavaScript (ES6+)** | 原生，无框架 | 交互逻辑、API 调用 |
| **Fetch API** | 浏览器内置 | HTTP 请求 |

**前端特点：**
- 零依赖，无 npm/构建工具
- 单文件结构（index.html + app.js + style.css）
- 通过 FastAPI 后端静态托管，或独立通过文件系统打开

---

## ASR 引擎详情

### 引擎 1：ali_funasr（本地引擎）

| 属性 | 值 |
|------|---|
| 类型 | local |
| 需要 API Key | 否 |
| 需要 GPU | 可选（支持 CPU 降级） |
| 模型来源 | ModelScope（默认）/ HuggingFace |

**支持模型：**

| 模型名 | 大小 | 支持语言 | 特点 |
|--------|------|---------|------|
| `SenseVoiceSmall` | ~900MB | zh/en/ja/ko/yue | 多语言，仅 ModelScope |
| `paraformer-zh` | ~1.2GB | zh | 中文专用，支持说话人分离 |

**配套模型（VAD/标点）：**
- `fsmn-vad` — 语音活动检测，~100MB
- `ct-punc` — 标点恢复（paraformer 专用）
- `cam++` — 说话人分离（可选）

### 引擎 2：ali_qwen（云端引擎）

| 属性 | 值 |
|------|---|
| 类型 | cloud |
| 需要 API Key | 是（`DASHSCOPE_API_KEY`） |
| 依赖网络 | 是 |
| API 提供商 | 阿里云 DashScope |

**支持模型：**

| 模型名 | 特点 |
|--------|------|
| `qwen3-asr-flash` | 低延迟，快速识别（默认） |
| `qwen3-asr-turbo` | 高精度，离线批处理 |

---

## VAD（语音活动检测）子系统

SmartASR 实现了一套多后端 VAD 系统，按优先级自动选择：

| 优先级 | 方法 | 来源 | 精度 | 是否需要下载模型 |
|--------|------|------|------|----------------|
| 1 | **silero-vad** | faster-whisper 内置 | 高 | 否 |
| 2 | **funasr fsmn-vad** | FunASR 框架 | 高 | 是（~100MB） |
| 3 | **pydub 静音检测** | pydub 内置 | 低 | 否 |

---

## 模型管理子系统

配置类 `ModelSourceConfig` 实现三级模型来源策略：

```
加载顺序: local → network → official
```

| 来源 | 描述 | 配置键 |
|------|------|--------|
| `local` | 本地预下载目录 | `STT_MODELS_DIR` 或 `config.json:model_source.local_dir` |
| `network` | 内网模型服务器 | `STT_MODEL_SERVER` 或 `config.json:model_source.network_server` |
| `official` | HuggingFace / ModelScope | `FUNASR_HUB=hf\|ms` |

---

## 系统依赖

| 依赖 | 版本要求 | 安装方式 | 用途 |
|------|---------|---------|------|
| **Python** | >=3.10 | python.org | 运行时 |
| **FFmpeg** | 任意 | 系统包管理器 | 音频格式转换 |
| **CUDA（可选）** | >=11.8 | NVIDIA | GPU 加速（FunASR） |

---

## 构建工具

| 工具 | 用途 |
|------|------|
| **setuptools** | Python 包构建 |
| **pyproject.toml** | 统一项目配置（PEP 517/518） |
| **pip** | 依赖安装 |

---

## 技术决策说明

1. **为什么选 FastAPI 而非 Flask/Django？**
   - 原生异步支持，适合长时间识别任务
   - 自动 OpenAPI 文档生成（`/documents`）
   - Pydantic 模型验证

2. **为什么用 Typer 而非 argparse？**
   - 基于类型提示，代码更简洁
   - 与 Rich 集成，提供美化终端输出

3. **为什么前端不使用 React/Vue？**
   - 文件体积小，无构建步骤
   - 直接由后端托管为静态文件
   - 适合轻量级工具类应用

4. **为什么引擎用插件注册模式？**
   - 新引擎只需：继承 `BaseSTTEngine` → 用 `@register_engine` 装饰 → 放入 `engines/` 目录
   - 删除文件即移除引擎，无需修改核心代码
