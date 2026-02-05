"""
audio_utils.py - 音频预处理工具
==================================

作用: 将任意音频转为 16kHz mono WAV 格式，供 STT 引擎使用。
设计参考: pyvideotrans 的 FFmpeg 封装思路（独立实现，无代码复制）
关键 API: check_ffmpeg(), convert_to_16k_wav(), get_duration()
维护: AI + Human
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple

from .exceptions import FFmpegNotFoundError, UnsupportedFormatError
from .compat import to_ffmpeg_path, IS_WINDOWS


# 支持的音频格式
SUPPORTED_FORMATS = [
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac",
    ".wma", ".opus", ".webm", ".mp4", ".mkv", ".avi"
]


def check_ffmpeg() -> bool:
    """
    检查 FFmpeg 是否可用
    
    Returns:
        bool: FFmpeg 是否可用
    """
    return shutil.which("ffmpeg") is not None


def get_ffmpeg_version() -> str:
    """
    获取 FFmpeg 版本号
    
    Returns:
        str: 版本号字符串，如 "6.0"
        
    Raises:
        FFmpegNotFoundError: FFmpeg 不可用时
    """
    if not check_ffmpeg():
        raise FFmpegNotFoundError()
    
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # 解析版本号，例如 "ffmpeg version 6.0 Copyright..."
        first_line = result.stdout.split("\n")[0]
        parts = first_line.split()
        if len(parts) >= 3 and parts[0] == "ffmpeg":
            return parts[2]
        return "unknown"
    except Exception:
        return "unknown"


def get_duration(path: Path) -> float:
    """
    获取音频/视频时长（秒）
    
    Args:
        path: 文件路径
        
    Returns:
        float: 时长（秒）
        
    Raises:
        FFmpegNotFoundError: FFmpeg 不可用时
    """
    if not check_ffmpeg():
        raise FFmpegNotFoundError()
    
    ffprobe_path = shutil.which("ffprobe")
    if not ffprobe_path:
        raise FFmpegNotFoundError("ffprobe 未找到")
    
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                to_ffmpeg_path(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return float(result.stdout.strip())
    except (ValueError, subprocess.TimeoutExpired):
        return 0.0


def convert_to_16k_wav(
    input_path: Path,
    output_path: Optional[Path] = None,
    overwrite: bool = True,
) -> Path:
    """
    将音频转换为 16kHz 单声道 WAV 格式
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径，为 None 时自动生成
        overwrite: 是否覆盖已存在的文件
        
    Returns:
        Path: 输出文件路径
        
    Raises:
        FFmpegNotFoundError: FFmpeg 不可用时
        UnsupportedFormatError: 不支持的格式
        FileNotFoundError: 输入文件不存在
    """
    if not check_ffmpeg():
        raise FFmpegNotFoundError()
    
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")
    
    # 检查格式
    suffix = input_path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(suffix, SUPPORTED_FORMATS)
    
    # 生成输出路径
    if output_path is None:
        output_path = input_path.with_suffix(".16k.wav")
    else:
        output_path = Path(output_path)
    
    # 构建 FFmpeg 命令
    cmd = [
        "ffmpeg",
        "-y" if overwrite else "-n",  # 覆盖/不覆盖
        "-i", to_ffmpeg_path(input_path),
        "-ac", "1",          # 单声道
        "-ar", "16000",      # 16kHz 采样率
        "-c:a", "pcm_s16le", # 16-bit PCM
        to_ffmpeg_path(output_path),
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 分钟超时
        )
        
        if result.returncode != 0:
            raise FFmpegNotFoundError(f"FFmpeg 转换失败: {result.stderr}")
        
        return output_path
        
    except subprocess.TimeoutExpired:
        raise FFmpegNotFoundError("FFmpeg 转换超时")


def get_audio_info(path: Path) -> dict:
    """
    获取音频文件信息
    
    Args:
        path: 文件路径
        
    Returns:
        dict: 包含 duration, sample_rate, channels, codec 等信息
    """
    if not check_ffmpeg():
        raise FFmpegNotFoundError()
    
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_name,sample_rate,channels:format=duration",
                "-of", "json",
                to_ffmpeg_path(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        import json
        data = json.loads(result.stdout)
        
        stream = data.get("streams", [{}])[0]
        format_info = data.get("format", {})
        
        return {
            "duration": float(format_info.get("duration", 0)),
            "sample_rate": int(stream.get("sample_rate", 0)),
            "channels": int(stream.get("channels", 0)),
            "codec": stream.get("codec_name", "unknown"),
        }
        
    except Exception:
        return {
            "duration": 0,
            "sample_rate": 0,
            "channels": 0,
            "codec": "unknown",
        }
