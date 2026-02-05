"""
VAD (Voice Activity Detection) 工具模块

本模块提供语音活动检测功能，用于将长音频切分为语音片段。
这是一个可选模块，引擎可以按需导入使用。

设计理念:
- 不放在 BaseSTTEngine 基类中，避免强制所有引擎依赖 VAD
- 不在每个引擎中重复实现，提供统一的工具函数
- 支持多种 VAD 后端，自动选择最佳可用方法

支持的 VAD 方法:
1. silero - 使用 faster_whisper 内置的 silero-vad (推荐)
2. funasr - 使用 FunASR 的 fsmn-vad 模型
3. pydub - 使用 pydub 的静音检测 (轻量级)

使用示例:
    from backend.app.services.stt.vad_utils import (
        detect_speech_segments,
        cut_audio_by_vad,
        get_available_vad_methods
    )
    
    # 检测语音片段
    segments = detect_speech_segments(audio_path)
    # [(0, 2500), (3000, 5500), ...]
    
    # 切分音频文件
    chunks = cut_audio_by_vad(audio_path, output_dir)
    # [(chunk1.wav, 0, 2500), (chunk2.wav, 3000, 5500), ...]

作者: SmartASR Team
创建日期: 2026-01-26
"""

import logging
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal, Optional, Tuple

logger = logging.getLogger(__name__)

# VAD 方法类型
VADMethod = Literal["auto", "silero", "funasr", "pydub"]


@dataclass
class VADConfig:
    """VAD 配置参数"""
    
    # 通用参数
    min_speech_duration_ms: int = 250
    """最小语音片段时长 (毫秒)"""
    
    min_silence_duration_ms: int = 500
    """最小静音时长，用于分割语音 (毫秒)"""
    
    max_speech_duration_s: float = 30.0
    """最大语音片段时长 (秒)，超过将强制分割"""
    
    speech_pad_ms: int = 100
    """语音片段前后的填充时长 (毫秒)"""
    
    # silero-vad 特有参数
    threshold: float = 0.5
    """silero-vad 阈值 (0-1)，越高越严格"""
    
    # pydub 特有参数
    silence_thresh_db: int = -40
    """pydub 静音阈值 (dB)"""


@dataclass
class VADSegment:
    """VAD 检测到的语音片段"""
    
    start_ms: int
    """开始时间 (毫秒)"""
    
    end_ms: int
    """结束时间 (毫秒)"""
    
    @property
    def duration_ms(self) -> int:
        """片段时长 (毫秒)"""
        return self.end_ms - self.start_ms


# =============================================================================
# VAD 方法检测
# =============================================================================

def _check_silero_available() -> bool:
    """检查 silero-vad (faster_whisper) 是否可用"""
    try:
        from faster_whisper.vad import VadOptions, get_speech_timestamps
        from faster_whisper.audio import decode_audio
        return True
    except ImportError:
        return False


def _check_funasr_available() -> bool:
    """检查 FunASR VAD 是否可用"""
    try:
        from funasr import AutoModel
        return True
    except ImportError:
        return False


def _check_pydub_available() -> bool:
    """检查 pydub 是否可用"""
    try:
        from pydub import AudioSegment
        from pydub.silence import detect_nonsilent
        return True
    except ImportError:
        return False


def get_available_vad_methods() -> List[str]:
    """
    获取当前环境可用的 VAD 方法
    
    Returns:
        可用方法名称列表，按推荐顺序排列
    """
    methods = []
    
    if _check_silero_available():
        methods.append("silero")
    
    if _check_funasr_available():
        methods.append("funasr")
    
    if _check_pydub_available():
        methods.append("pydub")
    
    return methods


def _select_best_method(preferred: str = "auto") -> str:
    """
    选择最佳可用的 VAD 方法
    
    Args:
        preferred: 首选方法，"auto" 表示自动选择
        
    Returns:
        选中的方法名称
        
    Raises:
        RuntimeError: 没有可用的 VAD 方法
    """
    available = get_available_vad_methods()
    
    if not available:
        raise RuntimeError(
            "没有可用的 VAD 方法。请安装以下任一依赖:\n"
            "  - pip install faster-whisper  (推荐，使用 silero-vad)\n"
            "  - pip install funasr  (使用 fsmn-vad)\n"
            "  - pip install pydub  (轻量级静音检测)"
        )
    
    if preferred == "auto":
        return available[0]  # 返回第一个可用的 (按优先级排序)
    
    if preferred in available:
        return preferred
    
    logger.warning(f"请求的 VAD 方法 '{preferred}' 不可用，回退到 '{available[0]}'")
    return available[0]


# =============================================================================
# VAD 实现: silero-vad (faster_whisper)
# =============================================================================

def _detect_with_silero(
    audio_path: Path,
    config: VADConfig
) -> List[VADSegment]:
    """
    使用 silero-vad 检测语音片段
    
    设计参考: pyvideotrans 的音频切分逻辑（独立实现）
    """
    from faster_whisper.audio import decode_audio
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    
    sampling_rate = 16000
    
    # 解码音频
    audio_data = decode_audio(str(audio_path), sampling_rate=sampling_rate)
    
    # VAD 参数
    vad_options = VadOptions(
        threshold=config.threshold,
        min_speech_duration_ms=config.min_speech_duration_ms,
        max_speech_duration_s=config.max_speech_duration_s,
        min_silence_duration_ms=config.min_silence_duration_ms,
        speech_pad_ms=config.speech_pad_ms,
    )
    
    # 检测语音片段
    timestamps = get_speech_timestamps(audio_data, vad_options=vad_options)
    
    # 转换为毫秒
    segments = []
    for ts in timestamps:
        start_ms = int(round(ts["start"] / sampling_rate * 1000))
        end_ms = int(round(ts["end"] / sampling_rate * 1000))
        segments.append(VADSegment(start_ms=start_ms, end_ms=end_ms))
    
    return segments


# =============================================================================
# VAD 实现: FunASR fsmn-vad
# =============================================================================

def _detect_with_funasr(
    audio_path: Path,
    config: VADConfig
) -> List[VADSegment]:
    """
    使用 FunASR fsmn-vad 检测语音片段
    
    设计参考: pyvideotrans 的 FunASR VAD 流程（独立实现）
    """
    from funasr import AutoModel
    
    # 加载 VAD 模型
    model = AutoModel(
        model="fsmn-vad",
        model_revision="v2.0.4",
        disable_update=True,
    )
    
    # 执行 VAD
    result = model.generate(
        input=str(audio_path),
        batch_size_s=300,
        merge_vad=True,
        merge_length_s=config.max_speech_duration_s,
    )
    
    segments = []
    if result and len(result) > 0 and result[0].get("value"):
        for item in result[0]["value"]:
            # FunASR 返回格式: [[start_ms, end_ms], ...]
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                start_ms = int(item[0])
                end_ms = int(item[1])
                segments.append(VADSegment(start_ms=start_ms, end_ms=end_ms))
    
    return segments


# =============================================================================
# VAD 实现: pydub 静音检测
# =============================================================================

def _detect_with_pydub(
    audio_path: Path,
    config: VADConfig
) -> List[VADSegment]:
    """
    使用 pydub 的静音检测
    
    设计参考: pyvideotrans 的 pydub VAD 方案（独立实现）
    注意: 这种方法精度较低，但依赖最轻
    """
    from pydub import AudioSegment
    from pydub.silence import detect_nonsilent
    
    # 加载音频
    audio = AudioSegment.from_file(str(audio_path))
    
    # 检测非静音片段
    nonsilent_ranges = detect_nonsilent(
        audio,
        min_silence_len=config.min_silence_duration_ms,
        silence_thresh=config.silence_thresh_db,
        seek_step=10  # 每 10ms 检测一次
    )
    
    segments = []
    for start_ms, end_ms in nonsilent_ranges:
        # 过滤过短的片段
        if end_ms - start_ms >= config.min_speech_duration_ms:
            segments.append(VADSegment(start_ms=start_ms, end_ms=end_ms))
    
    return segments


# =============================================================================
# 公共接口
# =============================================================================

def detect_speech_segments(
    audio_path: Path,
    method: VADMethod = "auto",
    config: Optional[VADConfig] = None,
) -> List[VADSegment]:
    """
    检测音频中的语音片段
    
    Args:
        audio_path: 音频文件路径 (建议 16kHz mono WAV)
        method: VAD 方法 ("auto", "silero", "funasr", "pydub")
        config: VAD 配置，None 使用默认值
        
    Returns:
        语音片段列表，每个元素包含 start_ms 和 end_ms
        
    Raises:
        RuntimeError: 没有可用的 VAD 方法
        FileNotFoundError: 音频文件不存在
    """
    audio_path = Path(audio_path)
    
    if not audio_path.exists():
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")
    
    if config is None:
        config = VADConfig()
    
    # 选择方法
    selected_method = _select_best_method(method)
    logger.info(f"使用 VAD 方法: {selected_method}")
    
    # 执行检测
    if selected_method == "silero":
        segments = _detect_with_silero(audio_path, config)
    elif selected_method == "funasr":
        segments = _detect_with_funasr(audio_path, config)
    elif selected_method == "pydub":
        segments = _detect_with_pydub(audio_path, config)
    else:
        raise ValueError(f"未知的 VAD 方法: {selected_method}")
    
    logger.info(f"检测到 {len(segments)} 个语音片段")
    return segments


def cut_audio_by_vad(
    audio_path: Path,
    output_dir: Optional[Path] = None,
    method: VADMethod = "auto",
    config: Optional[VADConfig] = None,
    max_chunk_ms: int = 30000,
) -> List[Tuple[Path, int, int]]:
    """
    按 VAD 结果切分音频文件
    
    Args:
        audio_path: 输入音频文件路径
        output_dir: 输出目录，None 则使用临时目录
        method: VAD 方法
        config: VAD 配置
        max_chunk_ms: 最大片段时长 (毫秒)，超过将强制分割
        
    Returns:
        切分结果列表: [(chunk_path, start_ms, end_ms), ...]
        
    Raises:
        RuntimeError: 没有可用的 VAD 方法
        FileNotFoundError: 音频文件不存在
    """
    from pydub import AudioSegment
    
    audio_path = Path(audio_path)
    
    if not audio_path.exists():
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")
    
    # 创建输出目录
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="vad_chunks_"))
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 检测语音片段
    segments = detect_speech_segments(audio_path, method, config)
    
    if not segments:
        logger.warning("未检测到语音片段")
        return []
    
    # 合并过短的相邻片段，分割过长的片段
    merged_segments = _merge_and_split_segments(segments, max_chunk_ms)
    
    # 加载音频
    audio = AudioSegment.from_file(str(audio_path))
    
    # 切分并保存
    results = []
    for i, seg in enumerate(merged_segments):
        chunk = audio[seg.start_ms:seg.end_ms]
        chunk_path = output_dir / f"{i:04d}_{seg.start_ms}_{seg.end_ms}.wav"
        chunk.export(str(chunk_path), format="wav")
        results.append((chunk_path, seg.start_ms, seg.end_ms))
    
    logger.info(f"已切分为 {len(results)} 个音频片段，保存到: {output_dir}")
    return results


def _merge_and_split_segments(
    segments: List[VADSegment],
    max_chunk_ms: int
) -> List[VADSegment]:
    """
    合并相邻片段并分割过长片段
    
    策略:
    1. 相邻片段间隔小于 1000ms 则合并
    2. 合并后超过 max_chunk_ms 则按 max_chunk_ms 强制分割
    """
    if not segments:
        return []
    
    merge_threshold_ms = 1000  # 合并阈值
    
    merged = []
    current = VADSegment(
        start_ms=segments[0].start_ms,
        end_ms=segments[0].end_ms
    )
    
    for seg in segments[1:]:
        gap = seg.start_ms - current.end_ms
        
        if gap <= merge_threshold_ms:
            # 合并
            current.end_ms = seg.end_ms
        else:
            # 保存当前片段
            merged.append(current)
            current = VADSegment(start_ms=seg.start_ms, end_ms=seg.end_ms)
    
    merged.append(current)
    
    # 分割过长片段
    final = []
    for seg in merged:
        if seg.duration_ms <= max_chunk_ms:
            final.append(seg)
        else:
            # 按 max_chunk_ms 分割
            start = seg.start_ms
            while start < seg.end_ms:
                end = min(start + max_chunk_ms, seg.end_ms)
                final.append(VADSegment(start_ms=start, end_ms=end))
                start = end
    
    return final


def cut_audio_by_duration(
    audio_path: Path,
    output_dir: Optional[Path] = None,
    chunk_duration_ms: int = 30000,
    overlap_ms: int = 0,
) -> List[Tuple[Path, int, int]]:
    """
    按固定时长切分音频 (不使用 VAD)
    
    适用于 VAD 不可用或音频质量不适合 VAD 的场景。
    
    Args:
        audio_path: 输入音频文件路径
        output_dir: 输出目录，None 则使用临时目录
        chunk_duration_ms: 每个片段的时长 (毫秒)
        overlap_ms: 片段之间的重叠时长 (毫秒)
        
    Returns:
        切分结果列表: [(chunk_path, start_ms, end_ms), ...]
    """
    from pydub import AudioSegment
    
    audio_path = Path(audio_path)
    
    if not audio_path.exists():
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")
    
    # 创建输出目录
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="duration_chunks_"))
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载音频
    audio = AudioSegment.from_file(str(audio_path))
    total_duration_ms = len(audio)
    
    # 计算步进
    step_ms = chunk_duration_ms - overlap_ms
    if step_ms <= 0:
        step_ms = chunk_duration_ms
    
    # 切分
    results = []
    start_ms = 0
    chunk_index = 0
    
    while start_ms < total_duration_ms:
        end_ms = min(start_ms + chunk_duration_ms, total_duration_ms)
        
        chunk = audio[start_ms:end_ms]
        chunk_path = output_dir / f"{chunk_index:04d}_{start_ms}_{end_ms}.wav"
        chunk.export(str(chunk_path), format="wav")
        
        results.append((chunk_path, start_ms, end_ms))
        
        start_ms += step_ms
        chunk_index += 1
    
    logger.info(f"已按 {chunk_duration_ms}ms 时长切分为 {len(results)} 个片段")
    return results
