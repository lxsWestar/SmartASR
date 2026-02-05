"""
DTO 单元测试 (V2 - 重构版)
============================

测试原则:
1. 覆盖所有 DTO 类
2. 测试边界情况和异常输入
3. 测试序列化/反序列化往返
4. 不依赖其他模块的具体实现
"""

import pytest
import json
from pathlib import Path

from backend.app.services.stt.dto import (
    UsageInfo,
    STTRequest,
    STTSegment,
    STTResponse,
    ParameterSpec,
    ModelInfo,
    EngineMetadata,
)


# ============================================================================
# UsageInfo 测试
# ============================================================================
class TestUsageInfo:
    """测试使用量统计类"""
    
    def test_default_values(self):
        """测试默认值全为 0"""
        usage = UsageInfo()
        assert usage.audio_duration_ms == 0
        assert usage.processing_time_ms == 0
        assert usage.api_calls == 0
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.characters == 0
    
    def test_local_engine_usage(self):
        """测试本地引擎场景 (只有时长和字符数)"""
        usage = UsageInfo(
            audio_duration_ms=60000,  # 1分钟
            processing_time_ms=3500,
            characters=256,
        )
        assert usage.audio_duration_ms == 60000
        assert usage.processing_time_ms == 3500
        assert usage.characters == 256
        # 本地引擎没有 API 调用和 token
        assert usage.api_calls == 0
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
    
    def test_cloud_engine_usage(self):
        """测试云端引擎场景 (包含 API 调用和 token)"""
        usage = UsageInfo(
            audio_duration_ms=120000,  # 2分钟
            processing_time_ms=5000,
            api_calls=6,  # VAD 切分后多次调用
            input_tokens=12000,
            output_tokens=500,
            characters=850,
        )
        assert usage.api_calls == 6
        assert usage.input_tokens == 12000
        assert usage.output_tokens == 500
    
    def test_to_dict_completeness(self):
        """测试 to_dict 包含所有字段"""
        usage = UsageInfo(
            audio_duration_ms=1000,
            processing_time_ms=200,
            api_calls=1,
            input_tokens=100,
            output_tokens=50,
            characters=20,
        )
        d = usage.to_dict()
        
        # 必须包含所有 6 个字段
        expected_keys = {
            "audio_duration_ms", "processing_time_ms", "api_calls",
            "input_tokens", "output_tokens", "characters"
        }
        assert set(d.keys()) == expected_keys
        
        # 值正确
        assert d["audio_duration_ms"] == 1000
        assert d["characters"] == 20


# ============================================================================
# STTSegment 测试
# ============================================================================
class TestSTTSegment:
    """测试识别片段类"""
    
    def test_basic_creation(self):
        """测试基本创建"""
        seg = STTSegment(start_ms=0, end_ms=5000, text="你好世界")
        assert seg.start_ms == 0
        assert seg.end_ms == 5000
        assert seg.text == "你好世界"
    
    def test_duration_property(self):
        """测试时长计算"""
        seg = STTSegment(start_ms=1000, end_ms=3500, text="测试")
        assert seg.duration_ms == 2500
    
    def test_zero_duration_segment(self):
        """测试零时长片段 (可能来自无声或错误)"""
        seg = STTSegment(start_ms=1000, end_ms=1000, text="")
        assert seg.duration_ms == 0
        assert seg.text == ""
    
    def test_empty_text(self):
        """测试空文本片段"""
        seg = STTSegment(start_ms=0, end_ms=1000, text="")
        assert seg.text == ""
        assert seg.duration_ms == 1000
    
    def test_unicode_text(self):
        """测试 Unicode 文本 (中日韩英混合)"""
        text = "Hello こんにちは 你好 🎤"
        seg = STTSegment(start_ms=0, end_ms=1000, text=text)
        assert seg.text == text
    
    def test_to_dict(self):
        """测试字典转换"""
        seg = STTSegment(start_ms=100, end_ms=200, text="test")
        d = seg.to_dict()
        assert d == {"start_ms": 100, "end_ms": 200, "text": "test"}
    
    def test_long_text(self):
        """测试长文本"""
        long_text = "这是一段很长的文本" * 100
        seg = STTSegment(start_ms=0, end_ms=60000, text=long_text)
        assert len(seg.text) == len(long_text)


# ============================================================================
# STTRequest 测试
# ============================================================================
class TestSTTRequest:
    """测试识别请求类"""
    
    def test_minimal_request(self):
        """测试最小请求 (只有必填字段)"""
        req = STTRequest(audio_path=Path("/audio/test.mp3"))
        assert req.audio_path == Path("/audio/test.mp3")
        assert req.language == "auto"
        assert req.engine == "ali_funasr"
        assert req.model is None
        assert req.options == {}
        assert req.callback_url is None
    
    def test_full_request(self):
        """测试完整请求"""
        req = STTRequest(
            audio_path=Path("/audio/test.mp3"),
            language="zh",
            engine="ali_qwen",
            model="qwen3-asr-turbo",
            options={"api_key": "sk-xxx", "enable_itn": True},
            callback_url="https://example.com/webhook",
        )
        assert req.language == "zh"
        assert req.engine == "ali_qwen"
        assert req.model == "qwen3-asr-turbo"
        assert req.options["api_key"] == "sk-xxx"
        assert req.callback_url == "https://example.com/webhook"
    
    def test_windows_path(self):
        """测试 Windows 路径"""
        req = STTRequest(audio_path=Path(r"D:\audio\test.mp3"))
        assert req.audio_path == Path(r"D:\audio\test.mp3")
    
    def test_to_dict_path_serialization(self):
        """测试路径序列化为字符串"""
        req = STTRequest(audio_path=Path("/test/audio.mp3"))
        d = req.to_dict()
        # Path 应该转为字符串
        assert isinstance(d["audio_path"], str)
        # Windows 和 Unix 路径分隔符可能不同
        assert "audio.mp3" in d["audio_path"]
    
    def test_options_isolation(self):
        """测试 options 不会相互污染"""
        req1 = STTRequest(audio_path=Path("/a.mp3"))
        req2 = STTRequest(audio_path=Path("/b.mp3"))
        
        req1.options["key"] = "value1"
        assert "key" not in req2.options


# ============================================================================
# STTResponse 测试
# ============================================================================
class TestSTTResponse:
    """测试识别结果类"""
    
    def test_minimal_response(self):
        """测试最小响应"""
        resp = STTResponse(
            text="",
            segments=[],
            duration_ms=0,
            engine="test",
            model="test",
        )
        assert resp.text == ""
        assert resp.segments == []
        assert resp.language_detected is None
        assert resp.usage is None
    
    def test_response_with_segments(self):
        """测试带片段的响应"""
        segments = [
            STTSegment(0, 2000, "你好"),
            STTSegment(2000, 5000, "世界"),
        ]
        resp = STTResponse(
            text="你好 世界",
            segments=segments,
            duration_ms=5000,
            engine="ali_funasr",
            model="SenseVoiceSmall",
        )
        assert len(resp.segments) == 2
        assert resp.segments[0].text == "你好"
        assert resp.segments[1].text == "世界"
    
    def test_response_with_usage(self):
        """测试带 usage 的响应"""
        usage = UsageInfo(
            audio_duration_ms=5000,
            processing_time_ms=1200,
            characters=4,
        )
        resp = STTResponse(
            text="测试",
            segments=[],
            duration_ms=5000,
            engine="test",
            model="test",
            usage=usage,
        )
        assert resp.usage is not None
        assert resp.usage.audio_duration_ms == 5000
    
    def test_to_dict_with_usage(self):
        """测试带 usage 的字典转换"""
        usage = UsageInfo(processing_time_ms=100)
        resp = STTResponse(
            text="test",
            segments=[STTSegment(0, 1000, "test")],
            duration_ms=1000,
            engine="e",
            model="m",
            usage=usage,
        )
        d = resp.to_dict()
        
        assert "usage" in d
        assert d["usage"]["processing_time_ms"] == 100
        assert len(d["segments"]) == 1
    
    def test_to_dict_without_usage(self):
        """测试无 usage 时不包含该字段"""
        resp = STTResponse(
            text="test",
            segments=[],
            duration_ms=1000,
            engine="e",
            model="m",
        )
        d = resp.to_dict()
        assert "usage" not in d
    
    def test_to_json_valid(self):
        """测试 JSON 输出有效"""
        resp = STTResponse(
            text="你好",
            segments=[STTSegment(0, 1000, "你好")],
            duration_ms=1000,
            engine="test",
            model="test",
            language_detected="zh",
        )
        j = resp.to_json()
        
        # 确保是有效 JSON
        data = json.loads(j)
        assert data["text"] == "你好"
        assert data["language_detected"] == "zh"
    
    def test_to_json_unicode(self):
        """测试 JSON 中文不转义"""
        resp = STTResponse(
            text="中文测试",
            segments=[],
            duration_ms=1000,
            engine="test",
            model="test",
        )
        j = resp.to_json()
        # ensure_ascii=False 应该保留中文
        assert "中文测试" in j


# ============================================================================
# ParameterSpec 测试
# ============================================================================
class TestParameterSpec:
    """测试参数规格类"""
    
    def test_minimal_spec(self):
        """测试最小参数规格"""
        spec = ParameterSpec(name="api_key", type="string")
        assert spec.name == "api_key"
        assert spec.type == "string"
        assert spec.required is False
        assert spec.default is None
        assert spec.options is None
        assert spec.description == ""
    
    def test_required_param(self):
        """测试必填参数"""
        spec = ParameterSpec(
            name="language",
            type="string",
            required=True,
            options=["zh", "en", "ja"],
            description="识别语言",
        )
        assert spec.required is True
        assert spec.options == ["zh", "en", "ja"]
    
    def test_with_default(self):
        """测试带默认值的参数"""
        spec = ParameterSpec(
            name="enable_itn",
            type="boolean",
            default=False,
            description="是否启用逆文本正则化",
        )
        assert spec.default is False
    
    def test_to_dict_excludes_none(self):
        """测试 to_dict 不包含 None 的可选字段"""
        spec = ParameterSpec(name="test", type="string")
        d = spec.to_dict()
        
        # default 和 options 为 None 时不应该出现
        assert "default" not in d
        assert "options" not in d
    
    def test_to_dict_includes_values(self):
        """测试 to_dict 包含有值的字段"""
        spec = ParameterSpec(
            name="model",
            type="string",
            default="auto",
            options=["auto", "small", "large"],
        )
        d = spec.to_dict()
        
        assert d["default"] == "auto"
        assert d["options"] == ["auto", "small", "large"]


# ============================================================================
# ModelInfo 测试
# ============================================================================
class TestModelInfo:
    """测试模型信息类"""
    
    def test_minimal_model(self):
        """测试最小模型信息"""
        model = ModelInfo(
            name="SenseVoiceSmall",
            display_name="SenseVoice 小模型",
            description="FunASR 语音识别模型",
            languages=["zh", "en"],
            size="500MB",
        )
        assert model.name == "SenseVoiceSmall"
        assert model.default is False
        assert model.parameters == []
        assert model.features == []
    
    def test_default_model(self):
        """测试默认模型"""
        model = ModelInfo(
            name="default_model",
            display_name="默认",
            description="默认模型",
            languages=["zh"],
            size="1GB",
            default=True,
        )
        assert model.default is True
    
    def test_model_with_features(self):
        """测试带特性标签的模型"""
        model = ModelInfo(
            name="qwen3-asr-turbo",
            display_name="Qwen3-ASR Turbo",
            description="通义千问语音模型",
            languages=["zh", "en", "ja", "ko"],
            size="cloud",
            features=["streaming", "punctuation", "emotion"],
        )
        assert "streaming" in model.features
        assert len(model.features) == 3
    
    def test_to_dict(self):
        """测试字典转换"""
        model = ModelInfo(
            name="test",
            display_name="测试",
            description="描述",
            languages=["zh"],
            size="100MB",
            parameters=[
                ParameterSpec(name="param1", type="string"),
            ],
        )
        d = model.to_dict()
        
        assert d["name"] == "test"
        assert len(d["parameters"]) == 1
        assert d["parameters"][0]["name"] == "param1"


# ============================================================================
# EngineMetadata 测试
# ============================================================================
class TestEngineMetadata:
    """测试引擎元数据类"""
    
    def test_local_engine(self):
        """测试本地引擎元数据"""
        meta = EngineMetadata(
            name="ali_funasr",
            display_name="阿里 FunASR",
            type="local",
            description="本地离线语音识别",
            requires_api_key=False,
        )
        assert meta.type == "local"
        assert meta.requires_api_key is False
        assert meta.version == "1.0.0"
    
    def test_cloud_engine(self):
        """测试云端引擎元数据"""
        meta = EngineMetadata(
            name="ali_qwen",
            display_name="阿里百炼 Qwen-ASR",
            type="cloud",
            description="云端语音识别服务",
            requires_api_key=True,
            supported_languages=["zh", "en", "ja", "ko"],
        )
        assert meta.type == "cloud"
        assert meta.requires_api_key is True
        assert "zh" in meta.supported_languages
    
    def test_engine_with_models(self):
        """测试带模型列表的引擎"""
        meta = EngineMetadata(
            name="test",
            display_name="测试",
            type="local",
            description="测试引擎",
            models=[
                ModelInfo(
                    name="model1",
                    display_name="模型1",
                    description="第一个模型",
                    languages=["zh"],
                    size="1GB",
                    default=True,
                ),
                ModelInfo(
                    name="model2",
                    display_name="模型2",
                    description="第二个模型",
                    languages=["en"],
                    size="2GB",
                ),
            ],
        )
        assert len(meta.models) == 2
        assert meta.models[0].default is True
        assert meta.models[1].default is False
    
    def test_to_dict_completeness(self):
        """测试 to_dict 完整性"""
        meta = EngineMetadata(
            name="test",
            display_name="测试",
            type="local",
            description="描述",
            version="2.0.0",
            supported_languages=["zh"],
            requires_api_key=True,
        )
        d = meta.to_dict()
        
        expected_keys = {
            "name", "display_name", "type", "description", "version",
            "supported_languages", "models", "requires_api_key", "parameters"
        }
        assert set(d.keys()) == expected_keys
        assert d["version"] == "2.0.0"
    
    def test_to_json(self):
        """测试 JSON 转换"""
        meta = EngineMetadata(
            name="test",
            display_name="测试引擎",
            type="local",
            description="测试",
        )
        j = meta.to_json()
        
        data = json.loads(j)
        assert data["name"] == "test"
        assert "测试引擎" in j  # 确保中文不被转义


# ============================================================================
# 边界情况和错误处理测试
# ============================================================================
class TestEdgeCases:
    """测试边界情况"""
    
    def test_negative_timestamps(self):
        """测试负时间戳 (不应该出现，但不会崩溃)"""
        seg = STTSegment(start_ms=-100, end_ms=1000, text="test")
        # duration 会变成 1100
        assert seg.duration_ms == 1100
    
    def test_very_large_duration(self):
        """测试超长音频 (10小时)"""
        ten_hours_ms = 10 * 60 * 60 * 1000
        usage = UsageInfo(audio_duration_ms=ten_hours_ms)
        assert usage.audio_duration_ms == ten_hours_ms
    
    def test_special_characters_in_text(self):
        """测试特殊字符"""
        text = 'He said "Hello" & <escaped> \'quotes\''
        seg = STTSegment(start_ms=0, end_ms=1000, text=text)
        assert seg.text == text
        
        # JSON 序列化应该正确处理
        d = seg.to_dict()
        j = json.dumps(d)
        restored = json.loads(j)
        assert restored["text"] == text
    
    def test_newlines_in_text(self):
        """测试文本中的换行符"""
        text = "第一行\n第二行\r\n第三行"
        seg = STTSegment(start_ms=0, end_ms=1000, text=text)
        d = seg.to_dict()
        assert "\n" in d["text"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
