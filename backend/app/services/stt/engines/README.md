# engines/ - 引擎插件目录

> **插件架构核心**: 放文件即注册，删文件即移除

## 职责
存放所有 STT 引擎实现，每个文件代表一个独立引擎。

## 目录结构
```
engines/
├── __init__.py       # 自动发现和加载引擎
├── _template.py      # 引擎开发模板 (不会被加载)
├── ali_funasr.py     # 阿里 FunASR 本地引擎
├── ali_qwen.py       # 阿里百炼云端引擎
└── qwen_local.py     # Qwen3-ASR 本地大模型引擎
```

## 核心机制

### 自动发现
`__init__.py` 在导入时自动扫描本目录：
- 导入所有 `.py` 文件（排除 `_` 开头的文件）
- 引擎通过 `@register_engine` 装饰器自动注册
- 依赖缺失时静默跳过，不影响其他引擎

### 命名约定
| 文件名 | 引擎名 | type | vendor | 说明 |
|--------|--------|------|--------|------|
| `ali_funasr.py` | `ali_funasr` | `local` | `Alibaba` | 阿里 FunASR 本地推理 |
| `ali_qwen.py` | `ali_qwen` | `cloud` | `Alibaba` | 阿里百炼云端 API |
| `qwen_local.py` | `qwen_local` | `local` | `Alibaba` | Qwen3-ASR 本地大模型推理 |
| `_template.py` | - | - | - | 模板，不加载 |
| `_utils.py` | - | - | - | 工具，不加载 |

## 添加新引擎步骤

### 1. 复制模板
```bash
cp _template.py my_engine.py
```

### 2. 修改类定义
```python
from dataclasses import dataclass
from ..base import BaseSTTEngine
from ..registry import register_engine

@register_engine
@dataclass
class MyEngine(BaseSTTEngine):
    name = "my_engine"           # 引擎标识（对应 API 中的 engine 参数）
    display_name = "我的引擎"     # 显示名称（出现在 GET /engines 响应中）
    engine_type = "local"        # local（本地推理）或 cloud（远程 API）
    vendor = "MyVendor"          # 厂商名（出现在 GET /engines 响应中）
```

### 3. 实现必要方法
```python
@classmethod
def get_metadata(cls) -> EngineMetadata:
    """返回引擎元数据"""
    ...

def check_available(self) -> Tuple[bool, str]:
    """检查依赖是否安装"""
    ...

def get_models(self) -> List[str]:
    """返回支持的模型列表"""
    ...

def transcribe(self, request: STTRequest) -> STTResponse:
    """执行语音识别"""
    ...
```

### 4. 验证注册
```python
from backend.app.services.stt import list_engines
engines = list_engines()
# 应该看到你的引擎
```

## 上下游关系
```
调用方 (上游):
  └── registry.py (通过装饰器自动发现)

依赖 (下游):
  ├── base.py (继承 BaseSTTEngine)
  ├── dto.py (使用 DTO 类型)
  ├── audio_utils.py (音频预处理)
  └── 各引擎特定依赖 (funasr, dashscope 等)
```

## 参数配置

引擎通过 `get_metadata()` 声明支持的参数，外部通过 `request.options` 传入。

### 参数层级
| 层级 | 位置 | 说明 |
|------|------|------|
| 引擎级 | `EngineMetadata.parameters` | 所有模型共享 |
| 模型级 | `ModelInfo.parameters` | 特定模型独有 |

### ParameterSpec 字段
```python
ParameterSpec(
    name="use_itn",           # 参数名
    type="boolean",           # string/boolean/integer/float
    required=False,           # 是否必填
    default=True,             # 默认值
    options=[True, False],    # 可选值列表
    description="描述",       # 说明文字
)
```

### 读取参数
```python
def transcribe(self, request: STTRequest) -> STTResponse:
    use_itn = request.options.get("use_itn", True)
    max_speakers = request.options.get("max_speakers", -1)
```

> 📖 详细文档见: [documents/guides/engines.md](../../../../documents/guides/engines.md)

## 隐含契约

### 性能要求
- `check_available()` 必须快速返回（<100ms），只检查依赖，不加载模型
- 模型采用延迟加载，首次 `transcribe()` 时加载
- 实现 `cleanup()` 释放 GPU 显存

### 错误处理
- 依赖缺失: 返回 `(False, "缺少依赖: pip install xxx")`
- API Key 缺失: 抛出 `APIKeyMissingError`
- 识别失败: 抛出 `TranscriptionError`

### 线程安全
- 引擎实例默认非线程安全
- 多线程使用需每线程创建独立实例

## 现有引擎状态

| 引擎 | 文件 | 状态 | 依赖 |
|------|------|------|------|
| `ali_funasr` | ali_funasr.py | ✅ 已完成 | `funasr`, `torch` |
| `ali_qwen` | ali_qwen.py | ✅ 已完成 | `dashscope` |
| `qwen_local` | qwen_local.py | ✅ 已完成 | `qwen-asr`, `soundfile`, `torch` |

### qwen_local 模型下载

```bash
# 推荐方式：git clone（需安装 git-lfs）
git clone https://huggingface.co/Qwen/Qwen3-ASR-0.6B ./models/Qwen3-ASR-0.6B
git clone https://huggingface.co/Qwen/Qwen3-ASR-7B  ./models/Qwen3-ASR-7B

# 设置模型目录（可选，默认查找 ./models/）
export STT_MODELS_DIR=./models
```

模型路径解析优先级：
1. `{STT_MODELS_DIR}/Qwen3-ASR-0.6B/`
2. `{STT_MODELS_DIR}/Qwen--Qwen3-ASR-0.6B/`
3. HuggingFace Hub 在线下载（`Qwen/Qwen3-ASR-0.6B`）
