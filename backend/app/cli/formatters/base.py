"""
base.py - 格式化器基类
=======================

作用: 定义输出格式化器的抽象接口
维护: AI + Human
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.services.stt import STTResponse


class OutputFormatter(ABC):
    """输出格式化器基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """格式名称"""
        pass
    
    @property
    @abstractmethod
    def extension(self) -> str:
        """文件扩展名"""
        pass
    
    @property
    def description(self) -> str:
        """格式描述"""
        return ""
    
    @abstractmethod
    def format(self, response: "STTResponse") -> str:
        """
        将识别结果格式化为字符串
        
        Args:
            response: STT 识别结果
            
        Returns:
            格式化后的字符串
        """
        pass
