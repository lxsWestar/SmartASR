"""
compat.py - 跨平台兼容工具
==============================

作用: 处理 Windows/Linux/macOS 的路径和环境差异。
关键 API: IS_WINDOWS, to_ffmpeg_path(), get_temp_dir(), get_models_dir()
维护: AI + Human
"""

import sys
import os
from pathlib import Path
from typing import Optional


# 平台检测
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")
IS_MACOS = sys.platform == "darwin"


def to_ffmpeg_path(path: Path) -> str:
    """
    转换路径为 FFmpeg 可接受格式
    
    Windows 上 FFmpeg 使用 / 分隔符更可靠，
    避免反斜杠被解释为转义字符。
    
    Args:
        path: 路径对象
        
    Returns:
        str: FFmpeg 可用的路径字符串
    """
    if IS_WINDOWS:
        return path.as_posix()
    return str(path)


def get_temp_dir() -> Path:
    """
    获取临时目录
    
    Returns:
        Path: 临时目录路径
    """
    if IS_WINDOWS:
        temp = os.environ.get("TEMP") or os.environ.get("TMP") or "C:/Temp"
        return Path(temp)
    return Path("/tmp")


def get_cache_dir(app_name: str = "SmartASR") -> Path:
    """
    获取应用缓存目录
    
    Args:
        app_name: 应用名称
        
    Returns:
        Path: 缓存目录路径
    """
    if IS_WINDOWS:
        base = Path(os.environ.get("LOCALAPPDATA", "~/.cache"))
    elif IS_MACOS:
        base = Path("~/Library/Caches")
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", "~/.cache"))
    
    cache_dir = base.expanduser() / app_name
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_models_dir(app_name: str = "SmartASR") -> Path:
    """
    获取模型存储目录
    
    加载优先级:
    1. STT_MODELS_DIR 环境变量
    2. 项目目录下的 ./models (如果存在)
    3. 系统默认路径 (~/.local/share/SmartASR/models)
    
    Args:
        app_name: 应用名称
        
    Returns:
        Path: 模型目录路径
    """
    # 1. 优先使用环境变量
    env_dir = os.environ.get("STT_MODELS_DIR")
    if env_dir:
        models_dir = Path(env_dir)
        models_dir.mkdir(parents=True, exist_ok=True)
        return models_dir
    
    # 2. 检查项目目录下的 ./models
    # 从当前文件向上找项目根目录 (包含 pyproject.toml 的目录)
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            project_models = parent / "models"
            if project_models.exists():
                return project_models
            break
    
    # 也检查当前工作目录
    cwd_models = Path.cwd() / "models"
    if cwd_models.exists():
        return cwd_models
    
    # 3. 默认路径 (系统级)
    if IS_WINDOWS:
        base = Path(os.environ.get("LOCALAPPDATA", "~/.local/share"))
    elif IS_MACOS:
        base = Path("~/Library/Application Support")
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", "~/.local/share"))
    
    models_dir = base.expanduser() / app_name / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def setup_environment() -> None:
    """
    设置运行环境变量
    
    解决常见的多线程和库冲突问题。
    """
    # 限制 OpenMP 线程数，避免与 PyTorch 冲突
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    
    # 允许重复加载 OpenMP 库 (Windows 常见问题)
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    
    # 禁用 tokenizers 并行，避免死锁
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def setup_model_hub(hub: str = "auto") -> str:
    """
    设置模型下载源
    
    Args:
        hub: 指定源
            - "auto": 自动选择 (海外用 hf, 国内用 ms)
            - "hf": HuggingFace (海外推荐)
            - "ms": ModelScope (国内推荐)
    
    Returns:
        str: 实际使用的 hub ("hf" 或 "ms")
    """
    if hub == "auto":
        # 通过环境变量或检测选择
        hub = os.environ.get("FUNASR_HUB", "").lower()
        if hub not in ("hf", "ms"):
            # 默认使用 HuggingFace (海外更快)
            # 国内用户可设置 FUNASR_HUB=ms
            hub = "hf"
    
    if hub == "hf":
        # HuggingFace 设置 (海外)
        # 不设置镜像，直接用官方源
        pass
    elif hub == "ms":
        # ModelScope 设置 (国内)
        setup_modelscope_mirror()
    
    return hub


def setup_modelscope_mirror() -> None:
    """
    设置 ModelScope 镜像加速
    
    适用于中国大陆用户，加速 FunASR 等模型下载。
    """
    # ModelScope 国内站点 (不带 https://, 库内部会自动加)
    os.environ.setdefault("MODELSCOPE_DOMAIN", "www.modelscope.cn")
    
    # 自定义缓存目录 (可选)
    if IS_WINDOWS:
        default_cache = Path(os.environ.get("LOCALAPPDATA", "~/.cache")).expanduser() / "modelscope"
    else:
        default_cache = Path("~/.cache/modelscope").expanduser()
    
    os.environ.setdefault("MODELSCOPE_CACHE", str(default_cache))


def get_python_executable() -> str:
    """
    获取当前 Python 解释器路径
    
    Returns:
        str: Python 可执行文件路径
    """
    return sys.executable


def normalize_path(path: str) -> Path:
    """
    标准化路径
    
    Args:
        path: 路径字符串
        
    Returns:
        Path: 标准化后的路径对象
    """
    return Path(path).expanduser().resolve()
