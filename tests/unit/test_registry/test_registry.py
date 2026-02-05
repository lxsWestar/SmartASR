"""
注册中心单元测试 (V2 - 重构版)
================================

测试原则:
1. 只使用公共 API，不直接操作 _engine_registry
2. 使用 fixture 进行隔离
3. 测试边界情况和错误处理
4. 覆盖实际使用场景
"""

import pytest
from typing import List, Tuple, Optional

from backend.app.services.stt.base import BaseSTTEngine
from backend.app.services.stt.registry import (
    register_engine,
    unregister_engine,
    get_engine_class,
    create_engine,
    list_engines,
    get_all_engines,
)
from backend.app.services.stt.dto import (
    STTRequest,
    STTResponse,
    STTSegment,
    EngineMetadata,
    UsageInfo,
)
from backend.app.services.stt.exceptions import EngineNotFoundError


# ============================================================================
# 测试用 Mock 引擎
# ============================================================================
def create_mock_engine_class(engine_name: str, engine_type: str = "local"):
    """动态创建 Mock 引擎类"""
    
    class DynamicMockEngine(BaseSTTEngine):
        """动态创建的 Mock 引擎"""
        
        def __init__(self):
            self.name = engine_name
            self.display_name = f"Mock {engine_name}"
            self.engine_type = engine_type
        
        @classmethod
        def get_metadata(cls) -> EngineMetadata:
            return EngineMetadata(
                name=engine_name,
                display_name=f"Mock {engine_name}",
                type=engine_type,
                description=f"Mock engine for testing: {engine_name}",
            )
        
        def transcribe(self, request: STTRequest) -> STTResponse:
            return STTResponse(
                text=f"Mock result from {engine_name}",
                segments=[STTSegment(0, 1000, f"Mock result from {engine_name}")],
                duration_ms=1000,
                engine=self.name,
                model="mock_model",
                usage=UsageInfo(processing_time_ms=100),
            )
        
        def get_models(self) -> List[str]:
            return ["mock_model"]
        
        def check_available(self) -> Tuple[bool, str]:
            return True, f"{engine_name} is available"
    
    # 设置类属性
    DynamicMockEngine.name = engine_name
    DynamicMockEngine.__name__ = f"MockEngine_{engine_name}"
    DynamicMockEngine.__qualname__ = f"MockEngine_{engine_name}"
    
    return DynamicMockEngine


# ============================================================================
# Fixtures
# ============================================================================
@pytest.fixture
def clean_registry():
    """
    清理注册表的 fixture
    
    在每个测试前后保存/恢复注册表状态
    """
    from backend.app.services.stt.registry import _engine_registry
    
    # 保存原始状态
    original = _engine_registry.copy()
    
    yield _engine_registry
    
    # 恢复原始状态
    _engine_registry.clear()
    _engine_registry.update(original)


@pytest.fixture
def registered_mock_engine(clean_registry):
    """注册一个 Mock 引擎用于测试"""
    MockEngine = create_mock_engine_class("fixture_engine")
    register_engine(MockEngine)
    return MockEngine


# ============================================================================
# 注册功能测试
# ============================================================================
class TestEngineRegistration:
    """测试引擎注册功能"""
    
    def test_register_with_decorator(self, clean_registry):
        """测试使用装饰器注册"""
        @register_engine
        class DecoratorEngine(BaseSTTEngine):
            name = "decorator_test"
            display_name = "Decorator Test"
            engine_type = "local"
            
            @classmethod
            def get_metadata(cls):
                return EngineMetadata(
                    name="decorator_test",
                    display_name="Decorator Test",
                    type="local",
                    description="Test",
                )
            
            def transcribe(self, request):
                return STTResponse(text="", segments=[], duration_ms=0, 
                                   engine=self.name, model="test")
            
            def get_models(self):
                return []
            
            def check_available(self):
                return True, "OK"
        
        # 验证已注册
        assert "decorator_test" in list_engines()
    
    def test_register_function_call(self, clean_registry):
        """测试函数调用方式注册"""
        MockEngine = create_mock_engine_class("func_test")
        register_engine(MockEngine)
        
        assert "func_test" in list_engines()
    
    def test_register_returns_class(self, clean_registry):
        """测试注册返回原始类"""
        MockEngine = create_mock_engine_class("return_test")
        result = register_engine(MockEngine)
        
        assert result is MockEngine
    
    def test_duplicate_registration(self, clean_registry):
        """测试重复注册 (应该覆盖)"""
        Engine1 = create_mock_engine_class("dup_test")
        Engine2 = create_mock_engine_class("dup_test")
        
        register_engine(Engine1)
        register_engine(Engine2)
        
        # 第二个应该覆盖第一个
        cls = get_engine_class("dup_test")
        assert cls is Engine2


# ============================================================================
# 注销功能测试
# ============================================================================
class TestEngineUnregistration:
    """测试引擎注销功能"""
    
    def test_unregister_existing(self, clean_registry):
        """测试注销已存在的引擎"""
        MockEngine = create_mock_engine_class("unreg_test")
        register_engine(MockEngine)
        
        # 确认已注册
        assert "unreg_test" in list_engines()
        
        # 注销
        result = unregister_engine("unreg_test")
        assert result is True
        assert "unreg_test" not in list_engines()
    
    def test_unregister_nonexistent(self, clean_registry):
        """测试注销不存在的引擎"""
        result = unregister_engine("nonexistent_engine")
        assert result is False
    
    def test_unregister_twice(self, clean_registry):
        """测试重复注销"""
        MockEngine = create_mock_engine_class("twice_test")
        register_engine(MockEngine)
        
        assert unregister_engine("twice_test") is True
        assert unregister_engine("twice_test") is False


# ============================================================================
# 获取引擎测试
# ============================================================================
class TestGetEngine:
    """测试获取引擎"""
    
    def test_get_engine_class(self, registered_mock_engine):
        """测试获取引擎类"""
        cls = get_engine_class("fixture_engine")
        assert cls is registered_mock_engine
    
    def test_get_nonexistent_raises(self, clean_registry):
        """测试获取不存在的引擎抛出异常"""
        with pytest.raises(EngineNotFoundError) as exc_info:
            get_engine_class("definitely_not_exist")
        
        assert "definitely_not_exist" in str(exc_info.value)
    
    def test_create_engine_instance(self, registered_mock_engine):
        """测试创建引擎实例"""
        engine = create_engine("fixture_engine")
        
        assert engine is not None
        assert engine.name == "fixture_engine"
    
    def test_create_engine_is_new_instance(self, registered_mock_engine):
        """测试每次创建新实例"""
        engine1 = create_engine("fixture_engine")
        engine2 = create_engine("fixture_engine")
        
        # 应该是不同的实例
        assert engine1 is not engine2
    
    def test_create_nonexistent_raises(self, clean_registry):
        """测试创建不存在的引擎抛出异常"""
        with pytest.raises(EngineNotFoundError):
            create_engine("not_exist")


# ============================================================================
# 列表功能测试
# ============================================================================
class TestListEngines:
    """测试列出引擎"""
    
    def test_list_empty(self, clean_registry):
        """测试空注册表"""
        clean_registry.clear()
        engines = list_engines()
        assert engines == []
    
    def test_list_single(self, registered_mock_engine):
        """测试单个引擎"""
        engines = list_engines()
        assert "fixture_engine" in engines
    
    def test_list_multiple(self, clean_registry):
        """测试多个引擎"""
        Engine1 = create_mock_engine_class("engine_a")
        Engine2 = create_mock_engine_class("engine_b")
        Engine3 = create_mock_engine_class("engine_c")
        
        register_engine(Engine1)
        register_engine(Engine2)
        register_engine(Engine3)
        
        engines = list_engines()
        assert len(engines) >= 3
        assert "engine_a" in engines
        assert "engine_b" in engines
        assert "engine_c" in engines
    
    def test_get_all_engines(self, registered_mock_engine):
        """测试获取所有引擎字典"""
        all_engines = get_all_engines()
        
        assert isinstance(all_engines, dict)
        assert "fixture_engine" in all_engines
        assert all_engines["fixture_engine"] is registered_mock_engine


# ============================================================================
# 引擎功能测试
# ============================================================================
class TestEngineFunction:
    """测试引擎实际功能"""
    
    def test_engine_transcribe(self, registered_mock_engine):
        """测试引擎转写"""
        from pathlib import Path
        
        engine = create_engine("fixture_engine")
        request = STTRequest(audio_path=Path("/fake/audio.mp3"))
        
        response = engine.transcribe(request)
        
        assert response.text is not None
        assert response.engine == "fixture_engine"
        assert response.usage is not None
    
    def test_engine_check_available(self, registered_mock_engine):
        """测试引擎可用性检查"""
        engine = create_engine("fixture_engine")
        available, reason = engine.check_available()
        
        assert isinstance(available, bool)
        assert isinstance(reason, str)
    
    def test_engine_get_models(self, registered_mock_engine):
        """测试获取模型列表"""
        engine = create_engine("fixture_engine")
        models = engine.get_models()
        
        assert isinstance(models, list)
    
    def test_engine_metadata(self, registered_mock_engine):
        """测试引擎元数据"""
        metadata = registered_mock_engine.get_metadata()
        
        assert isinstance(metadata, EngineMetadata)
        assert metadata.name == "fixture_engine"


# ============================================================================
# 边界情况测试
# ============================================================================
class TestEdgeCases:
    """测试边界情况"""
    
    def test_engine_name_with_special_chars(self, clean_registry):
        """测试特殊字符引擎名 (不推荐但应该能处理)"""
        # 引擎名通常应该是 snake_case，但系统应该能处理其他格式
        Engine = create_mock_engine_class("test-engine-123")
        register_engine(Engine)
        
        assert "test-engine-123" in list_engines()
        cls = get_engine_class("test-engine-123")
        assert cls is Engine
    
    def test_concurrent_registration_safety(self, clean_registry):
        """测试并发注册安全性 (简单测试)"""
        # 注意: 完整的并发测试需要 threading
        engines = [create_mock_engine_class(f"concurrent_{i}") for i in range(10)]
        
        for engine in engines:
            register_engine(engine)
        
        for i in range(10):
            assert f"concurrent_{i}" in list_engines()


# ============================================================================
# 实际使用场景测试
# ============================================================================
class TestRealWorldScenarios:
    """测试实际使用场景"""
    
    def test_dynamic_engine_loading(self, clean_registry):
        """测试动态加载引擎场景"""
        # 场景: 用户放入新的引擎文件，系统自动发现
        
        # 初始状态: 没有 whisper 引擎
        assert "whisper_local" not in list_engines()
        
        # 模拟: 加载新引擎
        WhisperEngine = create_mock_engine_class("whisper_local")
        register_engine(WhisperEngine)
        
        # 现在可以使用了
        assert "whisper_local" in list_engines()
        engine = create_engine("whisper_local")
        assert engine.name == "whisper_local"
    
    def test_engine_hot_swap(self, clean_registry):
        """测试引擎热更换场景"""
        # 场景: 用户升级引擎版本
        
        # 旧版本
        OldEngine = create_mock_engine_class("hot_swap_engine")
        register_engine(OldEngine)
        
        old_instance = create_engine("hot_swap_engine")
        
        # 升级: 注册新版本 (覆盖)
        NewEngine = create_mock_engine_class("hot_swap_engine")
        register_engine(NewEngine)
        
        # 新创建的实例是新版本
        new_instance = create_engine("hot_swap_engine")
        
        # 注意: old_instance 仍然可用 (已创建的实例不受影响)
        assert old_instance.name == "hot_swap_engine"
        assert new_instance.name == "hot_swap_engine"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
