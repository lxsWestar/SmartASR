# stt/ - 语音转文字核心服务

> **可独立嵌入**: 本目录可直接复制到任意 Python 项目中使用

## 职责
提供语音转文字 (Speech-to-Text) 的核心功能，支持多引擎插件架构。

## 目录结构
```
stt/
├── __init__.py        # 统一导出接口
├── exceptions.py      # 异常类定义 (12 个异常类)
├── dto.py             # 数据传输对象 (Request/Response/Metadata)
├── base.py            # 引擎基类 BaseSTTEngine
├── audio_utils.py     # FFmpeg 音频处理工具
├── vad_utils.py       # VAD 语音活动检测工具 (可选) 🆕
├── compat.py          # 跨平台兼容层
├── config.py          # 配置管理
├── registry.py        # 引擎注册中心
├── engines/           # 引擎插件目录
│   ├── __init__.py    # 自动发现引擎
│   └── _template.py   # 引擎开发模板
└── agents/            # AI 协作指令
    └── prompts.md     # 模块特定提示词
```

## 核心模块说明

### exceptions.py - 异常类
| 异常类 | 错误码 | 触发场景 |
|--------|--------|----------|
| `STTException` | - | 基类 |
| `FFmpegNotFoundError` | FFMPEG_NOT_FOUND | FFmpeg 未安装 |
| `EngineNotFoundError` | ENGINE_NOT_FOUND | 引擎不存在 |
| `ModelNotFoundError` | MODEL_NOT_FOUND | 模型不存在 |
| `APIKeyMissingError` | API_KEY_MISSING | 云端引擎缺少密钥 |
| `TranscriptionError` | TRANSCRIPTION_FAILED | 识别失败 |

### dto.py - 数据对象
```python
# 请求/响应
STTRequest   # 识别请求: audio_path, language, engine, model, options
STTResponse  # 识别结果: text, segments, duration_ms, usage
STTSegment   # 时间片段: start_ms, end_ms, text
UsageInfo    # 使用量统计: audio_duration_ms, processing_time_ms, characters

# 元数据 (用于 API 自描述)
EngineMetadata  # 引擎元数据: name, type, models, parameters
ModelInfo       # 模型信息: name, languages, size, features, parameters
ParameterSpec   # 参数规格: name, type, default, options, description
```

### ParameterSpec 字段
用于声明引擎/模型支持的参数，实现 API 自描述：
```python
ParameterSpec(
    name="max_speakers",     # 参数名
    type="integer",          # 类型: string/boolean/integer/float
    required=False,          # 是否必填
    default=-1,              # 默认值
    options=[-1, 2, 3, 4, 5],  # 可选值列表
    description="说话人数",  # 描述
)
```

### base.py - 引擎基类
```python
class BaseSTTEngine(ABC):
    @abstractmethod
    def transcribe(request: STTRequest) -> STTResponse
    @abstractmethod
    def check_available() -> Tuple[bool, str]
    @abstractmethod
    def get_models() -> List[str]
    @classmethod
    def get_metadata() -> EngineMetadata
```

### registry.py - 引擎注册中心
```python
@register_engine       # 装饰器，自动注册引擎
list_engines()         # 列出所有引擎名称 -> List[str]
create_engine(name)    # 创建引擎实例
get_engine_class(name) # 获取引擎类
get_engine_metadata(name)    # 获取单个引擎元数据
list_engines_metadata()      # 列出所有引擎元数据 -> List[EngineMetadata]
discover_engines()     # 自动发现并加载引擎
unregister_engine(name)      # 取消注册引擎
```

### compat.py - 跨平台兼容
```python
IS_WINDOWS, IS_LINUX, IS_MACOS  # 平台检测
to_ffmpeg_path(path)   # 转换路径为 FFmpeg 格式
get_temp_dir()         # 获取临时目录
get_cache_dir()        # 获取应用缓存目录
get_models_dir()       # 获取模型存储目录
setup_environment()    # 设置运行环境变量
get_python_executable()  # 获取 Python 解释器路径
normalize_path()       # 标准化路径
```

### audio_utils.py - 音频处理
```python
check_ffmpeg()         # 检查 FFmpeg 可用性
get_ffmpeg_version()   # 获取版本号
convert_to_16k_wav()   # 转换为 16kHz mono WAV
get_duration()         # 获取音频时长
```

### vad_utils.py - VAD 语音活动检测 (可选) 🆕
> 为不返回时间戳的云端 API 提供本地语音片段检测

```python
# 检测语音片段
detect_speech_segments(audio_path, method="auto") -> List[VADSegment]

# 切分音频文件
cut_audio_by_vad(audio_path, output_dir) -> List[Tuple[Path, int, int]]

# 获取可用 VAD 方法
get_available_vad_methods() -> List[str]  # ["silero", "funasr", "pydub"]

# 按时长切分 (无需 VAD)
cut_audio_by_duration(audio_path, chunk_duration_ms=30000)
```

**支持的 VAD 后端:**
| 方法 | 依赖 | 精度 | 速度 | 适用场景 |
|------|------|------|------|----------|
| silero | `faster-whisper` | 高 | 快 | 通用推荐 |
| funasr | `funasr` | 高 | 中 | 已装 FunASR 时 |
| pydub | `pydub` | 中 | 快 | 轻量级场景 |

## 上下游关系
```
调用方 (上游):
  ├── API 路由层 (FastAPI)
  ├── CLI 命令行工具
  └── 外部项目 (嵌入使用)

依赖 (下游):
  ├── FFmpeg (音频处理)
  ├── funasr (本地引擎，可选)
  ├── dashscope (云端引擎，可选)
  └── torch (GPU 加速，可选)
```

## 隐含契约

### 性能约束
- `check_ffmpeg()` 必须在 100ms 内返回
- 引擎 `check_available()` 不应加载模型，只检查依赖
- 模型采用**延迟加载**，首次 `transcribe()` 时才加载

### 线程安全
- `_engine_registry` 是模块级全局变量，读操作线程安全
- 引擎实例 (`_engine_instances`) 在单线程环境使用
- 多线程场景需外部加锁或每线程创建实例

### 路径处理
- 所有路径必须使用 `pathlib.Path`
- 传递给 FFmpeg 的 Windows 路径用 `.as_posix()` 转换
- 支持中文路径

### 资源管理
- 引擎必须实现 `cleanup()` 方法释放资源
- GPU 内存释放: `gc.collect()` + `torch.cuda.empty_cache()`

## 使用示例

### 作为库嵌入
```python
from stt import list_engines, transcribe

# 查看可用引擎
engines = list_engines()

# 识别音频
result = transcribe("audio.mp3", engine="ali_funasr")
print(result.text)
```

### 直接导入
```python
from stt.registry import get_engine
from stt.dto import STTRequest

engine = get_engine("ali_funasr")
request = STTRequest(audio_path=Path("test.mp3"))
response = engine.transcribe(request)
```

## 扩展指南
- 添加新引擎: 参考 [engines/README.md](engines/README.md)
- 修改配置: 参考 `config.py` 的环境变量说明

## 模型配置

本模块支持多种模型加载方式，适应不同部署场景。

### 环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `STT_MODELS_DIR` | 本地模型目录 | `D:\models\funasr` |
| `STT_MODEL_SERVER` | 内网模型服务地址 | `http://192.168.1.100:8765` |
| `FUNASR_HUB` | 官方源选择 (hf/ms) | `hf` |

### 模型加载优先级

1. **本地目录** (`STT_MODELS_DIR`) - 最快，离线可用
2. **内网服务** (`STT_MODEL_SERVER`) - 公司部署推荐
3. **官方源** (ModelScope/HuggingFace) - 兜底

### 场景配置

#### 开发测试 (本地模型)
```powershell
# 设置本地模型目录
$env:STT_MODELS_DIR = "D:\models\funasr"

# 目录结构
D:\models\funasr\
├── SenseVoiceSmall\    # 多语言识别
├── paraformer-zh\      # 中文识别
├── fsmn-vad\           # VAD 模型
└── ct-punc\            # 标点模型
```

#### 企业部署 (内网服务)
```powershell
# 1. 在有模型的机器上启动服务
python scripts/model_server.py --models-dir D:\models\funasr --port 8765

# 2. 客户端配置
$env:STT_MODEL_SERVER = "http://192.168.1.100:8765"
```

#### 云端/官方源
```powershell
# 不设置任何环境变量，自动从官方源下载
# 海外用户推荐 HuggingFace
$env:FUNASR_HUB = "hf"

# 国内用户推荐 ModelScope
$env:FUNASR_HUB = "ms"
```

### 模型服务器

项目提供了简单的模型文件服务器，用于内网分发：

```bash
# 启动服务
python scripts/model_server.py -d D:\models\funasr -p 8765

# API 端点
GET /              # 列出所有模型
GET /models/{name} # 下载模型 (zip)
GET /health        # 健康检查
```
