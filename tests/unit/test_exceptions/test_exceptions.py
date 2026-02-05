"""
异常类单元测试 (V2 - 重构版)
==============================

测试原则:
1. 覆盖所有已定义的异常类
2. 测试异常消息格式化
3. 测试 to_dict 和 __str__ 的一致性
4. 测试实际使用场景
"""

import pytest
from backend.app.services.stt.exceptions import (
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


# ============================================================================
# 基础异常类测试
# ============================================================================
class TestSTTException:
    """测试基础异常类"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        exc = STTException("发生了错误")
        assert exc.message == "发生了错误"
        assert exc.error_code == "STT_ERROR"
    
    def test_custom_error_code(self):
        """测试自定义错误码"""
        exc = STTException("错误", error_code="CUSTOM_CODE")
        assert exc.error_code == "CUSTOM_CODE"
    
    def test_str_format(self):
        """测试字符串格式"""
        exc = STTException("测试消息", error_code="TEST")
        assert str(exc) == "[TEST] 测试消息"
    
    def test_to_dict(self):
        """测试字典转换"""
        exc = STTException("消息", error_code="CODE")
        d = exc.to_dict()
        assert d == {"error_code": "CODE", "message": "消息"}
    
    def test_can_be_raised(self):
        """测试可以正常抛出"""
        with pytest.raises(STTException) as exc_info:
            raise STTException("测试抛出")
        assert "测试抛出" in str(exc_info.value)
    
    def test_inheritance(self):
        """测试是 Exception 的子类"""
        exc = STTException("test")
        assert isinstance(exc, Exception)


# ============================================================================
# FFmpeg 相关异常测试
# ============================================================================
class TestFFmpegNotFoundError:
    """测试 FFmpeg 未找到异常"""
    
    def test_default_message(self):
        """测试默认消息"""
        exc = FFmpegNotFoundError()
        assert "FFmpeg" in exc.message or "ffmpeg" in exc.message.lower()
        assert exc.error_code == "FFMPEG_NOT_FOUND"
    
    def test_custom_message(self):
        """测试自定义消息"""
        exc = FFmpegNotFoundError("请安装 FFmpeg 到 PATH")
        assert "请安装" in exc.message
    
    def test_error_code_preserved(self):
        """测试错误码不被覆盖"""
        exc = FFmpegNotFoundError("custom")
        assert exc.error_code == "FFMPEG_NOT_FOUND"


# ============================================================================
# 引擎相关异常测试
# ============================================================================
class TestEngineNotFoundError:
    """测试引擎未找到异常"""
    
    def test_with_engine_name(self):
        """测试引擎名称包含在消息中"""
        exc = EngineNotFoundError("whisper")
        assert exc.engine_name == "whisper"
        assert "whisper" in exc.message
        assert exc.error_code == "ENGINE_NOT_FOUND"
    
    def test_chinese_engine_name(self):
        """测试中文引擎名称"""
        exc = EngineNotFoundError("测试引擎")
        assert exc.engine_name == "测试引擎"


class TestAPIKeyMissingError:
    """测试 API Key 缺失异常"""
    
    def test_with_engine_and_env(self):
        """测试带引擎名和环境变量"""
        exc = APIKeyMissingError("ali_qwen", "DASHSCOPE_API_KEY")
        assert exc.engine_name == "ali_qwen"
        assert exc.key_name == "DASHSCOPE_API_KEY"  # 实际属性名是 key_name
        assert exc.error_code == "API_KEY_MISSING"
        # 消息应该包含指导信息
        assert "ali_qwen" in exc.message or "DASHSCOPE_API_KEY" in exc.message


# ============================================================================
# 模型相关异常测试
# ============================================================================
class TestModelNotFoundError:
    """测试模型未找到异常"""
    
    def test_model_only(self):
        """测试只有模型名称"""
        exc = ModelNotFoundError("SenseVoiceSmall")
        assert exc.model_name == "SenseVoiceSmall"
        assert "SenseVoiceSmall" in exc.message
        assert exc.error_code == "MODEL_NOT_FOUND"
    
    def test_with_engine(self):
        """测试带引擎名称"""
        exc = ModelNotFoundError("unknown_model", engine_name="ali_funasr")
        assert exc.model_name == "unknown_model"
        assert exc.engine_name == "ali_funasr"
        assert "ali_funasr" in exc.message


class TestModelDownloadError:
    """测试模型下载错误"""
    
    def test_basic(self):
        """测试基本创建"""
        exc = ModelDownloadError("paraformer-zh", "网络连接超时")
        assert exc.model_name == "paraformer-zh"
        assert "paraformer-zh" in exc.message
        assert exc.error_code == "MODEL_DOWNLOAD_ERROR"
    
    def test_with_url(self):
        """测试带下载地址 (当前实现不支持 URL 参数)"""
        exc = ModelDownloadError(
            model_name="test",
            reason="HTTP 404",
        )
        # 当前实现只保存 model_name 和 reason
        assert hasattr(exc, 'model_name')
        assert hasattr(exc, 'reason')
        assert exc.reason == "HTTP 404"


class TestModelNotLoadedError:
    """测试模型未加载异常"""
    
    def test_basic(self):
        """测试基本创建"""
        exc = ModelNotLoadedError("SenseVoiceSmall")
        assert exc.model_name == "SenseVoiceSmall"
        assert exc.error_code == "MODEL_NOT_LOADED"


# ============================================================================
# 转写相关异常测试
# ============================================================================
class TestTranscriptionError:
    """测试转写错误"""
    
    def test_basic(self):
        """测试基本创建"""
        exc = TranscriptionError("音频文件损坏")
        assert "音频文件损坏" in exc.message
        assert exc.error_code == "TRANSCRIPTION_ERROR"
    
    def test_with_engine(self):
        """测试带引擎名"""
        exc = TranscriptionError("VAD 处理失败", engine_name="ali_funasr")
        assert exc.engine_name == "ali_funasr"
    
    def test_api_error(self):
        """测试 API 错误场景"""
        exc = TranscriptionError(
            "InvalidParameter: model not found",
            engine_name="ali_qwen"
        )
        assert "ali_qwen" in exc.message or exc.engine_name == "ali_qwen"


# ============================================================================
# 任务相关异常测试
# ============================================================================
class TestTaskNotFoundError:
    """测试任务未找到异常"""
    
    def test_with_task_id(self):
        """测试任务 ID"""
        exc = TaskNotFoundError("task_abc123")
        assert exc.task_id == "task_abc123"
        assert "task_abc123" in exc.message
        assert exc.error_code == "TASK_NOT_FOUND"


class TestTaskCancelledError:
    """测试任务取消异常"""
    
    def test_with_task_id(self):
        """测试任务 ID"""
        exc = TaskCancelledError("task_xyz789")
        assert exc.task_id == "task_xyz789"
        assert exc.error_code == "TASK_CANCELLED"


# ============================================================================
# 文件相关异常测试
# ============================================================================
class TestFileTooLargeError:
    """测试文件过大异常"""
    
    def test_with_sizes(self):
        """测试带文件大小"""
        exc = FileTooLargeError(
            file_size=600 * 1024 * 1024,  # 600 MB
            max_size=500 * 1024 * 1024,   # 500 MB
        )
        assert exc.file_size == 600 * 1024 * 1024
        assert exc.max_size == 500 * 1024 * 1024
        assert exc.error_code == "FILE_TOO_LARGE"
        # 消息应该包含可读大小
        assert "600" in exc.message or "500" in exc.message
    
    def test_small_file(self):
        """测试小文件 (KB 级别)"""
        exc = FileTooLargeError(
            file_size=100 * 1024,  # 100 KB
            max_size=50 * 1024,    # 50 KB
        )
        assert exc.file_size == 100 * 1024


class TestUnsupportedFormatError:
    """测试不支持格式异常"""
    
    def test_format_only(self):
        """测试只有格式名"""
        exc = UnsupportedFormatError(".xyz")
        assert exc.format_name == ".xyz"
        assert ".xyz" in exc.message
        assert exc.error_code == "UNSUPPORTED_FORMAT"
    
    def test_with_supported_list(self):
        """测试带支持列表"""
        exc = UnsupportedFormatError(
            ".abc",
            supported_formats=[".mp3", ".wav", ".flac"]
        )
        assert ".abc" in exc.message
        # 应该提示支持哪些格式
        assert ".mp3" in exc.message or "mp3" in exc.message
    
    def test_case_sensitivity(self):
        """测试大小写"""
        exc = UnsupportedFormatError(".MP3")
        assert exc.format_name == ".MP3"


# ============================================================================
# 异常继承关系测试
# ============================================================================
class TestExceptionHierarchy:
    """测试异常继承关系"""
    
    def test_all_inherit_from_base(self):
        """所有异常都继承自 STTException"""
        exceptions = [
            FFmpegNotFoundError(),
            EngineNotFoundError("test"),
            ModelNotFoundError("test"),
            ModelDownloadError("test", "reason"),
            ModelNotLoadedError("test"),
            APIKeyMissingError("engine", "VAR"),
            TranscriptionError("error"),
            TaskNotFoundError("task"),
            TaskCancelledError("task"),
            FileTooLargeError(100, 50),
            UnsupportedFormatError(".xyz"),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, STTException), f"{type(exc).__name__} 应该继承自 STTException"
    
    def test_can_catch_by_base(self):
        """可以用基类捕获所有子类异常"""
        def raise_engine_error():
            raise EngineNotFoundError("test")
        
        with pytest.raises(STTException):
            raise_engine_error()


# ============================================================================
# 实际使用场景测试
# ============================================================================
class TestRealWorldScenarios:
    """测试实际使用场景"""
    
    def test_error_chain(self):
        """测试错误链 (异常包装)"""
        try:
            # 模拟底层错误
            raise ValueError("底层错误")
        except ValueError as e:
            # 包装为 STT 异常
            exc = TranscriptionError(f"处理失败: {e}", engine_name="test")
            assert "底层错误" in exc.message
    
    def test_error_response_format(self):
        """测试错误响应格式 (API 使用)"""
        exc = TranscriptionError("音频损坏")
        d = exc.to_dict()
        
        # API 响应需要的字段
        assert "error_code" in d
        assert "message" in d
        
        # 可以直接 JSON 序列化
        import json
        json_str = json.dumps(d, ensure_ascii=False)
        assert "音频损坏" in json_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
