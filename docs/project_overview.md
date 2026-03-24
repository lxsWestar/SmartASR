# SmartASR 项目概述

> 由 document-project 工作流生成 | 扫描级别: exhaustive | 日期: 2026-03-02

---

## 什么是 SmartASR？

SmartASR 是一个**轻量级语音转文字（ASR/STT）统一服务**，提供：

- **REST API**：通过 HTTP 接口调用多种语音识别引擎
- **命令行工具**：直接从终端转录音频文件
- **嵌入式库**：将 `backend/app/services/stt/` 作为 Python 库嵌入其他项目

### 核心价值

1. **引擎统一** — 本地引擎（FunASR）和云端引擎（通义千问）使用同一接口
2. **离线可用** — 本地引擎完全离线运行，支持内网模型服务器
3. **插件化** — 新增引擎无需修改核心代码，放文件即注册

---

## 项目基本信息

| 属性 | 值 |
|------|---|
| 项目名称 | SmartASR |
| 版本 | 0.1.0 (Alpha) |
| 许可证 | MIT |
| 主要语言 | Python 3.10+ |
| 次要语言 | JavaScript (前端) |
| 主框架 | FastAPI |
| 包类型 | 单体仓库（Monolith） |

---

## 支持的引擎

| 引擎 ID | 引擎名称 | 类型 | 支持语言 | 需要 API Key |
|---------|---------|------|---------|-------------|
| `ali_funasr` | 阿里 FunASR | 本地 | zh/en/ja/ko/yue | 否 |
| `ali_qwen` | 通义千问 ASR | 云端 | zh/en/ja/ko/auto | 是 |

---

## 快速使用

### 安装

```bash
pip install -e ".[api,funasr]"    # 安装 API 服务 + FunASR 本地引擎
# 或
pip install -e ".[all]"           # 安装所有组件
```

### 启动服务

```bash
smartasr serve                    # 启动 API 服务（http://localhost:8000）
```

### 命令行识别

```bash
smartasr transcribe audio.mp3                        # 基础识别
smartasr transcribe audio.mp3 -o result.srt          # 输出 SRT 字幕
smartasr transcribe audio.mp3 --engine ali_qwen      # 使用云端引擎
```

### API 调用

```bash
curl -X POST http://localhost:8000/api/stt/transcribe \
  -F "file=@audio.mp3" -F "engine=ali_funasr"
```

---

## 项目结构概览

```
SmartASR/
├── backend/          # Python 后端（FastAPI + STT 服务库）
├── frontend/         # 静态 Web UI（零依赖 HTML/JS/CSS）
├── tests/            # pytest 测试套件（unit/integration/e2e）
├── scripts/          # 模型下载和内网服务器脚本
├── models/           # 模型元数据（非模型权重文件）
├── docs/             # 棕地上下文文档（AI 协作用）
├── documents/        # 设计文档和用户指南
└── pyproject.toml    # 项目配置（依赖/工具/构建）
```

---

## 核心概念

### 引擎（Engine）

语音识别的执行单元。每个引擎继承 `BaseSTTEngine` 并实现：
- `transcribe(STTRequest) → STTResponse`
- `get_metadata() → EngineMetadata`
- `check_available() → Tuple[bool, str]`
- `get_models() → List[str]`

### 任务（Task）

异步识别的工作单元。状态：`pending → processing → completed/failed/cancelled`

识别进度通过 `GET /api/stt/tasks/{task_id}` 轮询获取。

### 模型来源策略

按优先级自动选择：**本地目录** → **内网服务器** → **官方 Hub（HuggingFace/ModelScope）**

### VAD（语音活动检测）

将长音频切分为语音片段，避免静音段占用识别资源。SmartASR 支持三种 VAD 后端，按可用性自动选择。

---

## 依赖关系图

```
核心（必装）：Python 3.10+ + FFmpeg + typer + rich
     │
     ├── [api] FastAPI + uvicorn + httpx + python-multipart
     │         └── Web UI（frontend/）
     │
     ├── [funasr] funasr + torch + torchaudio + pydub
     │         └── 本地引擎（ali_funasr）
     │
     └── [qwen] dashscope
               └── 云端引擎（ali_qwen）
```

---

## 参考资料

- FunASR: https://github.com/modelscope/FunASR
- SenseVoice: https://github.com/FunAudioLLM/SenseVoice
- DashScope: https://dashscope.console.aliyun.com/
- ModelScope: https://modelscope.cn/
- 设计参考（非代码复制）: pyvideotrans (GPL v3)
