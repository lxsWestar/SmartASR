#!/usr/bin/env python
"""
快速测试脚本 - 验证已完成模块的基本功能
"""
import sys
from pathlib import Path

# 确保项目根目录在路径中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_exceptions():
    """测试 2: 异常类"""
    print("=" * 60)
    print("测试 2: 异常类")
    print("=" * 60)
    
    from backend.app.services.stt.exceptions import (
        STTException, FFmpegNotFoundError, EngineNotFoundError,
        ModelNotFoundError, APIKeyMissingError, TranscriptionError
    )
    
    # 测试基类
    e = STTException("测试错误", "TEST_001")
    print(f'✅ STTException: message="{e.message}", code="{e.error_code}"')
    
    # 测试子类
    e2 = EngineNotFoundError("funasr")
    print(f'✅ EngineNotFoundError: "{e2}"')
    
    e3 = APIKeyMissingError("ali_qwen")
    print(f'✅ APIKeyMissingError: "{e3}"')
    
    # 测试异常抛出和捕获
    try:
        raise FFmpegNotFoundError()
    except STTException as e:
        print(f"✅ 异常捕获正常: {e.error_code}")


def test_compat():
    """测试 3: 跨平台兼容层"""
    print("\n" + "=" * 60)
    print("测试 3: 跨平台兼容层")
    print("=" * 60)
    
    from backend.app.services.stt.compat import (
        IS_WINDOWS, IS_LINUX, IS_MACOS,
        to_ffmpeg_path, get_temp_dir, get_cache_dir,
        get_models_dir, normalize_path
    )
    
    print(f"✅ 平台检测: Windows={IS_WINDOWS}, Linux={IS_LINUX}, macOS={IS_MACOS}")
    
    # 测试路径转换
    test_path = Path("C:/Users/test/音频文件.mp3")
    ffmpeg_path = to_ffmpeg_path(test_path)
    print(f"✅ to_ffmpeg_path: {test_path} → {ffmpeg_path}")
    
    # 测试目录获取
    print(f"✅ get_temp_dir: {get_temp_dir()}")
    print(f"✅ get_cache_dir: {get_cache_dir()}")
    print(f"✅ get_models_dir: {get_models_dir()}")
    
    # 测试路径标准化
    normalized = normalize_path("C:\\Users\\test\\file.txt")
    print(f'✅ normalize_path: "C:\\\\Users\\\\test\\\\file.txt" → "{normalized}"')


def test_dto():
    """测试 4: 数据传输对象"""
    print("\n" + "=" * 60)
    print("测试 4: 数据传输对象 (DTO)")
    print("=" * 60)
    
    from backend.app.services.stt.dto import (
        STTRequest, STTResponse, STTSegment,
        EngineMetadata, ModelInfo, ParameterSpec
    )
    
    # 测试 STTRequest
    request = STTRequest(
        audio_path=Path("test.mp3"),
        language="zh",
        engine="ali_funasr"
    )
    print(f"✅ STTRequest: engine={request.engine}, language={request.language}")
    
    # 测试 STTSegment
    segment = STTSegment(start_ms=0, end_ms=2000, text="你好世界")
    print(f"✅ STTSegment: {segment.start_ms}ms-{segment.end_ms}ms: '{segment.text}'")
    
    # 测试 STTResponse
    response = STTResponse(
        text="你好世界",
        segments=[segment],
        duration_ms=2000,
        engine="ali_funasr",
        model="SenseVoiceSmall"
    )
    print(f"✅ STTResponse: text='{response.text}', duration={response.duration_ms}ms")
    
    # 测试 ParameterSpec
    param = ParameterSpec(
        name="language",
        type="string",
        required=False,
        default="auto",
        options=["zh", "en", "auto"],
        description="识别语言"
    )
    print(f"✅ ParameterSpec: {param.name} ({param.type}), default={param.default}")
    
    # 测试 ModelInfo
    model = ModelInfo(
        name="SenseVoiceSmall",
        display_name="SenseVoice 小模型",
        description="多语言语音识别",
        languages=["zh", "en", "ja"],
        size="1.2GB",
        default=True
    )
    print(f"✅ ModelInfo: {model.name}, languages={model.languages}")
    
    # 测试 EngineMetadata
    metadata = EngineMetadata(
        name="ali_funasr",
        display_name="阿里 FunASR",
        type="local",
        description="本地语音识别引擎",
        supported_languages=["zh", "en"],
        models=[model]
    )
    print(f"✅ EngineMetadata: {metadata.name} ({metadata.type})")
    
    # 测试 to_dict
    metadata_dict = metadata.to_dict()
    print(f"✅ EngineMetadata.to_dict(): keys={list(metadata_dict.keys())}")


def test_registry():
    """测试 5: 引擎注册中心"""
    print("\n" + "=" * 60)
    print("测试 5: 引擎注册中心")
    print("=" * 60)
    
    from backend.app.services.stt.registry import (
        register_engine, list_engines, get_engine_class
    )
    from backend.app.services.stt.base import BaseSTTEngine
    from backend.app.services.stt.dto import (
        STTRequest, STTResponse, EngineMetadata, ModelInfo
    )
    from dataclasses import dataclass
    from typing import List, Tuple
    
    # 创建测试引擎 (装饰器不带参数)
    @register_engine
    @dataclass
    class TestEngine(BaseSTTEngine):
        name = "test_engine"
        display_name = "测试引擎"
        engine_type = "local"
        
        @classmethod
        def get_metadata(cls) -> EngineMetadata:
            return EngineMetadata(
                name="test_engine",
                display_name="测试引擎",
                type="local",
                description="用于测试的引擎",
                supported_languages=["zh", "en"],
                models=[
                    ModelInfo(
                        name="test_model",
                        display_name="测试模型",
                        description="测试用模型",
                        languages=["zh", "en"],
                        size="100MB",
                        default=True
                    )
                ]
            )
        
        def transcribe(self, request: STTRequest) -> STTResponse:
            return STTResponse(
                text="测试文本",
                segments=[],
                duration_ms=1000,
                engine=self.name,
                model="test_model"
            )
        
        def get_models(self) -> List[str]:
            return ["test_model"]
        
        def check_available(self) -> Tuple[bool, str]:
            return True, "可用"
    
    # 验证注册 - 通过 list_engines 检查 (返回引擎名称列表)
    engines = list_engines()
    is_registered = "test_engine" in engines
    print(f"✅ 引擎已注册: {is_registered}")
    
    # 列出引擎 (返回 List[str])
    print(f"✅ list_engines(): {engines}")
    
    # 获取引擎类
    engine_cls = get_engine_class("test_engine")
    print(f"✅ get_engine_class('test_engine'): {engine_cls.__name__}")
    
    # 获取元数据
    metadata = engine_cls.get_metadata()
    print(f"✅ 引擎元数据: name={metadata.name}, type={metadata.type}")


def test_audio_utils():
    """测试 6: 音频工具"""
    print("\n" + "=" * 60)
    print("测试 6: 音频工具")
    print("=" * 60)
    
    from backend.app.services.stt.audio_utils import (
        check_ffmpeg, get_ffmpeg_version
    )
    
    # 检查 FFmpeg
    ffmpeg_available = check_ffmpeg()
    print(f"✅ check_ffmpeg(): {ffmpeg_available}")
    
    if ffmpeg_available:
        version = get_ffmpeg_version()
        print(f"✅ get_ffmpeg_version(): {version}")
    else:
        print("⚠️ FFmpeg 未安装，跳过版本检测")


def test_config():
    """测试 7: 配置管理"""
    print("\n" + "=" * 60)
    print("测试 7: 配置管理")
    print("=" * 60)
    
    from backend.app.services.stt.config import STTConfig, get_config
    
    # 获取默认配置
    config = get_config()
    print(f"✅ get_config(): default_engine={config.default_engine}")
    print(f"✅ config.cache_dir: {config.cache_dir}")
    print(f"✅ config.models_dir: {config.models_dir}")
    print(f"✅ config.max_file_size_mb: {config.max_file_size_mb}")
    print(f"✅ config.api_timeout: {config.api_timeout}s")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("SmartASR 模块快速测试")
    print("=" * 60)
    
    tests = [
        ("异常类", test_exceptions),
        ("跨平台兼容层", test_compat),
        ("数据传输对象", test_dto),
        ("引擎注册中心", test_registry),
        ("音频工具", test_audio_utils),
        ("配置管理", test_config),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"通过: {passed}/{len(tests)}")
    print(f"失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，请检查!")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
