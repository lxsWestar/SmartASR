"""
SmartASR STT Service
====================

轻量级语音转文字服务，可作为独立模块嵌入任意 Python 项目。

使用方式:
    from backend.app.services.stt import transcribe, list_engines
    
    # 列出可用引擎
    engines = list_engines()
    
    # 执行语音识别
    result = transcribe("audio.mp3", engine="ali_funasr")
"""

from .exceptions import (
    STTException,
    FFmpegNotFoundError,
    EngineNotFoundError,
    ModelNotFoundError,
    ModelDownloadError,
    ModelNotLoadedError,
    APIKeyMissingError,
    TranscriptionError,
    TaskNotFoundError,
    TaskCancelledError,
    FileTooLargeError,
    UnsupportedFormatError,
)

from .dto import (
    STTRequest,
    STTResponse,
    STTSegment,
    EngineMetadata,
    ModelInfo,
    ParameterSpec,
    ProgressCallback,
)

from .registry import (
    list_engines,
    create_engine,
    get_engine_class,
    get_engine_metadata,
)

from .base import BaseSTTEngine

from .audio_utils import (
    check_ffmpeg,
    convert_to_16k_wav,
    get_duration,
)

from .config import (
    STTConfig,
    ModelSourceConfig,
    get_config,
    set_config,
)

# VAD 工具 (可选，延迟导入以避免强制依赖)
# 使用时: from backend.app.services.stt.vad_utils import detect_speech_segments

# 确保引擎被自动发现
from . import engines

__version__ = "0.1.0"
__all__ = [
    # 异常类
    "STTException",
    "FFmpegNotFoundError",
    "EngineNotFoundError",
    "ModelNotFoundError",
    "ModelDownloadError",
    "ModelNotLoadedError",
    "APIKeyMissingError",
    "TranscriptionError",
    "TaskNotFoundError",
    "TaskCancelledError",
    "FileTooLargeError",
    "UnsupportedFormatError",
    # DTO
    "STTRequest",
    "STTResponse",
    "STTSegment",
    "EngineMetadata",
    "ModelInfo",
    "ParameterSpec",
    # 配置
    "STTConfig",
    "ModelSourceConfig",
    "get_config",
    "set_config",
    # 注册表 API
    "list_engines",
    "create_engine",
    "get_engine_class",
    "get_engine_metadata",
    # 基类
    "BaseSTTEngine",
    # 音频工具
    "check_ffmpeg",
    "convert_to_16k_wav",
    "get_duration",
    # VAD 工具 (需要单独导入: from backend.app.services.stt.vad_utils import ...)
    # "detect_speech_segments",
    # "cut_audio_by_vad",
    # "get_available_vad_methods",
]
