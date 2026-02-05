"""
FunASR 引擎集成测试
===================

测试真实的 FunASR 引擎识别能力。
运行前提：
- 安装 FunASR: pip install funasr
- 安装 torch (可选，用于 GPU)
- 首次运行会自动下载模型 (~900MB)

用法：
    pytest tests/integration/test_funasr/ -v -s
    pytest tests/integration/test_funasr/ -v -s -k "nhk"  # 只跑 NHK 测试
"""

import pytest
import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============ 检查 FunASR 是否可用 ============

def is_funasr_available() -> bool:
    """检查 FunASR 是否已安装"""
    try:
        import funasr
        return True
    except ImportError:
        return False


# 如果 FunASR 不可用，跳过所有测试
pytestmark = pytest.mark.skipif(
    not is_funasr_available(),
    reason="FunASR 未安装 (pip install funasr)"
)


# ============ Fixtures ============

@pytest.fixture(scope="module")
def funasr_engine():
    """创建 FunASR 引擎实例 (模块级别，避免重复加载模型)"""
    from backend.app.services.stt import create_engine
    
    engine = create_engine("ali_funasr")
    
    # 检查可用性
    available, reason = engine.check_available()
    if not available:
        pytest.skip(f"FunASR 引擎不可用: {reason}")
    
    logger.info(f"FunASR 引擎已创建: {engine.name}")
    yield engine
    
    # 清理 (释放 GPU 内存)
    import gc
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass
    gc.collect()


@pytest.fixture
def nhk_audio_path():
    """NHK 新闻音频文件路径"""
    path = Path(r"D:\tmp\fc5270a9e2d0964b40ec0ffec65f2ba6_64k.mp3")
    if not path.exists():
        pytest.skip(f"测试音频不存在: {path}")
    return path


@pytest.fixture
def sample_audio_path(tmp_path):
    """生成一个简单的测试音频 (静音)"""
    # 创建一个空的 WAV 文件用于基本测试
    import wave
    import struct
    
    audio_path = tmp_path / "silence.wav"
    with wave.open(str(audio_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        # 1 秒静音
        wav.writeframes(struct.pack("<" + "h" * 16000, *([0] * 16000)))
    
    return audio_path


# ============ 测试类 ============

class TestFunASRAvailability:
    """FunASR 可用性测试"""
    
    def test_engine_registered(self):
        """测试引擎是否已注册"""
        from backend.app.services.stt import list_engines
        
        engines = list_engines()
        assert "ali_funasr" in engines, f"引擎列表: {engines}"
    
    def test_engine_metadata(self):
        """测试引擎元数据"""
        from backend.app.services.stt import get_engine_metadata
        
        metadata = get_engine_metadata("ali_funasr")
        
        assert metadata.name == "ali_funasr"
        assert metadata.type == "local"
        assert "zh" in metadata.supported_languages
        assert len(metadata.models) >= 1
        
        # 检查默认模型
        default_models = [m for m in metadata.models if m.default]
        assert len(default_models) == 1
        logger.info(f"默认模型: {default_models[0].name}")
    
    def test_engine_available(self, funasr_engine):
        """测试引擎可用性检查"""
        available, reason = funasr_engine.check_available()
        
        logger.info(f"可用: {available}, 原因: {reason}")
        assert available is True
        assert reason == "ok" or "可用" in reason.lower() or available


class TestFunASRTranscription:
    """FunASR 识别测试"""
    
    def test_transcribe_nhk_news(self, funasr_engine, nhk_audio_path):
        """测试 NHK 新闻日语识别"""
        from backend.app.services.stt import STTRequest
        
        request = STTRequest(
            audio_path=nhk_audio_path,
            language="ja",  # 日语
            engine="ali_funasr",
            model="SenseVoiceSmall",
        )
        
        logger.info(f"开始识别: {nhk_audio_path}")
        result = funasr_engine.transcribe(request)
        
        # 基本断言
        assert result is not None
        assert result.text, "识别结果不应为空"
        assert len(result.text) > 10, f"文本太短: {result.text}"
        
        # 输出结果
        logger.info(f"识别文本 ({len(result.text)} 字):")
        logger.info(f"  {result.text[:200]}{'...' if len(result.text) > 200 else ''}")
        
        # 检查时间戳
        if result.segments:
            logger.info(f"片段数: {len(result.segments)}")
            for i, seg in enumerate(result.segments[:3]):
                logger.info(f"  [{seg.start_ms}-{seg.end_ms}] {seg.text[:50]}")
        
        # 检查 usage 统计
        if result.usage:
            logger.info(f"Usage: {result.usage}")
    
    def test_transcribe_nhk_auto_language(self, funasr_engine, nhk_audio_path):
        """测试自动语言检测"""
        from backend.app.services.stt import STTRequest
        
        request = STTRequest(
            audio_path=nhk_audio_path,
            language="auto",  # 自动检测
            engine="ali_funasr",
        )
        
        result = funasr_engine.transcribe(request)
        
        assert result.text
        logger.info(f"自动检测语言: {result.language_detected or '未返回'}")
        logger.info(f"识别文本: {result.text[:100]}...")
    
    def test_transcribe_with_itn(self, funasr_engine, nhk_audio_path):
        """测试逆文本正则化 (ITN)"""
        from backend.app.services.stt import STTRequest
        
        # 启用 ITN
        request_itn = STTRequest(
            audio_path=nhk_audio_path,
            language="ja",
            engine="ali_funasr",
            options={"use_itn": True},
        )
        
        result_itn = funasr_engine.transcribe(request_itn)
        
        # 禁用 ITN
        request_no_itn = STTRequest(
            audio_path=nhk_audio_path,
            language="ja",
            engine="ali_funasr",
            options={"use_itn": False},
        )
        
        result_no_itn = funasr_engine.transcribe(request_no_itn)
        
        logger.info(f"ITN 开启: {result_itn.text[:100]}...")
        logger.info(f"ITN 关闭: {result_no_itn.text[:100]}...")
        
        # 结果应该都有内容
        assert result_itn.text
        assert result_no_itn.text


class TestFunASREdgeCases:
    """边界情况测试"""
    
    def test_invalid_model(self, funasr_engine, nhk_audio_path):
        """测试无效模型名"""
        from backend.app.services.stt import STTRequest
        from backend.app.services.stt.exceptions import ModelNotFoundError
        
        request = STTRequest(
            audio_path=nhk_audio_path,
            language="ja",
            engine="ali_funasr",
            model="nonexistent_model",
        )
        
        with pytest.raises(ModelNotFoundError) as exc_info:
            funasr_engine.transcribe(request)
        
        assert "nonexistent_model" in str(exc_info.value)
    
    def test_file_not_found(self, funasr_engine):
        """测试文件不存在"""
        from backend.app.services.stt import STTRequest
        from backend.app.services.stt.exceptions import TranscriptionError
        
        request = STTRequest(
            audio_path=Path("/nonexistent/audio.wav"),
            language="ja",
            engine="ali_funasr",
        )
        
        with pytest.raises((TranscriptionError, FileNotFoundError)):
            funasr_engine.transcribe(request)


if __name__ == "__main__":
    # 直接运行此文件
    pytest.main([__file__, "-v", "-s"])

