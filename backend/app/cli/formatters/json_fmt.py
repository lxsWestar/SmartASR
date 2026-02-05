"""
json_fmt.py - JSON 格式化器
============================

作用: 输出 JSON 格式，包含完整元数据
维护: AI + Human
"""

import json
from typing import TYPE_CHECKING

from .base import OutputFormatter

if TYPE_CHECKING:
    from backend.app.services.stt import STTResponse


class JsonFormatter(OutputFormatter):
    """JSON 格式化器"""
    
    @property
    def name(self) -> str:
        return "json"
    
    @property
    def extension(self) -> str:
        return "json"
    
    @property
    def description(self) -> str:
        return "JSON 格式 (含完整元数据)"
    
    def format(self, response: "STTResponse") -> str:
        """
        输出 JSON 格式
        
        包含:
        - text: 完整文本
        - segments: 时间戳片段
        - duration_ms: 音频时长
        - engine: 使用的引擎
        - model: 使用的模型
        - language_detected: 检测到的语言
        """
        data = {
            "text": response.text,
            "segments": [
                {
                    "start_ms": seg.start_ms,
                    "end_ms": seg.end_ms,
                    "text": seg.text,
                }
                for seg in response.segments
            ],
            "duration_ms": response.duration_ms,
            "engine": response.engine,
            "model": response.model,
        }
        
        if response.language_detected:
            data["language_detected"] = response.language_detected
        
        return json.dumps(data, ensure_ascii=False, indent=2)
