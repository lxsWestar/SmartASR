"""
base.py - STT 引擎基类
==========================

作用: 定义所有 STT 引擎的抽象基类，新引擎必须继承此类。
设计参考: pyvideotrans 的 API 抽象思路（独立实现，无代码复制）
关键方法: transcribe(), check_available(), get_models(), get_metadata()
维护: AI + Human
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .dto import STTRequest, STTResponse, EngineMetadata


@dataclass
class BaseSTTEngine(ABC):
    """
    STT 引擎基类
    
    新引擎实现步骤:
    1. 继承此类
    2. 实现所有抽象方法
    3. 用 @register_engine 装饰器注册
    
    示例:
        from backend.app.services.stt.base import BaseSTTEngine
        from backend.app.services.stt.registry import register_engine
        
        @register_engine
        @dataclass
        class MyEngine(BaseSTTEngine):
            name = "my_engine"
            display_name = "My Engine"
            engine_type = "local"
            ...
    """
    
    # 子类必须定义的类属性 (不是实例属性)
    name: str = ""                # 引擎标识，如 "ali_funasr"
    display_name: str = ""        # 显示名称（纯名称，不含厂商/部署方式），如 "FunASR"
    engine_type: str = "local"    # "local" 或 "cloud"
    vendor: str = ""              # 厂商，如 "Alibaba"
    
    # 运行时状态 (实例属性)
    device: str = field(default="cpu", init=False)
    is_cuda: bool = field(default=False, init=False)
    _model: object = field(default=None, init=False, repr=False)
    
    def __post_init__(self):
        """初始化后自动检测 CUDA"""
        self._detect_device()
    
    def _detect_device(self) -> None:
        """检测可用设备 (CPU/CUDA)"""
        try:
            import torch
            self.is_cuda = torch.cuda.is_available()
            self.device = "cuda" if self.is_cuda else "cpu"
        except ImportError:
            self.is_cuda = False
            self.device = "cpu"
    
    @classmethod
    @abstractmethod
    def get_metadata(cls) -> "EngineMetadata":
        """
        返回引擎元数据 (类方法，无需实例化即可调用)
        
        Returns:
            EngineMetadata: 引擎的完整元数据
        """
        pass
    
    @abstractmethod
    def transcribe(self, request: "STTRequest") -> "STTResponse":
        """
        执行语音识别
        
        Args:
            request: 识别请求对象
            
        Returns:
            STTResponse: 识别结果
            
        Raises:
            TranscriptionError: 识别失败时
        """
        pass
    
    @abstractmethod
    def get_models(self) -> List[str]:
        """
        获取支持的模型列表
        
        Returns:
            List[str]: 模型名称列表
        """
        pass
    
    @abstractmethod
    def check_available(self) -> Tuple[bool, str]:
        """
        检查引擎是否可用
        
        Returns:
            Tuple[bool, str]: (是否可用, 原因/错误信息)
        """
        pass
    
    def get_default_model(self) -> str:
        """
        获取默认模型名称
        
        Returns:
            str: 默认模型名称，若无则返回空字符串
        """
        metadata = self.get_metadata()
        for model in metadata.models:
            if model.default:
                return model.name
        return metadata.models[0].name if metadata.models else ""
    
    def load_model(self, model_name: Optional[str] = None) -> None:
        """
        加载模型 - 子类可重写
        
        Args:
            model_name: 模型名称，为 None 时加载默认模型
        """
        pass
    
    def unload_model(self) -> None:
        """卸载模型 - 子类可重写"""
        self._model = None
    
    def cleanup(self) -> None:
        """释放资源 - 子类可重写"""
        self._model = None
        try:
            import gc
            gc.collect()
            
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动清理资源"""
        self.cleanup()
        return False
