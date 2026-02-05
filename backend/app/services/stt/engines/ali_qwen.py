"""
ali_qwen.py - 阿里通义千问 Qwen-ASR 云端引擎
==============================================

作用: 基于 DashScope API 的云端语音识别引擎。
设计参考: pyvideotrans 的 Qwen-ASR 对接思路（独立实现，无代码复制）
维护: AI + Human

模型说明:
- qwen3-asr-flash: 快速识别模型，适合实时场景
- qwen3-asr-turbo: 高精度模型，适合离线处理

依赖:
- dashscope (pip install dashscope)

API Key 获取:
- 访问 https://dashscope.console.aliyun.com/ 获取 API Key
"""

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

from ..base import BaseSTTEngine
from ..registry import register_engine
from ..dto import (
    STTRequest,
    STTResponse,
    STTSegment,
    EngineMetadata,
    ModelInfo,
    ParameterSpec,
    UsageInfo,
)
from ..exceptions import (
    TranscriptionError,
    ModelNotFoundError,
    APIKeyMissingError,
)
from ..compat import get_cache_dir


logger = logging.getLogger(__name__)


# 支持的模型列表
QWEN_ASR_MODELS = {
    "qwen3-asr-flash": {
        "display_name": "Qwen3 ASR Flash",
        "description": "快速识别模型，低延迟",
        "languages": ["zh", "en", "ja", "ko", "yue", "auto"],
        "size": "云端",
    },
    "qwen3-asr-turbo": {
        "display_name": "Qwen3 ASR Turbo",
        "description": "高精度模型，更准确",
        "languages": ["zh", "en", "ja", "ko", "yue", "auto"],
        "size": "云端",
    },
}

# 默认模型
DEFAULT_MODEL = "qwen3-asr-flash"

# API Key 环境变量名
API_KEY_ENV = "DASHSCOPE_API_KEY"


@register_engine
@dataclass
class QwenASREngine(BaseSTTEngine):
    """
    阿里通义千问 Qwen-ASR 云端语音识别引擎
    
    使用 DashScope API 进行云端识别，需要配置 API Key。
    
    API Key 配置方式 (按优先级):
    1. STTRequest.options["api_key"]
    2. 环境变量 DASHSCOPE_API_KEY
    """
    
    # 引擎标识
    name: str = field(default="ali_qwen", init=False)
    display_name: str = field(default="通义千问 ASR (云端)", init=False)
    engine_type: str = field(default="cloud", init=False)
    
    # 配置
    _api_key: Optional[str] = field(default=None, init=False)
    
    def __post_init__(self):
        """初始化后从环境变量读取 API Key"""
        super().__post_init__()
        self._api_key = os.environ.get(API_KEY_ENV)
    
    @classmethod
    def get_metadata(cls) -> EngineMetadata:
        """返回引擎元数据"""
        models = []
        for name, info in QWEN_ASR_MODELS.items():
            models.append(ModelInfo(
                name=name,
                display_name=info["display_name"],
                description=info["description"],
                languages=info["languages"],
                size=info["size"],
                default=(name == DEFAULT_MODEL),
                features=["cloud", "auto_language"],
            ))
        
        return EngineMetadata(
            name="ali_qwen",
            display_name="通义千问 ASR (云端)",
            type="cloud",
            description="基于阿里云 DashScope API 的云端语音识别",
            version="1.0.0",
            supported_languages=["zh", "en", "ja", "ko", "yue", "auto"],
            requires_api_key=True,
            models=models,
            parameters=[
                ParameterSpec(
                    name="api_key",
                    type="string",
                    required=False,
                    description=f"DashScope API Key (或设置环境变量 {API_KEY_ENV})",
                ),
                ParameterSpec(
                    name="enable_lid",
                    type="boolean",
                    required=False,
                    default=True,
                    description="是否启用语种自动识别",
                ),
                ParameterSpec(
                    name="enable_itn",
                    type="boolean",
                    required=False,
                    default=False,
                    description="是否启用逆文本正则化",
                ),
            ],
        )
    
    def transcribe(self, request: STTRequest) -> STTResponse:
        """
        执行语音识别
        
        Args:
            request: 识别请求
            
        Returns:
            STTResponse: 识别结果 (包含 usage 统计)
        """
        start_time = time.time()
        
        # 检查可用性
        available, reason = self.check_available()
        if not available:
            raise TranscriptionError(f"引擎不可用: {reason}", engine_name=self.name)
        
        # 获取 API Key
        api_key = request.options.get("api_key") or self._api_key
        if not api_key:
            raise APIKeyMissingError(self.name, API_KEY_ENV)
        
        # 确定模型
        model_name = request.model or DEFAULT_MODEL
        if model_name not in QWEN_ASR_MODELS:
            raise ModelNotFoundError(model_name, engine_name=self.name)
        
        # 确定语言
        language = request.language
        if language == "auto":
            language = "zh"  # 默认中文，但启用 LID
        
        # 获取选项
        enable_lid = request.options.get("enable_lid", True)
        enable_itn = request.options.get("enable_itn", False)
        
        # 使用 VAD 切分音频后识别
        try:
            segments, usage_stats = self._transcribe_with_vad(
                audio_path=request.audio_path,
                api_key=api_key,
                model=model_name,
                language=language,
                enable_lid=enable_lid,
                enable_itn=enable_itn,
                progress_callback=request.progress_callback,
            )
        except Exception as e:
            logger.exception(f"识别失败: {e}")
            raise TranscriptionError(str(e), engine_name=self.name)
        
        # 计算处理耗时
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # 构建响应
        full_text = " ".join(seg.text for seg in segments)
        duration_ms = max(seg.end_ms for seg in segments) if segments else 0
        
        # 构建 usage 统计
        usage = UsageInfo(
            audio_duration_ms=duration_ms,
            processing_time_ms=processing_time_ms,
            api_calls=usage_stats.get("api_calls", 0),
            input_tokens=usage_stats.get("input_tokens", 0),
            output_tokens=usage_stats.get("output_tokens", 0),
            characters=len(full_text.replace(" ", "")),
        )
        
        return STTResponse(
            text=full_text,
            segments=segments,
            duration_ms=duration_ms,
            engine=self.name,
            model=model_name,
            language_detected=language,
            usage=usage,
        )
    
    def _transcribe_with_vad(
        self,
        audio_path: Path,
        api_key: str,
        model: str,
        language: str,
        enable_lid: bool,
        enable_itn: bool,
        progress_callback: Optional[callable] = None,
    ) -> Tuple[List[STTSegment], Dict[str, int]]:
        """
        使用 VAD 切分音频后逐段发送到云端识别
        
        VAD 切分可以减少单次 API 调用的音频长度，提高稳定性。
        
        Returns:
            Tuple[List[STTSegment], Dict[str, int]]: (识别片段列表, usage统计)
        """
        import dashscope
        
        # 先将视频/音频转换为 16kHz WAV (压缩文件大小)
        from ..audio_utils import convert_to_16k_wav
        
        cache_dir = get_cache_dir() / "temp"
        cache_dir.mkdir(parents=True, exist_ok=True)
        wav_path = cache_dir / f"qwen_input_{audio_path.stem}.wav"
        
        logger.info(f"转换音频: {audio_path} -> {wav_path}")
        convert_to_16k_wav(audio_path, wav_path)
        logger.info(f"转换完成，WAV 大小: {wav_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        # 使用转换后的 WAV 文件进行 VAD 切分
        raw_segments = self._cut_audio_with_vad(wav_path)
        total_segments = len(raw_segments)
        
        # 报告 VAD 切分完成
        if progress_callback:
            try:
                progress_callback(0, total_segments, f"VAD 切分完成，共 {total_segments} 段")
            except Exception:
                pass
        
        logger.info(f"VAD 切分完成，共 {total_segments} 段待识别")
        
        segments = []
        errors = []
        ok_count = 0
        
        # Usage 统计
        total_input_tokens = 0
        total_output_tokens = 0
        api_calls = 0
        
        for i, raw_seg in enumerate(raw_segments):
            file_path = raw_seg.get("file", str(audio_path))
            start_ms = raw_seg.get("start_time", 0)
            end_ms = raw_seg.get("end_time", 0)
            
            # 报告当前进度
            if progress_callback:
                try:
                    progress_callback(i, total_segments, f"识别第 {i + 1}/{total_segments} 段")
                except Exception:
                    pass
            
            try:
                api_calls += 1
                response = dashscope.MultiModalConversation.call(
                    api_key=api_key,
                    model=model,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"audio": file_path},
                        ]
                    }],
                    result_format="message",
                    asr_options={
                        "language": language[:2].lower(),
                        "enable_lid": enable_lid,
                        "enable_itn": enable_itn,
                    }
                )
                
                # 检查响应
                if not hasattr(response, 'output') or not hasattr(response.output, 'choices'):
                    error_msg = f"{getattr(response, 'code', 'unknown')}:{getattr(response, 'message', 'unknown error')}"
                    errors.append(error_msg)
                    logger.warning(f"片段 {i+1} 识别失败: {error_msg}")
                    continue
                
                # 提取 usage 信息 (DashScope 返回 input_tokens / output_tokens)
                if hasattr(response, 'usage') and response.usage:
                    total_input_tokens += getattr(response.usage, 'input_tokens', 0) or 0
                    total_output_tokens += getattr(response.usage, 'output_tokens', 0) or 0
                
                # 提取文本
                text_parts = []
                for content in response.output.choices[0]['message']['content']:
                    if 'text' in content:
                        text_parts.append(content['text'])
                
                text = ''.join(text_parts).strip()
                
                if text:
                    segments.append(STTSegment(
                        start_ms=start_ms,
                        end_ms=end_ms,
                        text=text,
                    ))
                    ok_count += 1
                
            except Exception as e:
                logger.warning(f"片段 {i+1} 处理异常: {e}")
                errors.append(str(e))
        
        # 报告识别完成
        if progress_callback:
            try:
                progress_callback(total_segments, total_segments, f"识别完成，成功 {ok_count}/{total_segments} 段")
            except Exception:
                pass
        
        # 如果全部失败则抛出异常
        if ok_count == 0 and errors:
            raise TranscriptionError("; ".join(errors[:3]), engine_name=self.name)
        
        # 清理临时文件
        self._cleanup_temp_files(raw_segments)
        
        # 清理转换后的 WAV 文件
        if wav_path.exists():
            try:
                wav_path.unlink()
            except Exception:
                pass
        
        # 构建 usage 统计
        usage_stats = {
            "api_calls": api_calls,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
        }
        
        return segments, usage_stats
    
    def _cut_audio_with_vad(self, audio_path: Path) -> List[Dict]:
        """
        使用 VAD 切分音频 (云端 API 专用，不下载任何本地模型)
        
        云端 API 的 VAD 策略 (按优先级):
        1. silero-vad (faster_whisper 内置，无需下载)
        2. pydub 静音检测 (轻量级)
        3. 按时长切分 (最后回退)
        
        注意: 不使用 funasr VAD，因为它会下载模型文件
        """
        # 尝试使用 silero-vad
        try:
            return self._cut_audio_with_silero(audio_path)
        except ImportError:
            logger.info("faster_whisper 未安装，尝试 pydub")
        except Exception as e:
            logger.warning(f"silero VAD 失败: {e}，尝试 pydub")
        
        # 尝试使用 pydub 静音检测
        try:
            return self._cut_audio_with_pydub(audio_path)
        except ImportError:
            logger.info("pydub 未安装，使用时长切分")
        except Exception as e:
            logger.warning(f"pydub 切分失败: {e}，使用时长切分")
        
        # 最后回退：按时长切分
        return self._cut_audio_by_duration(audio_path, chunk_duration_ms=10000)
    
    def _cut_audio_with_silero(self, audio_path: Path) -> List[Dict]:
        """
        使用 silero-vad 切分音频
        
        silero-vad 是 faster_whisper 内置的，不需要额外下载模型文件
        """
        from faster_whisper.audio import decode_audio
        from faster_whisper.vad import VadOptions, get_speech_timestamps
        from pydub import AudioSegment
        
        sampling_rate = 16000
        
        # VAD 参数
        vad_options = VadOptions(
            threshold=0.45,
            min_speech_duration_ms=0,
            max_speech_duration_s=10.0,  # 云端 API 建议每段不超过 10 秒
            min_silence_duration_ms=500,
            speech_pad_ms=0,
        )
        
        # 解码音频并检测语音段
        audio_data = decode_audio(str(audio_path), sampling_rate=sampling_rate)
        speech_chunks = get_speech_timestamps(audio_data, vad_options=vad_options)
        
        # 转换为毫秒
        speech_chunks_ms = [
            {
                "start": int(round(ts["start"] / sampling_rate * 1000)),
                "end": int(round(ts["end"] / sampling_rate * 1000)),
            }
            for ts in speech_chunks
        ]
        
        if not speech_chunks_ms:
            logger.warning("VAD 未检测到语音，使用整个音频")
            return self._cut_audio_by_duration(audio_path, chunk_duration_ms=10000)
        
        # 切分并保存音频片段
        cache_dir = get_cache_dir() / "temp"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        audio = AudioSegment.from_file(str(audio_path))
        data = []
        
        for i, chunk in enumerate(speech_chunks_ms):
            start_ms, end_ms = chunk["start"], chunk["end"]
            audio_chunk = audio[start_ms:end_ms]
            file_name = cache_dir / f"qwen_vad_{start_ms}_{end_ms}.wav"
            audio_chunk.export(str(file_name), format="wav")
            data.append({
                "line": i + 1,
                "text": "",
                "start_time": start_ms,
                "end_time": end_ms,
                "file": str(file_name),
            })
        
        logger.info(f"silero VAD 切分完成: {len(data)} 段")
        return data
    
    def _cut_audio_with_pydub(self, audio_path: Path) -> List[Dict]:
        """
        使用 pydub 静音检测切分音频 (轻量级替代方案)
        """
        from pydub import AudioSegment
        from pydub.silence import detect_nonsilent
        
        audio = AudioSegment.from_file(str(audio_path))
        
        # 检测非静音段
        nonsilent_ranges = detect_nonsilent(
            audio,
            min_silence_len=500,  # 500ms 静音判定
            silence_thresh=audio.dBFS - 16,  # 相对于平均音量
        )
        
        if not nonsilent_ranges:
            logger.warning("pydub 未检测到语音，使用时长切分")
            return self._cut_audio_by_duration(audio_path, chunk_duration_ms=10000)
        
        # 合并过短的片段，限制最长 10 秒
        merged_ranges = self._merge_audio_ranges(nonsilent_ranges, max_duration_ms=10000)
        
        cache_dir = get_cache_dir() / "temp"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        data = []
        for i, (start_ms, end_ms) in enumerate(merged_ranges):
            audio_chunk = audio[start_ms:end_ms]
            file_name = cache_dir / f"qwen_pydub_{start_ms}_{end_ms}.wav"
            audio_chunk.export(str(file_name), format="wav")
            data.append({
                "line": i + 1,
                "text": "",
                "start_time": start_ms,
                "end_time": end_ms,
                "file": str(file_name),
            })
        
        logger.info(f"pydub 静音检测切分完成: {len(data)} 段")
        return data
    
    def _merge_audio_ranges(
        self,
        ranges: List[Tuple[int, int]],
        max_duration_ms: int = 10000,
        min_gap_ms: int = 300,
    ) -> List[Tuple[int, int]]:
        """合并音频范围，确保每段不超过最大时长"""
        if not ranges:
            return []
        
        merged = []
        current_start, current_end = ranges[0]
        
        for start, end in ranges[1:]:
            gap = start - current_end
            duration = end - current_start
            
            # 如果间隔小且合并后不超时长，则合并
            if gap < min_gap_ms and duration <= max_duration_ms:
                current_end = end
            else:
                merged.append((current_start, current_end))
                current_start, current_end = start, end
        
        merged.append((current_start, current_end))
        
        # 如果有超长片段，进一步切分
        result = []
        for start, end in merged:
            duration = end - start
            if duration <= max_duration_ms:
                result.append((start, end))
            else:
                # 按最大时长切分
                pos = start
                while pos < end:
                    chunk_end = min(pos + max_duration_ms, end)
                    result.append((pos, chunk_end))
                    pos = chunk_end
        
        return result
    
    def _cut_audio_by_duration(self, audio_path: Path, chunk_duration_ms: int = 30000) -> List[Dict]:
        """
        按固定时长切分音频 (作为 VAD 不可用时的回退方案)
        
        Args:
            audio_path: 音频文件路径
            chunk_duration_ms: 每段时长 (毫秒)，默认 30 秒
        """
        try:
            from pydub import AudioSegment
            
            audio_data = AudioSegment.from_file(str(audio_path))
            total_duration = len(audio_data)
            
            cache_dir = get_cache_dir() / "temp"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            raw_segments = []
            start_ms = 0
            
            while start_ms < total_duration:
                end_ms = min(start_ms + chunk_duration_ms, total_duration)
                chunk = audio_data[start_ms:end_ms]
                chunk_path = cache_dir / f"qwen_chunk_{start_ms}_{end_ms}.wav"
                chunk.export(str(chunk_path), format="wav")
                
                raw_segments.append({
                    "file": str(chunk_path),
                    "start_time": start_ms,
                    "end_time": end_ms,
                })
                
                start_ms = end_ms
            
            logger.info(f"按时长切分完成: {len(raw_segments)} 段, 每段 {chunk_duration_ms/1000:.0f} 秒")
            return raw_segments
            
        except ImportError:
            logger.error("pydub 未安装，无法切分音频")
            # 最后的回退：整段音频
            return [{
                "file": str(audio_path),
                "start_time": 0,
                "end_time": self._get_duration_ms(audio_path),
            }]
    
    def _get_duration_ms(self, audio_path: Path) -> int:
        """获取音频时长 (毫秒)"""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(audio_path))
            return len(audio)
        except Exception:
            return 0
    
    def _cleanup_temp_files(self, raw_segments: List[Dict]) -> None:
        """清理临时音频文件"""
        cache_dir = get_cache_dir() / "temp"
        for seg in raw_segments:
            file_path = Path(seg.get("file", ""))
            if file_path.parent == cache_dir and file_path.exists():
                try:
                    file_path.unlink()
                except Exception:
                    pass
    
    def get_models(self) -> List[str]:
        """获取支持的模型列表"""
        return list(QWEN_ASR_MODELS.keys())
    
    def check_available(self) -> Tuple[bool, str]:
        """
        检查引擎是否可用
        
        Returns:
            Tuple[bool, str]: (是否可用, 原因)
        """
        # 检查 dashscope 是否安装
        try:
            import dashscope
            version = getattr(dashscope, '__version__', 'unknown')
            return True, f"dashscope {version} 已安装"
        except ImportError:
            return False, "dashscope 未安装，请运行: pip install dashscope"
    
    def set_api_key(self, api_key: str) -> None:
        """
        设置 API Key
        
        Args:
            api_key: DashScope API Key
        """
        self._api_key = api_key
    
    def cleanup(self) -> None:
        """释放资源"""
        super().cleanup()
        # 清理临时目录
        cache_dir = get_cache_dir() / "temp"
        if cache_dir.exists():
            for f in cache_dir.glob("qwen_chunk_*.wav"):
                try:
                    f.unlink()
                except Exception:
                    pass
