"""
txt.py - 纯文本格式化器
========================

作用: 输出纯文本格式
维护: AI + Human
"""

from typing import TYPE_CHECKING

from .base import OutputFormatter

if TYPE_CHECKING:
    from backend.app.services.stt import STTResponse


class TxtFormatter(OutputFormatter):
    """纯文本格式化器"""
    
    @property
    def name(self) -> str:
        return "txt"
    
    @property
    def extension(self) -> str:
        return "txt"
    
    @property
    def description(self) -> str:
        return "纯文本格式"
    
    def format(self, response: "STTResponse") -> str:
        """输出纯文本"""
        return response.text
