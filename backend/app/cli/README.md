# cli/ - 命令行界面模块

> **SmartASR CLI**: 产品级命令行语音识别工具

## 职责

提供完整的命令行界面，支持：
- 单文件/批量语音识别
- 多种输出格式 (txt, srt, vtt, json, tsv)
- 引擎管理与配置
- API 服务启动
- 进度显示与日志

## 目录结构

```
cli/
├── __init__.py        # 模块入口
├── __main__.py        # python -m 入口
├── main.py            # CLI 主程序 (typer)
├── README.md          # 本文档
├── commands/          # 子命令实现
│   ├── __init__.py
│   ├── transcribe.py  # 核心识别命令
│   ├── engines.py     # 引擎管理命令
│   ├── config.py      # 配置管理命令
│   └── serve.py       # API 服务命令
├── formatters/        # 输出格式化器
│   ├── __init__.py
│   ├── base.py        # 格式化器基类
│   ├── txt.py         # 纯文本格式
│   ├── srt.py         # SRT 字幕格式
│   ├── vtt.py         # WebVTT 字幕格式
│   ├── json_fmt.py    # JSON 格式
│   └── tsv.py         # TSV 表格格式
└── utils/             # CLI 工具函数
    ├── __init__.py
    └── console.py     # 终端输出 (rich)
```

## 安装依赖

```bash
pip install typer[all] rich
```

## 使用方式

### 基本用法

```bash
# 作为模块运行
python -m backend.app.cli transcribe audio.mp3

# 使用入口脚本 (推荐)
smartasr transcribe audio.mp3

# 帮助信息
smartasr --help
smartasr transcribe --help
```

### 子命令

#### transcribe - 语音识别

```bash
# 基本识别 (输出到控制台)
smartasr transcribe audio.mp3

# 输出到文件 (自动识别格式)
smartasr transcribe audio.mp3 -o result.srt

# 指定输出格式
smartasr transcribe audio.mp3 -o result.txt -f srt

# 批量处理
smartasr transcribe *.mp3 -o output_dir/

# 指定引擎和模型
smartasr transcribe audio.mp3 -e ali_funasr -m SenseVoiceSmall

# 详细输出
smartasr transcribe audio.mp3 -v
```

#### engines - 引擎管理

```bash
# 列出所有引擎
smartasr engines list

# 查看引擎详情
smartasr engines info ali_funasr

# 检查引擎状态
smartasr engines check
```

#### config - 配置管理

```bash
# 查看当前配置
smartasr config show

# 设置模型目录
smartasr config set models_dir /path/to/models

# 设置默认引擎
smartasr config set default_engine ali_funasr
```

#### serve - API 服务

```bash
# 启动 API 服务
smartasr serve

# 指定端口
smartasr serve --port 8000

# 开发模式 (自动重载)
smartasr serve --reload
```

## 输出格式

| 格式 | 扩展名 | 描述 |
|------|--------|------|
| txt | .txt | 纯文本，只有识别内容 |
| srt | .srt | SRT 字幕格式 |
| vtt | .vtt | WebVTT 字幕格式 |
| json | .json | JSON 格式，包含完整元数据 |
| tsv | .tsv | 制表符分隔，便于导入表格 |

## 设计原则

1. **渐进式体验**: 简单命令即可完成基本任务，高级选项支持复杂需求
2. **友好的错误提示**: 明确的错误信息和修复建议
3. **进度反馈**: 长时间任务有进度条显示
4. **中断安全**: Ctrl+C 可安全中断，不会损坏文件
5. **批量高效**: 批量处理时复用引擎实例

## 上下游关系

```
调用方 (上游):
  └── 用户终端

依赖 (下游):
  ├── backend.app.services.stt (核心服务)
  ├── backend.app.api (API 服务)
  ├── typer (CLI 框架)
  └── rich (终端美化)
```
