"""
SmartASR CLI
============

产品级命令行语音识别工具。

用法:
    python -m backend.app.cli transcribe audio.mp3
    python -m backend.app.cli engines list
    python -m backend.app.cli --help
"""

from .main import app, main

__version__ = "0.1.0"
__all__ = ["app", "main"]
