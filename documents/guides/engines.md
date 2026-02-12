# 引擎开发指南

## 概述

SmartASR 采用插件式架构，放置引擎文件即可自动注册。

## 快速开始

1. 复制模板文件：

```bash
cp backend/app/services/stt/engines/_template.py \
   backend/app/services/stt/engines/my_engine.py
```

2. 修改引擎实现（见下文）

3. 引擎自动被发现和注册

## 引擎文件结构

```python
from dataclasses import dataclass, field
from typing import List, Tuple

from ..base import BaseSTTEngine
from ..registry import register_engine
from ..dto import STTRequest, STTResponse, EngineMetadata

@register_engine  # 关键！这个装饰器注册引擎
@dataclass
class MyEngine(BaseSTTEngine):
    # 引擎标识
    name: str = field(default="my_engine", init=False)
    display_name: str = field(default="我的引擎", init=False)
    engine_type: str = field(default="local", init=False)
    
    @classmethod
    def get_metadata(cls) -> EngineMetadata:
        """返回引擎元数据"""
        ...
    
    def transcribe(self, request: STTRequest) -> STTResponse:
        """执行识别"""
        ...
    
    def get_models(self) -> List[str]:
        """返回支持的模型列表"""
        ...
    
    def check_available(self) -> Tuple[bool, str]:
        """检查引擎是否可用"""
        ...
```

## 必须实现的方法

### get_metadata()

返回引擎的元数据，用于 API 自描述：

```python
@classmethod
def get_metadata(cls) -> EngineMetadata:
    return EngineMetadata(
        name="my_engine",
        display_name="我的引擎",
        type="local",  # 或 "cloud"
        description="引擎描述",
        supported_languages=["zh", "en", "ja"],
        models=[
            ModelInfo(
                name="default",
                display_name="默认模型",
                languages=["zh", "en"],
                size="1.2GB",
                default=True,
            ),
        ],
    )
```

### transcribe()

执行实际的语音识别：

```python
def transcribe(self, request: STTRequest) -> STTResponse:
    # 1. 加载模型（如果需要）
    if self._model is None:
        self.load_model(request.model)
    
    # 2. 读取音频
    audio_path = request.audio_path
    
    # 3. 执行识别
    # ... 你的识别逻辑 ...
    
    # 4. 返回结果
    return STTResponse(
        text="识别文本",
        segments=[STTSegment(0, 1000, "识别文本")],
        duration_ms=1000,
        engine=self.name,
        model=request.model or self.get_default_model(),
    )
```

### check_available()

检查引擎是否可用：

```python
def check_available(self) -> Tuple[bool, str]:
    # 检查依赖库
    try:
        import some_library
    except ImportError:
        return False, "缺少依赖库 some_library"
    
    # 检查模型文件
    if not self._check_model_exists():
        return False, "模型文件不存在"
    
    return True, "引擎可用"
```

## 参数配置机制

SmartASR 采用自描述参数机制：引擎在 `get_metadata()` 中声明支持的参数，外部通过统一的 `options` 字典传入。

### 参数层级

| 层级 | 定义位置 | 说明 | 示例 |
|------|----------|------|------|
| **引擎级参数** | `EngineMetadata.parameters` | 所有模型共享的参数 | `use_itn`, `max_speakers` |
| **模型级参数** | `ModelInfo.parameters` | 特定模型独有的参数 | `beam_size`, `temperature` |
| **请求级参数** | `STTRequest.options` | 用户每次调用时传入 | 动态覆盖默认值 |

### ParameterSpec 字段说明

```python
from ..dto import ParameterSpec

ParameterSpec(
    name="use_itn",           # 参数名 (必填)
    type="boolean",           # 类型: string/boolean/integer/float (必填)
    required=False,           # 是否必填，默认 False
    default=True,             # 默认值
    options=[True, False],    # 可选值列表 (用于枚举类型)
    description="是否使用逆文本正则化",  # 参数描述
)
```

### 完整 get_metadata() 示例

```python
@classmethod
def get_metadata(cls) -> EngineMetadata:
    return EngineMetadata(
        name="my_engine",
        display_name="我的引擎",
        type="local",
        description="引擎描述",
        version="1.0.0",
        supported_languages=["zh", "en", "ja", "auto"],
        requires_api_key=False,  # 云端引擎设为 True
        
        # 引擎级参数 - 所有模型共享
        parameters=[
            ParameterSpec(
                name="use_itn",
                type="boolean",
                default=True,
                description="是否使用逆文本正则化 (数字转汉字等)",
            ),
            ParameterSpec(
                name="max_speakers",
                type="integer",
                default=-1,
                options=[-1, 2, 3, 4, 5],  # -1 表示禁用
                description="最大说话人数 (说话人分离)",
            ),
            ParameterSpec(
                name="output_format",
                type="string",
                default="text",
                options=["text", "json", "srt"],
                description="输出格式",
            ),
        ],
        
        # 模型列表
        models=[
            ModelInfo(
                name="model_small",
                display_name="小模型",
                description="轻量级，速度快",
                languages=["zh", "en"],
                size="~500MB",
                default=True,
                features=["timestamps", "vad"],  # 特性标签
                # 模型级参数 - 仅此模型可用
                parameters=[
                    ParameterSpec(
                        name="beam_size",
                        type="integer",
                        default=5,
                        options=[1, 3, 5, 10],
                        description="Beam search 宽度",
                    ),
                ],
            ),
            ModelInfo(
                name="model_large",
                display_name="大模型",
                description="高精度，支持说话人分离",
                languages=["zh", "en", "ja", "ko"],
                size="~2GB",
                default=False,
                features=["timestamps", "vad", "speaker_diarization"],
            ),
        ],
    )
```

### 在 transcribe() 中读取参数

```python
def transcribe(self, request: STTRequest) -> STTResponse:
    # 从 request.options 获取参数，使用默认值兜底
    use_itn = request.options.get("use_itn", True)
    max_speakers = request.options.get("max_speakers", -1)
    beam_size = request.options.get("beam_size", 5)
    
    # 使用参数执行识别
    if max_speakers > 0:
        # 启用说话人分离逻辑
        ...
```

### 外部调用方式

#### CLI 方式

```bash
# 通过 --option 传递参数
python -m backend.app.cli transcribe audio.mp3 \
    -e my_engine \
    --option use_itn=false \
    --option max_speakers=2 \
    --option beam_size=10
```

#### API 方式

```bash
# POST /api/stt/transcribe
curl -X POST http://localhost:8000/api/stt/transcribe \
    -F "file=@audio.mp3" \
    -F "engine=my_engine" \
    -F 'options={"use_itn": false, "max_speakers": 2}'
```

#### Python 库方式

```python
from backend.app.services.stt import create_engine, STTRequest
from pathlib import Path

engine = create_engine("my_engine")
result = engine.transcribe(STTRequest(
    audio_path=Path("audio.mp3"),
    options={
        "use_itn": False,
        "max_speakers": 2,
        "beam_size": 10,
    }
))
```

### API 自动暴露参数

引擎注册后，API 会自动返回参数定义：

```bash
GET /api/stt/engines/my_engine
```

响应：
```json
{
  "name": "my_engine",
  "display_name": "我的引擎",
  "parameters": [
    {
      "name": "use_itn",
      "type": "boolean",
      "default": true,
      "description": "是否使用逆文本正则化"
    },
    {
      "name": "max_speakers",
      "type": "integer",
      "default": -1,
      "options": [-1, 2, 3, 4, 5],
      "description": "最大说话人数"
    }
  ],
  "models": [
    {
      "name": "model_small",
      "languages": ["zh", "en"],
      "features": ["timestamps", "vad"],
      "parameters": [...]
    }
  ]
}
```

### 参数验证建议

```python
def transcribe(self, request: STTRequest) -> STTResponse:
    # 1. 参数验证
    max_speakers = request.options.get("max_speakers", -1)
    if max_speakers not in [-1, 2, 3, 4, 5]:
        raise TranscriptionError(
            f"无效的 max_speakers 值: {max_speakers}，允许值: [-1, 2, 3, 4, 5]"
        )
    
    # 2. 类型转换 (CLI 传入可能是字符串)
    use_itn = request.options.get("use_itn", True)
    if isinstance(use_itn, str):
        use_itn = use_itn.lower() in ("true", "1", "yes")
```

---

## 文件命名规则

- `_` 开头的文件不会被自动加载（如 `_template.py`）
- 其他 `.py` 文件会自动导入
- 建议使用描述性名称，如 `ali_funasr.py`、`whisper_local.py`

## 测试引擎

```python
from backend.app.services.stt.registry import create_engine, list_engines

# 确认引擎已注册
print(list_engines())  # 应包含 'my_engine'

# 测试可用性
engine = create_engine("my_engine")
available, reason = engine.check_available()
print(f"可用: {available}, 原因: {reason}")

# 测试识别
from backend.app.services.stt.dto import STTRequest
from pathlib import Path

request = STTRequest(audio_path=Path("test.wav"))
result = engine.transcribe(request)
print(result.text)
```
