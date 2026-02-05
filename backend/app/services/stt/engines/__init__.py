"""
STT 引擎目录
============

放置引擎文件即自动注册，删除文件即移除引擎。

规则：
- 以 _ 开头的文件不会被自动加载（如 _template.py）
- 每个引擎文件应包含一个用 @register_engine 装饰的引擎类

示例引擎文件结构：
    from dataclasses import dataclass
    from backend.app.services.stt.base import BaseSTTEngine
    from backend.app.services.stt.registry import register_engine
    
    @register_engine
    @dataclass
    class MyEngine(BaseSTTEngine):
        name = "my_engine"
        display_name = "My Engine"
        engine_type = "local"  # 或 "cloud"
        
        @classmethod
        def get_metadata(cls):
            ...
        
        def transcribe(self, request):
            ...
        
        def get_models(self):
            ...
        
        def check_available(self):
            ...
"""

from pathlib import Path
import importlib


def _auto_discover():
    """自动发现并导入引擎模块"""
    engines_dir = Path(__file__).parent
    
    for file in engines_dir.glob("*.py"):
        # 跳过 __init__.py 和 _ 开头的文件
        if file.name.startswith("_"):
            continue
        
        module_name = file.stem
        
        try:
            importlib.import_module(f".{module_name}", package=__name__)
        except ImportError as e:
            # 导入失败时静默跳过
            pass


# 模块加载时自动发现引擎
_auto_discover()
