"""
tsv.py - TSV 表格格式化器
==========================

作用: 输出制表符分隔的表格格式，便于导入 Excel
维护: AI + Human

TSV 格式示例:
    start_ms	end_ms	text
    0	2500	这是第一句话
    2500	5000	这是第二句话
"""

from typing import TYPE_CHECKING

from .base import OutputFormatter

if TYPE_CHECKING:
    from backend.app.services.stt import STTResponse


class TsvFormatter(OutputFormatter):
    """TSV 表格格式化器"""
    
    @property
    def name(self) -> str:
        return "tsv"
    
    @property
    def extension(self) -> str:
        return "tsv"
    
    @property
    def description(self) -> str:
        return "TSV 表格格式 (制表符分隔)"
    
    def format(self, response: "STTResponse") -> str:
        """
        输出 TSV 格式
        
        列: start_ms, end_ms, text
        """
        lines = ["start_ms\tend_ms\ttext"]
        
        if response.segments:
            for seg in response.segments:
                # 替换文本中的制表符和换行
                text = seg.text.replace("\t", " ").replace("\n", " ")
                lines.append(f"{seg.start_ms}\t{seg.end_ms}\t{text}")
        else:
            # 没有时间戳
            text = response.text.replace("\t", " ").replace("\n", " ")
            lines.append(f"0\t{response.duration_ms}\t{text}")
        
        return "\n".join(lines)
