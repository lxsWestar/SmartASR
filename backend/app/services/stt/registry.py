"""
registry.py - 引擎注册中心
==============================

作用: 实现插件式引擎管理，放文件即注册，删文件即移除。
关键 API: @register_engine, list_engines(), get_engine(), get_engine_class()
维护: AI + Human
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type, TYPE_CHECKING

from .exceptions import EngineNotFoundError

if TYPE_CHECKING:
    from .base import BaseSTTEngine
    from .dto import EngineMetadata


# 全局引擎注册表
_engine_registry: Dict[str, Type["BaseSTTEngine"]] = {}


def register_engine(cls: Type["BaseSTTEngine"]) -> Type["BaseSTTEngine"]:
    """
    引擎注册装饰器
    
    使用示例:
        @register_engine
        @dataclass
        class MyEngine(BaseSTTEngine):
            name = "my_engine"
            ...
    
    Args:
        cls: 引擎类
        
    Returns:
        原始类（不做修改）
    """
    if hasattr(cls, "name") and cls.name:
        _engine_registry[cls.name] = cls
    return cls


def unregister_engine(name: str) -> bool:
    """
    取消注册引擎
    
    Args:
        name: 引擎名称
        
    Returns:
        bool: 是否成功取消
    """
    if name in _engine_registry:
        del _engine_registry[name]
        return True
    return False


def get_engine_class(name: str) -> Type["BaseSTTEngine"]:
    """
    获取引擎类
    
    Args:
        name: 引擎名称
        
    Returns:
        引擎类
        
    Raises:
        EngineNotFoundError: 引擎不存在时
    """
    if name not in _engine_registry:
        raise EngineNotFoundError(name)
    return _engine_registry[name]


def create_engine(name: str, **kwargs) -> "BaseSTTEngine":
    """
    创建引擎实例
    
    Args:
        name: 引擎名称
        **kwargs: 传递给引擎构造函数的参数
        
    Returns:
        引擎实例
        
    Raises:
        EngineNotFoundError: 引擎不存在时
    """
    cls = get_engine_class(name)
    return cls(**kwargs)


def list_engines() -> List[str]:
    """
    列出所有已注册的引擎名称
    
    Returns:
        List[str]: 引擎名称列表
    """
    return list(_engine_registry.keys())


def get_all_engines() -> Dict[str, Type["BaseSTTEngine"]]:
    """
    获取所有已注册的引擎类
    
    Returns:
        Dict[str, Type[BaseSTTEngine]]: 引擎名称到类的映射
    """
    return _engine_registry.copy()


def get_engine_metadata(name: str) -> "EngineMetadata":
    """
    获取引擎元数据
    
    Args:
        name: 引擎名称
        
    Returns:
        EngineMetadata: 引擎元数据
        
    Raises:
        EngineNotFoundError: 引擎不存在时
    """
    cls = get_engine_class(name)
    return cls.get_metadata()


def list_engines_metadata() -> List["EngineMetadata"]:
    """
    列出所有引擎的元数据
    
    Returns:
        List[EngineMetadata]: 元数据列表
    """
    return [cls.get_metadata() for cls in _engine_registry.values()]


def discover_engines(package_path: Optional[str] = None) -> int:
    """
    自动发现并加载引擎
    
    扫描 engines 目录下所有非 _ 开头的 .py 文件，
    自动导入以触发 @register_engine 装饰器。
    
    Args:
        package_path: 引擎包路径，为 None 时使用默认路径
        
    Returns:
        int: 发现的引擎数量
    """
    if package_path is None:
        # 默认路径：当前包下的 engines 子包
        engines_dir = Path(__file__).parent / "engines"
    else:
        engines_dir = Path(package_path)
    
    if not engines_dir.exists():
        return 0
    
    count = 0
    
    # 遍历目录中的 .py 文件
    for file in engines_dir.glob("*.py"):
        # 跳过 __init__.py 和 _ 开头的文件
        if file.name.startswith("_"):
            continue
        
        module_name = file.stem
        
        try:
            # 构建完整模块路径
            full_module_name = f"backend.app.services.stt.engines.{module_name}"
            importlib.import_module(full_module_name)
            count += 1
        except ImportError as e:
            # 导入失败时静默跳过，不影响其他引擎
            print(f"警告: 引擎 {module_name} 加载失败: {e}")
    
    return count


def check_engine_available(name: str) -> tuple:
    """
    检查引擎是否可用
    
    Args:
        name: 引擎名称
        
    Returns:
        Tuple[bool, str]: (是否可用, 原因/错误信息)
    """
    try:
        engine = create_engine(name)
        return engine.check_available()
    except EngineNotFoundError:
        return False, f"引擎 '{name}' 未注册"
    except Exception as e:
        return False, str(e)
