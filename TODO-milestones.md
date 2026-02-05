# SmartASR: 里程碑详细任务清单

> 📋 本文件包含 M1-M11 各里程碑的详细实现任务。

---

## M1 项目骨架 ✅ 已完成
> **目标**: 创建目录结构和基础设施
> **完成日期**: 2026-01-23

### 1.1 目录结构
- [x] 创建 STT 服务目录结构
- [x] `__init__.py` - 统一导出
- [x] `exceptions.py` - 异常类定义
- [x] `dto.py` - 数据传输对象
- [x] `base.py` - 引擎基类
- [x] `audio_utils.py` - 音频预处理
- [x] `vad_utils.py` - VAD 语音活动检测
- [x] `registry.py` - 引擎注册中心
- [x] `config.py` - 配置管理
- [x] `engines/` - 引擎插件目录

### 1.2 跨平台兼容层 (`compat.py`)
- [x] `IS_WINDOWS`, `IS_LINUX`, `IS_MACOS` 常量
- [x] `to_ffmpeg_path()` - FFmpeg 路径转换
- [x] `get_temp_dir()` - 获取临时目录
- [x] `get_cache_dir()` - 获取缓存目录
- [x] `get_models_dir()` - 获取模型目录
- [x] `setup_environment()` - 环境变量设置
- [x] `get_python_executable()` - Python 解释器路径
- [x] `normalize_path()` - 路径标准化

### 1.3 异常类 (`exceptions.py`)
- [x] `STTException` - 基类
- [x] `FFmpegNotFoundError`
- [x] `EngineNotFoundError`
- [x] `ModelNotFoundError`
- [x] `ModelDownloadError`
- [x] `ModelNotLoadedError`
- [x] `APIKeyMissingError`
- [x] `TranscriptionError`
- [x] `TaskNotFoundError`
- [x] `TaskCancelledError`
- [x] `FileTooLargeError`
- [x] `UnsupportedFormatError`

### 1.4 验证
- [x] Windows: `python -c "from backend.app.services.stt import exceptions"`
- [ ] Linux: `python3 -c "from backend.app.services.stt import exceptions"`
- [ ] 嵌入测试: 复制 stt/ 到空项目，import 无报错

---

## M2 音频预处理 ✅ 已完成
> **目标**: 将任意音频转为 16kHz mono WAV
> **状态**: ✅ 已完成

### 2.1 FFmpeg 检测 (`audio_utils.py`)
- [x] `check_ffmpeg() -> bool`
- [x] `get_ffmpeg_version() -> str`

### 2.2 音频转换
- [x] `convert_to_16k_wav(input_path, output_path)`
- [x] Windows 路径用 `.as_posix()` 处理
- [x] 失败抛出 `FFmpegNotFoundError`

### 2.3 媒体信息
- [x] `get_duration(path) -> float`
- [x] `get_audio_info(path) -> dict`

### 2.4 VAD 语音活动检测 (`vad_utils.py`)
- [x] `detect_speech_segments()` - 检测语音片段
  - [x] silero-vad 支持
  - [x] funasr fsmn-vad 支持
  - [x] pydub detect_nonsilent 支持
  - [x] 自动选择最佳方法
- [x] `cut_audio_by_vad()` - 按 VAD 切分音频
- [x] `get_available_vad_methods()` - 获取可用方法

### 2.5 验证
- [x] 转换 MP3 → WAV 成功
- [x] 中文路径正常处理
- [x] silero-vad 检测正常
- [x] 长音频切分正常
- [x] 无 VAD 依赖时优雅降级

---

## M3 DTO + 引擎接口 ✅ 已完成
> **目标**: 定义数据结构、引擎契约和自描述元数据

### 3.1 数据对象 (`dto.py`)
- [x] `STTRequest` - 识别请求
- [x] `STTSegment` - 识别片段
- [x] `STTResponse` - 识别结果
- [x] `ParameterSpec` - 参数规格
- [x] `ModelInfo` - 模型信息
- [x] `EngineMetadata` - 引擎元数据
- [x] `UsageInfo` - 使用量统计

### 3.2 引擎基类 (`base.py`)
- [x] `BaseSTTEngine` 抽象基类
- [x] `get_metadata()` 类方法
- [x] `transcribe()` 抽象方法
- [x] `get_models()` 抽象方法
- [x] `check_available()` 抽象方法
- [x] `get_default_model()` 方法
- [x] `cleanup()` 资源释放

### 3.3 验证
- [x] DTO 可正常实例化和序列化为 JSON
- [x] `EngineMetadata.to_dict()` 输出符合 API 响应格式
- [x] Windows/Linux 路径处理正确

---

## M4 引擎注册中心 ✅ 已完成
> **目标**: 实现真正的插件式引擎管理 - 放文件即用

### 4.1 核心理念
```
放文件 = 注册引擎
删文件 = 移除引擎
无需修改任何其他代码
```

### 4.2 注册中心 (`registry.py`)
- [x] `_engine_registry` - 引擎注册表
- [ ] `_engine_instances` - 引擎实例缓存 (待实现)
- [x] `@register_engine` - 注册装饰器
- [x] `create_engine(name)` - 创建实例
- [x] `get_engine_class(name)` - 获取引擎类
- [x] `list_engines()` - 列出引擎名称
- [x] `list_engines_metadata()` - 列出元数据
- [x] `discover_engines()` - 自动发现
- [x] `unregister_engine(name)` - 取消注册
- [ ] `reload_engines()` - 热重载 (待实现)

### 4.3 自动发现机制 (`engines/__init__.py`)
- [x] 自动扫描 engines/ 目录
- [x] 跳过下划线开头的文件
- [x] 依赖缺失时静默跳过

### 4.4 引擎模板 (`engines/_template.py`)
- [x] 完整开发模板

### 4.5 优雅降级
- [x] engines/ 目录为空不报错
- [x] 单个引擎失败不影响其他
- [x] API 返回清晰提示

### 4.6 验证
- [x] 放入 `ali_funasr.py` → `list_engines()` 显示
- [x] 删除后不再显示
- [x] 依赖缺失时其他引擎正常
- [ ] `reload_engines()` 热加载 (待实现)

---

## M5 FunASR 引擎 ✅ 已完成
> **目标**: 实现本地 FunASR 引擎
> **依赖**: M2, M4

### 5.1 引擎类 (`engines/ali_funasr.py`)
- [x] `FunASREngine` 类定义
- [x] `@register_engine` 装饰器

### 5.2 初始化
- [x] 检查 `funasr` 库
- [x] CUDA 检测和回退
- [x] 延迟加载模型

### 5.3 模型管理
- [x] `SenseVoiceSmall` - 多语言
- [x] `paraformer-zh` - 中文高精度
- [x] 自动下载 (HF 镜像)

### 5.4 识别实现
- [x] `transcribe()` 完整实现

### 5.5 资源清理
- [x] `cleanup()` 释放显存

### 5.6 验证
- [x] 10秒中文音频识别成功
- [x] GPU 模式正常
- [x] CPU 回退正常

---

## M6 Qwen-ASR 引擎 ✅ 已完成
> **目标**: 实现云端 Qwen-ASR 引擎
> **依赖**: M4

### 6.1 引擎类 (`engines/ali_qwen.py`)
- [x] `QwenASREngine` 类定义
- [x] `@register_engine` 装饰器

### 6.2 初始化
- [x] 检查 `dashscope` 库
- [x] API Key 获取
- [x] 无 Key 时抛出异常

### 6.3 识别实现
- [x] 音频转换 16kHz WAV
- [x] VAD 切分
- [x] 逐段调用 API
- [x] 汇总结果

### 6.4 错误处理
- [x] API Key 无效
- [x] 配额耗尽
- [ ] 网络超时重试 (待优化)

### 6.5 验证
- [x] 真实 API Key 测试 (284秒 → 37段)
- [x] 错误异常正确抛出

---

## M7 API 路由 ✅ 已完成
> **目标**: 暴露完整的 RESTful API
> **依赖**: M5, M6

详见 [TODO-api.md](TODO-api.md)

---

## M8 测试 + 文档 ✅ 单元测试完成
> **目标**: 完善测试和文档
> **单元测试完成日期**: 2026-02-03

### 8.1 单元测试 ✅ 已完成
> **测试统计**: 135 tests passed, 0 warnings

| 测试模块 | 测试数 | 覆盖内容 | 状态 |
|---------|-------|---------|------|
| `test_dto.py` | 41 | DTO 类创建、字段验证、边界条件、序列化 | ✅ |
| `test_exceptions.py` | 31 | 异常类继承、消息格式、错误链、HTTP 状态码 | ✅ |
| `test_registry.py` | 24 | 引擎注册/注销、装饰器、实例创建、热插拔 | ✅ |
| `test_audio_utils.py` | 23 | FFmpeg 检测、格式转换、时长获取、边界情况 | ✅ |
| `test_api_endpoints.py` | 4 | API 端点集成测试 | ✅ |
| `test_funasr_engine.py` | 8 | FunASR 引擎集成测试 | ✅ |
| `test_full_pipeline.py` | 4 | 端到端完整流程测试 | ✅ |

**测试质量改进**:
- 精确断言: 去除 `try/except: pass` 的"硬接"模式
- Mock 隔离: 所有外部调用都用 mock 隔离
- 覆盖全面: 包含正常路径、边界条件、错误处理

### 8.2 集成测试
- [ ] `test_funasr/` - FunASR 引擎
- [ ] `test_api/` - API 端点

### 8.3 文档
- [ ] 更新 `README.md`
- [ ] `docs/api/stt.md` - API 文档
- [ ] `docs/guides/add_engine.md` - 添加引擎指南

### 8.4 验证
- [x] `pytest tests/unit/` 全部通过
- [ ] `pytest tests/integration/` 全部通过
- [ ] 文档示例可运行

---

## M9 依赖检查 + 友好提示 🔲 待开发
> **目标**: 引擎运行前检查依赖，缺失时给出清晰安装指引
> **优先级**: 高 (用户体验改进)

### 9.1 需求场景
```
当前问题:
- 引擎文件存在 → 自动注册
- 但依赖库没装 → 调用时才报晦涩的 ImportError
- 用户不知道该装什么、怎么装

改进后:
- 引擎注册时标记依赖
- check_available() 检查依赖并返回友好提示
- API 错误响应包含安装命令
```

### 9.2 实现方案
- [ ] 在 EngineMetadata 中添加 `dependencies` 字段
  ```python
  @dataclass
  class DependencyInfo:
      package: str           # pip 包名
      import_name: str       # Python 导入名
      version: str = ""      # 版本要求
      install_cmd: str = ""  # 安装命令
  ```
- [ ] 完善 `check_available()` 检查依赖库
- [ ] 返回清晰错误信息: "缺少依赖: pip install funasr"
- [ ] API 错误响应包含 `install_hint` 字段

### 9.3 示例效果
```json
{
  "name": "ali_funasr",
  "available": false,
  "available_reason": "缺少依赖库",
  "install_hint": "pip install funasr torch",
  "dependencies": [
    {"package": "funasr", "installed": false},
    {"package": "torch", "installed": true}
  ]
}
```

---

## M10 模型源配置 + 内网分发 ✅ 已完成
> **目标**: 支持内网模型分发

- [x] 模型目录配置 (`STT_MODELS_DIR`)
- [x] HF 镜像自动切换
- [x] 本地模型加载支持

---

## M11 命令行工具 (CLI) ✅ 已完成
> **目标**: 产品级命令行工具
> **完成日期**: 2026-02-04

### 11.1 CLI 架构
- [x] Typer + Rich 框架
- [x] 模块化设计 (`backend/app/cli/`)
- [x] commands/ - 子命令
- [x] formatters/ - 输出格式器
- [x] utils/ - 工具函数

### 11.2 子命令
- [x] `transcribe` - 语音识别
- [x] `engines` - 引擎管理
- [x] `config` - 配置管理
- [x] `serve` - 启动 API 服务

### 11.3 输出格式
- [x] txt - 纯文本
- [x] srt - SubRip 字幕
- [x] vtt - WebVTT 字幕
- [x] json - JSON 格式
- [x] tsv - 制表符分隔

### 11.4 功能特性
- [x] 批量处理
- [x] 进度条显示
- [x] UTF-8 编码
- [x] pyproject.toml 入口点

### 11.5 使用方式
```bash
# 单文件转写
python -m backend.app.cli transcribe audio.mp3 -o result.srt

# 批量处理
python -m backend.app.cli transcribe *.mp3 -o output/

# 查看引擎
python -m backend.app.cli engines list

# 启动服务
python -m backend.app.cli serve --port 8000
```
