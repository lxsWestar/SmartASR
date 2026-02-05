"""
exceptions.py - STT 异常类定义
====================================

作用: 定义 STT 模块的所有异常类，提供统一的错误处理机制。
设计参考: pyvideotrans 的异常分类思路（独立实现，无代码复制）
维护: AI + Human
"""

from typing import Optional


class STTException(Exception):
    """STT 基础异常类"""
    
    error_code: str = "STT_ERROR"
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        if error_code:
            self.error_code = error_code
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"
    
    def to_dict(self) -> dict:
        """转换为字典，便于 API 响应"""
        return {
            "error_code": self.error_code,
            "message": self.message,
        }


class FFmpegNotFoundError(STTException):
    """FFmpeg 未安装或不可用"""
    error_code = "FFMPEG_NOT_FOUND"
    
    def __init__(self, message: str = "FFmpeg 未安装或不在 PATH 中"):
        super().__init__(message)


class EngineNotFoundError(STTException):
    """引擎不存在"""
    error_code = "ENGINE_NOT_FOUND"
    
    def __init__(self, engine_name: str):
        super().__init__(f"引擎 '{engine_name}' 不存在或未注册")
        self.engine_name = engine_name


class ModelNotFoundError(STTException):
    """模型不存在"""
    error_code = "MODEL_NOT_FOUND"
    
    def __init__(self, model_name: str, engine_name: Optional[str] = None):
        msg = f"模型 '{model_name}' 不存在"
        if engine_name:
            msg += f" (引擎: {engine_name})"
        super().__init__(msg)
        self.model_name = model_name
        self.engine_name = engine_name


class ModelDownloadError(STTException):
    """模型下载失败"""
    error_code = "MODEL_DOWNLOAD_ERROR"
    
    def __init__(self, model_name: str, reason: str = ""):
        msg = f"模型 '{model_name}' 下载失败"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
        self.model_name = model_name
        self.reason = reason


class ModelNotLoadedError(STTException):
    """模型未加载"""
    error_code = "MODEL_NOT_LOADED"
    
    def __init__(self, model_name: str):
        super().__init__(f"模型 '{model_name}' 未加载，请先调用 load_model()")
        self.model_name = model_name


class APIKeyMissingError(STTException):
    """API Key 缺失"""
    error_code = "API_KEY_MISSING"
    
    def __init__(self, engine_name: str, key_name: str = "API_KEY"):
        super().__init__(f"引擎 '{engine_name}' 需要配置 {key_name}")
        self.engine_name = engine_name
        self.key_name = key_name


class TranscriptionError(STTException):
    """识别失败"""
    error_code = "TRANSCRIPTION_ERROR"
    
    def __init__(self, message: str, engine_name: Optional[str] = None):
        if engine_name:
            message = f"[{engine_name}] {message}"
        super().__init__(message)
        self.engine_name = engine_name


class TaskNotFoundError(STTException):
    """任务不存在"""
    error_code = "TASK_NOT_FOUND"
    
    def __init__(self, task_id: str):
        super().__init__(f"任务 '{task_id}' 不存在")
        self.task_id = task_id


class TaskCancelledError(STTException):
    """任务已取消"""
    error_code = "TASK_CANCELLED"
    
    def __init__(self, task_id: str):
        super().__init__(f"任务 '{task_id}' 已被取消")
        self.task_id = task_id


class FileTooLargeError(STTException):
    """文件过大"""
    error_code = "FILE_TOO_LARGE"
    
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            f"文件大小 {file_size / 1024 / 1024:.1f}MB 超过限制 {max_size / 1024 / 1024:.1f}MB"
        )
        self.file_size = file_size
        self.max_size = max_size


class UnsupportedFormatError(STTException):
    """不支持的格式"""
    error_code = "UNSUPPORTED_FORMAT"
    
    def __init__(self, format_name: str, supported_formats: list = None):
        msg = f"不支持的音频格式: {format_name}"
        if supported_formats:
            msg += f"，支持的格式: {', '.join(supported_formats)}"
        super().__init__(msg)
        self.format_name = format_name
        self.supported_formats = supported_formats or []
