"""
SmartASR API 模块
==================

提供 RESTful API 端点，包括：
- /api/stt/engines - 引擎管理
- /api/stt/transcribe - 语音识别
- /api/stt/tasks - 异步任务管理
"""

from .main import app, create_app

__all__ = ["app", "create_app"]
