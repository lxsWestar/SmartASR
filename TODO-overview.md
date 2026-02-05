# SmartASR: 项目定位与架构概述

> 📖 本文件描述项目的核心定位、架构设计和里程碑规划。

---

## 项目定位

**核心功能**: 音频输入 → 文字输出，仅此而已。

本项目从 `pyvideotrans` 中提取 STT 核心逻辑，构建为独立的 API 后端服务。

---

## 设计原则

- **单一职责**: 只做语音识别，不做字幕处理、视频处理等
- **插件架构**: 引擎可热插拔，放文件即注册，删除即移除
- **双模式**: 可作为 HTTP API 服务，也可作为 Python 库导入
- **跨平台**: Windows/Linux 通用，可嵌入任意 Python 项目
- **零配置启动**: 无引擎文件时优雅降级，不报错

---

## 跨平台设计

```
┌─────────────────────────────────────────────────────────────┐
│                    SmartASR 微服务                          │
├─────────────────────────────────────────────────────────────┤
│  使用方式 A: 独立 HTTP 服务                                  │
│  $ python -m SmartASR.server --port 8080                    │
│                                                             │
│  使用方式 B: 嵌入现有项目                                    │
│  from SmartASR import transcribe                            │
│  result = transcribe("audio.mp3", engine="ali_funasr")      │
│                                                             │
│  使用方式 C: 复制 stt/ 目录到任意项目                        │
│  your_project/                                              │
│  └── services/                                              │
│      └── stt/          ← 直接复制整个目录                   │
│          └── engines/  ← 只放你需要的引擎文件               │
└─────────────────────────────────────────────────────────────┘
```

---

## 插件架构核心理念

```
engines/
├── __init__.py          # 自动扫描本目录所有 .py 文件
├── ali_funasr.py        # 放这个文件 → FunASR 可用
├── ali_qwen.py          # 放这个文件 → Qwen-ASR 可用
├── whisper.py           # 放这个文件 → Whisper 可用
└── (删除文件 = 移除引擎，无需改任何代码)
```

---

## 初期支持引擎

> ⚠️ **注意**: 当前两个引擎为初期实现，用于**验证插件架构的可行性**。
> 
> 🎯 **核心目标**: 支持多种 ASR 引擎像"卡片"一样**即插即用** —— 放入文件即注册，删除文件即移除，无需修改任何其他代码。验证通过后，将陆续接入 Whisper、Google、Azure 等主流引擎。

| 引擎 | 类型 | 特点 | 状态 |
|------|------|------|------|
| **阿里 FunASR** | 本地 | SenseVoiceSmall / Paraformer，免费，支持 GPU | ✅ 初期验证 |
| **阿里百炼 Qwen-ASR** | 云端 | 通义千问大模型，按量计费 | ✅ 初期验证 |
| Faster-Whisper | 本地 | OpenAI Whisper 加速版，多语言 | 🔲 计划中 |
| OpenAI Whisper API | 云端 | 官方 API，高精度 | 🔲 计划中 |
| Google Cloud STT | 云端 | 企业级，多语言 | 🔲 计划中 |
| Azure Speech | 云端 | 微软云，实时转写 | 🔲 计划中 |

---

## 里程碑总览

| 里程碑 | 目标 | 预估工期 | 前置依赖 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| M1 | 项目骨架 + 异常类 + 跨平台基础 | 0.5天 | 无 | ✅ 已完成 |
| M2 | 音频预处理模块 (跨平台) + VAD 工具 | 0.5天 | M1 | ✅ 已完成 |
| M3 | DTO + 引擎接口 + 引擎元数据规范 | 0.5天 | M1 | ✅ 已完成 |
| M4 | 引擎注册中心 (自动发现) | 1天 | M3 | ✅ 已完成 |
| M5 | FunASR 引擎 | 1天 | M2, M4 | ✅ 已完成 |
| M6 | Qwen-ASR 引擎 | 1天 | M4 | ✅ 已完成 |
| M7 | API 路由层 (完整版) | 1.5天 | M5, M6 | ✅ 已完成 |
| M8 | 测试 + 文档 + 嵌入指南 | 0.5天 | M7 | ✅ 单元测试完成 (135 tests) |
| M9 | 依赖检查 + 友好提示 | 0.5天 | M4 | 🔲 待开发 |
| M10 | 模型源配置 + 内网分发 | 0.5天 | M5 | ✅ 已完成 |
| M11 | 命令行工具 (CLI) | 0.5天 | M7 | ✅ 已完成 |

**总预估**: 8 天

---

## 关键约束

### 1. CUDA 处理
- 默认尝试 CUDA，失败自动回退 CPU
- 使用 `torch.cuda.is_available()` 检测

### 2. 显存管理
- 任务结束后调用 `gc.collect()` + `torch.cuda.empty_cache()`

### 3. 模型下载
- 检测 HuggingFace 连通性
- 超时自动切换镜像: `https://hf-mirror.com`

---

## VAD (语音活动检测) 架构

> **分析日期**: 2026-01-26
> **结论**: VAD 作为**独立工具模块** (`vad_utils.py`)，引擎按需调用

### 参考项目 VAD 策略分类

| 类别 | 引擎 | VAD 方式 | 时间戳来源 |
|------|------|----------|------------|
| **原生时间戳** | FunASR (paraformer), Deepgram, WhisperX, ElevenLabs | 无需 VAD | API 直接返回 |
| **使用 cut_audio()** | Qwen-ASR, Gemini, OpenAI API, HuggingFace, AI302 | `faster_whisper.vad` | 本地 VAD 切分 |
| **自有 VAD** | Google, FunASR (SenseVoice) | `pydub` / `funasr.fsmn-vad` | 各自实现 |

### VAD 方法对比

| 方法 | 库 | 依赖大小 | 精度 | 速度 | 适用场景 |
|------|-----|---------|------|------|----------|
| `faster_whisper.vad` | silero-vad | ~5MB | 高 | 快 | 通用推荐 |
| `funasr.fsmn-vad` | funasr | ~100MB | 高 | 中 | 已装 FunASR 时 |
| `pydub.detect_nonsilent` | pydub | ~1MB | 中 | 快 | 轻量级场景 |
| `webrtcvad` | webrtcvad | ~100KB | 中 | 最快 | 实时流式 |

### 设计决策

```
❌ 方案 A: VAD 放在 BaseSTTEngine 基类
   问题: 强制所有引擎依赖 VAD，包括原生支持时间戳的引擎

❌ 方案 B: VAD 在每个引擎中各自实现
   问题: 代码重复，维护困难

✅ 方案 C: VAD 作为独立工具模块 (vad_utils.py)
   优点: 
   - 引擎按需导入，无强制依赖
   - 代码复用，统一维护
   - 支持多种 VAD 后端切换
   - 原生时间戳引擎完全不受影响
```
