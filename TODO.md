# SmartASR: 轻量级语音转文字 API 服务 - 开发计划总览

> 📋 本文件是 TODO 系列的入口，细分计划已拆分到独立文件中。

## 快速导航

| 文档 | 内容 | 状态 |
|------|------|------|
| [TODO-overview.md](TODO-overview.md) | 项目定位、架构、里程碑总览 | 📖 概述 |
| [TODO-milestones.md](TODO-milestones.md) | M1-M11 里程碑详细任务清单 | ✅ 核心进度 |
| [TODO-api.md](TODO-api.md) | API 端点设计与实现状态 | 🔧 API 规范 |
| [TODO-reference.md](TODO-reference.md) | pyvideotrans 源码参考 | 📚 参考资料 |
| [TODO-future.md](TODO-future.md) | 后续扩展与部署计划 | 🚀 未来规划 |

---

## 里程碑进度速览

| 里程碑 | 目标 | 状态 |
| :--- | :--- | :--- |
| M1 | 项目骨架 + 异常类 + 跨平台基础 | ✅ 已完成 |
| M2 | 音频预处理模块 (跨平台) + VAD 工具 | ✅ 已完成 |
| M3 | DTO + 引擎接口 + 引擎元数据规范 | ✅ 已完成 |
| M4 | 引擎注册中心 (自动发现) | ✅ 已完成 |
| M5 | FunASR 引擎 | ✅ 已完成 |
| M6 | Qwen-ASR 引擎 | ✅ 已完成 |
| M7 | API 路由层 (完整版) | ✅ 已完成 |
| M8 | 测试 + 文档 + 嵌入指南 | ✅ 单元测试完成 (135 tests) |
| M9 | 依赖检查 + 友好提示 | 🔲 待开发 |
| M10 | 模型源配置 + 内网分发 | ✅ 已完成 |
| M11 | 命令行工具 (CLI) | ✅ 已完成 |

---

## 当前项目结构

```
SmartASR/
├── README.md                          # 项目说明
├── TODO.md                            # 开发计划入口 (本文件)
├── TODO-*.md                          # 细分计划文档
├── AGENTS.md                          # AI 协作规范
│
├── backend/                           # 后端代码
│   └── app/
│       ├── api/                       # API 路由层
│       │   ├── main.py               # FastAPI 应用入口
│       │   └── routers/              # 路由模块
│       ├── cli/                       # 命令行工具 ✨
│       │   ├── commands/             # 子命令
│       │   ├── formatters/           # 输出格式器
│       │   └── utils/                # CLI 工具函数
│       └── services/
│           └── stt/                   # STT 核心服务
│               ├── engines/          # 引擎插件目录
│               └── ...               # 核心模块
│
├── docs/                              # 文档
├── tests/                             # 测试
└── pyvideotrans/                      # 参考项目 (只读)
```

---

## 设计原则

- **单一职责**: 只做语音识别，不做字幕处理、视频处理等
- **插件架构**: 引擎可热插拔，放文件即注册，删除即移除
- **双模式**: 可作为 HTTP API 服务，也可作为 Python 库导入
- **跨平台**: Windows/Linux 通用，可嵌入任意 Python 项目
- **零配置启动**: 无引擎文件时优雅降级，不报错

---

## 如何使用

### CLI 方式 (推荐)
```bash
# 单文件转写
python -m backend.app.cli transcribe audio.mp3 -o result.srt

# 查看可用引擎
python -m backend.app.cli engines list

# 启动 API 服务
python -m backend.app.cli serve --port 8000
```

### API 方式
```bash
# 启动服务
python -m backend.app.api.main

# 调用 API
curl -X POST http://localhost:8000/api/stt/transcribe \
  -F "file=@audio.mp3" \
  -F "engine=ali_funasr"
```

### Python 库方式
```python
from backend.app.services.stt import transcribe, list_engines

# 查看可用引擎
engines = list_engines()

# 识别音频
result = transcribe("audio.mp3", engine="ali_funasr")
print(result.text)
```

---

> 📌 **详细内容请查看各细分文档：**
> - 项目架构详情 → [TODO-overview.md](TODO-overview.md)
> - 里程碑任务清单 → [TODO-milestones.md](TODO-milestones.md)
> - API 端点规范 → [TODO-api.md](TODO-api.md)
> - 源码参考 → [TODO-reference.md](TODO-reference.md)
> - 未来规划 → [TODO-future.md](TODO-future.md)
