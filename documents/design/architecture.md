# 架构设计

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     SmartASR 服务                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   HTTP API  │    │  Python库   │    │   CLI 工具   │     │
│  │   (FastAPI) │    │   (import)  │    │ (argparse)  │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   STT 服务核心                       │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────────┐   │   │
│  │  │  Registry │  │   DTO     │  │  AudioUtils   │   │   │
│  │  │  (注册表)  │  │ (数据对象) │  │  (音频处理)    │   │   │
│  │  └─────┬─────┘  └───────────┘  └───────────────┘   │   │
│  │        │                                            │   │
│  │        ▼                                            │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │              引擎插件层                       │   │   │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │   │
│  │  │  │ FunASR  │ │ Qwen-ASR│ │ Whisper │ ...   │   │   │
│  │  │  └─────────┘ └─────────┘ └─────────┘       │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 核心模块

### 1. 异常类 (exceptions.py)

统一的异常体系，便于错误处理：

```
STTException (基类)
├── FFmpegNotFoundError
├── EngineNotFoundError
├── ModelNotFoundError
├── ModelDownloadError
├── APIKeyMissingError
├── TranscriptionError
├── TaskNotFoundError
├── TaskCancelledError
├── FileTooLargeError
└── UnsupportedFormatError
```

### 2. 数据对象 (dto.py)

类型安全的数据传输对象：

- `STTRequest` - 识别请求
- `STTResponse` - 识别结果
- `STTSegment` - 识别片段
- `EngineMetadata` - 引擎元数据
- `ModelInfo` - 模型信息
- `ParameterSpec` - 参数规格

### 3. 引擎基类 (base.py)

所有引擎的抽象基类，定义契约：

- `get_metadata()` - 获取元数据
- `transcribe()` - 执行识别
- `get_models()` - 获取模型列表
- `check_available()` - 检查可用性

### 4. 注册中心 (registry.py)

插件式引擎管理：

- `@register_engine` - 注册装饰器
- `list_engines()` - 列出引擎
- `create_engine()` - 创建实例
- `discover_engines()` - 自动发现

### 5. 音频工具 (audio_utils.py)

音频预处理：

- `check_ffmpeg()` - 检查 FFmpeg
- `convert_to_16k_wav()` - 格式转换
- `get_duration()` - 获取时长

### 6. 配置管理 (config.py)

统一配置：

- 环境变量支持
- 配置文件支持
- 引擎特定配置

## 设计原则

### 1. 单一职责

每个模块只做一件事：
- `exceptions.py` 只定义异常
- `dto.py` 只定义数据结构
- `registry.py` 只管理引擎注册

### 2. 插件架构

放文件即注册，删文件即移除：
```
engines/
├── ali_funasr.py  → FunASR 可用
├── ali_qwen.py    → Qwen-ASR 可用
└── (删除即移除)
```

### 3. 零配置启动

- 无引擎时优雅降级
- 无模型时提示下载
- 无 API Key 时明确报错

### 4. 跨平台兼容

- Windows/Linux/macOS 通用
- 路径处理统一
- 环境变量跨平台
