"""
vtt.py - WebVTT 字幕格式化器
=============================

作用: 输出 WebVTT 字幕格式
维护: AI + Human

WebVTT 格式示例:
    WEBVTT
    
    1
    00:00:00.000 --> 00:00:02.500
    这是第一句话
    
    2
    00:00:02.500 --> 00:00:05.000
    这是第二句话
"""

from typing import TYPE_CHECKING

from .base import OutputFormatter

if TYPE_CHECKING:
    from backend.app.services.stt import STTResponse


def format_time_vtt(ms: int) -> str:
    """
    毫秒转 WebVTT 时间格式
    
    格式: HH:MM:SS.mmm
    
    Args:
        ms: 毫秒数
        
    Returns:
        VTT 格式时间字符串
    """
    if ms < 0:
        ms = 0
    
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


class VttFormatter(OutputFormatter):
    """WebVTT 字幕格式化器"""
    
    @property
    def name(self) -> str:
        return "vtt"
    
    @property
    def extension(self) -> str:
        return "vtt"
    
    @property
    def description(self) -> str:
        return "WebVTT 字幕格式"
    
    def format(self, response: "STTResponse") -> str:
        """
        输出 WebVTT 字幕格式
        
        如果没有时间戳，则创建单条字幕
        """
        lines = ["WEBVTT", ""]
        
        if response.segments:
            for i, seg in enumerate(response.segments, 1):
                lines.append(str(i))
                lines.append(
                    f"{format_time_vtt(seg.start_ms)} --> {format_time_vtt(seg.end_ms)}"
                )
                lines.append(seg.text)
                lines.append("")
        else:
            # 没有时间戳，创建整体字幕
            lines.append("1")
            lines.append(
                f"{format_time_vtt(0)} --> {format_time_vtt(response.duration_ms)}"
            )
            lines.append(response.text)
            lines.append("")
        
        return "\n".join(lines)
