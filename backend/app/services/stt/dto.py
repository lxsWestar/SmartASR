"""
dto.py - STT 数据传输对象 (DTO)
======================================

作用: 定义请求、响应和元数据的数据结构。
       包括 STTRequest, STTResponse, STTSegment, EngineMetadata 等。
维护: AI + Human
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import json


# 进度回调函数类型: (current, total, message) -> None
ProgressCallback = Callable[[int, int, str], None]


@dataclass
class UsageInfo:
    """
    单次请求的使用量统计
    
    用于跟踪每次识别请求的资源消耗，便于用户自行累计统计。
    本地引擎和云端引擎返回的字段可能不同。
    """
    audio_duration_ms: int = 0       # 音频时长 (毫秒)
    processing_time_ms: int = 0      # 处理耗时 (毫秒)
    api_calls: int = 0               # API 调用次数 (云端引擎，VAD 切分后可能多次)
    input_tokens: int = 0            # 输入 token (云端引擎)
    output_tokens: int = 0           # 输出 token (云端引擎)
    characters: int = 0              # 识别字符数
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)


@dataclass
class STTRequest:
    """识别请求"""
    audio_path: Path              # 音频文件路径
    language: str = "auto"        # 语言: zh/en/ja/auto
    engine: str = "ali_funasr"    # 引擎名称
    model: Optional[str] = None   # 模型名称
    params: Dict[str, Any] = field(default_factory=dict)          # 标准层：SmartASR 统一参数名
    engine_options: Dict[str, Any] = field(default_factory=dict)  # 直通层：原样透传给底层 SDK
    callback_url: Optional[str] = None  # Webhook 回调 URL
    progress_callback: Optional[ProgressCallback] = field(default=None, repr=False)  # 进度回调
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "audio_path": str(self.audio_path),
            "language": self.language,
            "engine": self.engine,
            "model": self.model,
            "params": self.params,
            "engine_options": self.engine_options,
            "callback_url": self.callback_url,
        }
    
    def report_progress(self, current: int, total: int, message: str = "") -> None:
        """报告进度 (如果设置了回调)"""
        if self.progress_callback:
            try:
                self.progress_callback(current, total, message)
            except Exception:
                pass  # 忽略回调异常


@dataclass
class STTSegment:
    """识别片段"""
    start_ms: int     # 开始时间 (毫秒)
    end_ms: int       # 结束时间 (毫秒)
    text: str         # 识别文本
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @property
    def duration_ms(self) -> int:
        """片段时长 (毫秒)"""
        return self.end_ms - self.start_ms


@dataclass
class STTResponse:
    """识别结果"""
    text: str                     # 完整文本
    segments: List[STTSegment]    # 分段结果
    duration_ms: int              # 音频时长
    engine: str                   # 使用的引擎
    model: str                    # 使用的模型
    language_detected: Optional[str] = None  # 检测到的语言
    usage: Optional[UsageInfo] = None        # 使用量统计
    
    def to_dict(self) -> dict:
        """转换为字典"""
        result = {
            "text": self.text,
            "segments": [seg.to_dict() for seg in self.segments],
            "duration_ms": self.duration_ms,
            "engine": self.engine,
            "model": self.model,
            "language_detected": self.language_detected,
        }
        if self.usage is not None:
            result["usage"] = self.usage.to_dict()
        return result
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class ParameterSpec:
    """参数规格 - 用于 API 自描述"""
    name: str                     # 参数名
    type: str                     # 类型: string/boolean/integer/float
    required: bool = False        # 是否必填
    default: Any = None           # 默认值
    options: Optional[List[Any]] = None  # 可选值列表
    description: str = ""         # 参数描述
    layer: str = "engine"         # 参数层: "standard"（标准层）或 "engine"（直通层）
    
    def to_dict(self) -> dict:
        """转换为字典"""
        result = {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
            "layer": self.layer,
        }
        if self.default is not None:
            result["default"] = self.default
        if self.options:
            result["options"] = self.options
        return result


@dataclass
class ModelInfo:
    """模型信息"""
    name: str                     # 模型标识
    display_name: str             # 显示名称
    description: str              # 模型描述
    languages: List[str]          # 支持的语言
    size: str                     # 模型大小 (如 "1.2GB")
    default: bool = False         # 是否为默认模型
    parameters: List[ParameterSpec] = field(default_factory=list)  # 模型特定参数
    features: List[str] = field(default_factory=list)  # 特性标签
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "languages": self.languages,
            "size": self.size,
            "default": self.default,
            "parameters": [p.to_dict() for p in self.parameters],
            "features": self.features,
        }


@dataclass
class EngineMetadata:
    """引擎元数据 - 自描述"""
    name: str                     # 引擎标识
    display_name: str             # 显示名称（纯名称，不含厂商/部署方式）
    type: str                     # "local" 或 "cloud"
    description: str              # 引擎描述
    vendor: str = ""              # 厂商，如 "Alibaba"、"OpenAI"（可选，默认空串）
    version: str = "1.0.0"        # 版本号
    supported_languages: List[str] = field(default_factory=list)
    models: List[ModelInfo] = field(default_factory=list)
    requires_api_key: bool = False  # 是否需要 API Key
    parameters: List[ParameterSpec] = field(default_factory=list)  # 引擎级参数
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "type": self.type,
            "vendor": self.vendor,
            "description": self.description,
            "version": self.version,
            "supported_languages": self.supported_languages,
            "models": [m.to_dict() for m in self.models],
            "requires_api_key": self.requires_api_key,
            "parameters": [p.to_dict() for p in self.parameters],
        }
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# ============================================================================
# 标准层参数注册表
# ============================================================================

STANDARD_PARAMS: Dict[str, ParameterSpec] = {
    "itn": ParameterSpec(
        name="itn", type="boolean", required=False, default=True,
        layer="standard",
        description="逆文本正则化：将口语数字/标点还原为书面形式（并非所有引擎都支持）",
    ),
    "timestamps": ParameterSpec(
        name="timestamps", type="boolean", required=False, default=False,
        layer="standard",
        description="返回词级或句级时间戳（并非所有引擎都支持）",
    ),
    "context": ParameterSpec(
        name="context", type="string", required=False, default="",
        layer="standard",
        description="识别上下文提示词，帮助模型识别专有名词（并非所有引擎都支持）",
    ),
    "speaker_diarization": ParameterSpec(
        name="speaker_diarization", type="boolean", required=False, default=False,
        layer="standard",
        description="启用说话人分离，识别多人对话（并非所有引擎都支持）",
    ),
    "max_speakers": ParameterSpec(
        name="max_speakers", type="integer", required=False, default=2,
        layer="standard",
        description="最大说话人数，仅在 speaker_diarization=true 时有效",
    ),
}
