"""
输出格式化器模块
================

支持的格式: txt, srt, vtt, json, tsv
"""

from .base import OutputFormatter
from .txt import TxtFormatter
from .srt import SrtFormatter
from .vtt import VttFormatter
from .json_fmt import JsonFormatter
from .tsv import TsvFormatter
from pathlib import Path
from typing import Optional, Dict, Type

# 格式化器注册表
_formatters: Dict[str, Type[OutputFormatter]] = {
    "txt": TxtFormatter,
    "text": TxtFormatter,
    "srt": SrtFormatter,
    "vtt": VttFormatter,
    "json": JsonFormatter,
    "tsv": TsvFormatter,
}


def get_formatter(format_name: str) -> Optional[OutputFormatter]:
    """获取格式化器实例"""
    formatter_class = _formatters.get(format_name.lower())
    if formatter_class:
        return formatter_class()
    return None


def list_formats() -> list[str]:
    """列出所有支持的格式"""
    # 去重，返回主要格式名
    return ["txt", "srt", "vtt", "json", "tsv"]


def detect_format_from_path(path: Path) -> str:
    """从文件路径推断输出格式"""
    ext = path.suffix.lower().lstrip(".")
    if ext in _formatters:
        return ext
    return "txt"


__all__ = [
    "OutputFormatter",
    "TxtFormatter",
    "SrtFormatter",
    "VttFormatter",
    "JsonFormatter",
    "TsvFormatter",
    "get_formatter",
    "list_formats",
    "detect_format_from_path",
]
