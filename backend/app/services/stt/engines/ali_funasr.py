"""
ali_funasr.py - 阿里 FunASR 本地引擎
=====================================

作用: 基于 FunASR 的本地语音识别引擎，支持 SenseVoiceSmall 和 paraformer 模型。
设计参考: pyvideotrans 的 FunASR 对接思路（独立实现，无代码复制）
维护: AI + Human

模型说明:
- SenseVoiceSmall: 多语言模型，支持 zh/en/ja/ko/yue 等 (仅 ModelScope)
- paraformer-zh: 中文专用，支持说话人分离 (HuggingFace/ModelScope)

依赖:
- funasr (pip install funasr)
- torch (可选，用于 GPU 加速)

模型源选择:
- 海外用户: 设置环境变量 FUNASR_HUB=hf (使用 HuggingFace)
- 国内用户: 设置环境变量 FUNASR_HUB=ms (使用 ModelScope，默认)
"""

import gc
import logging
import os
import re
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
    ModelDownloadError,
)
from ..compat import get_models_dir, to_ffmpeg_path, setup_environment, setup_model_hub

# 设置环境变量
setup_environment()

# 获取用户选择的 hub (可通过 FUNASR_HUB 环境变量设置)
MODEL_HUB = setup_model_hub(os.environ.get("FUNASR_HUB", "auto"))

logger = logging.getLogger(__name__)


# 支持的模型列表
# hub_support: 模型在哪些 hub 上可用
FUNASR_MODELS = {
    "paraformer-zh": {
        "model_id": "paraformer-zh",  # 标准化名称，FunASR 内部会映射
        "display_name": "Paraformer (中文)",
        "description": "中文专用模型，支持说话人分离。HuggingFace/ModelScope 均可用。",
        "languages": ["zh"],
        "size": "~1.2GB",
        "use_vad": False,  # 内置 VAD
        "hub_support": ["hf", "ms"],  # 两个源都支持
    },
    "SenseVoiceSmall": {
        "model_id": "iic/SenseVoiceSmall",
        "display_name": "SenseVoice Small (多语言)",
        "description": "轻量级多语言模型，支持中英日韩粤语。仅 ModelScope 可用。",
        "languages": ["zh", "en", "ja", "ko", "yue"],
        "size": "~900MB",
        "use_vad": True,  # 需要单独的 VAD 模型
        "hub_support": ["ms"],  # 仅 ModelScope
    },
}

# 默认模型 (根据 hub 选择)
def get_default_model_for_hub(hub: str) -> str:
    """根据 hub 选择默认模型"""
    if hub == "hf":
        return "paraformer-zh"  # HuggingFace 上 SenseVoice 不可用
    return "SenseVoiceSmall"  # ModelScope 上两个都有

DEFAULT_MODEL = get_default_model_for_hub(MODEL_HUB)


def _remove_unwanted_characters(text: str) -> str:
    """
    移除不需要的特殊字符
    
    保留：中文、日文、韩文、英文、数字和常见符号
    """
    allowed_characters = re.compile(
        r'[^\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af'
        r'a-zA-Z0-9\s.,!@#$%^&*()_+\-=\[\]{};\'"\\|<>/?，。！｛｝【】；''""《》、（）￥]+'
    )
    return re.sub(allowed_characters, '', text)


@register_engine
@dataclass
class FunASREngine(BaseSTTEngine):
    """
    阿里 FunASR 本地语音识别引擎
    
    支持两种主要模型：
    - SenseVoiceSmall: 轻量级多语言模型
    - paraformer-zh: 中文专用，支持说话人分离
    """
    
    # 引擎标识
    name: str = field(default="ali_funasr", init=False)
    display_name: str = field(default="FunASR", init=False)
    engine_type: str = field(default="local", init=False)
    vendor: str = field(default="Alibaba", init=False)
    
    # 内部状态
    _vad_model: Any = field(default=None, init=False, repr=False)
    _current_model_name: str = field(default="", init=False)
    
    @classmethod
    def get_metadata(cls) -> EngineMetadata:
        """返回引擎元数据"""
        models = []
        for name, info in FUNASR_MODELS.items():
            models.append(ModelInfo(
                name=name,
                display_name=info["display_name"],
                description=info["description"],
                languages=info["languages"],
                size=info["size"],
                default=(name == DEFAULT_MODEL),
                features=["timestamps", "vad"] if info["use_vad"] else ["timestamps", "vad", "speaker_diarization"],
            ))
        
        return EngineMetadata(
            name="ali_funasr",
            display_name="FunASR",
            vendor="Alibaba",
            type="local",
            description="基于 FunASR 的本地语音识别，支持中英日韩粤语",
            version="1.0.0",
            supported_languages=["zh", "en", "ja", "ko", "yue", "auto"],
            requires_api_key=False,
            models=models,
            parameters=[
                ParameterSpec(
                    name="use_itn",
                    type="boolean",
                    required=False,
                    default=True,
                    description="是否使用逆文本正则化 (数字转汉字等)",
                ),
                ParameterSpec(
                    name="max_speakers",
                    type="integer",
                    required=False,
                    default=-1,
                    description="最大说话人数 (-1 表示禁用分离)",
                    options=[-1, 2, 3, 4, 5],
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
        
        # 确定模型
        model_name = request.model or DEFAULT_MODEL
        if model_name not in FUNASR_MODELS:
            raise ModelNotFoundError(model_name, engine_name=self.name)
        
        model_info = FUNASR_MODELS[model_name]
        
        # 确定语言
        language = request.language
        if language == "auto":
            language = "zh"  # FunASR 默认中文
        
        # 获取选项
        use_itn = request.options.get("use_itn", True)
        max_speakers = request.options.get("max_speakers", -1)
        
        # 获取进度回调
        progress_callback = request.progress_callback
        
        # 根据模型选择识别方法
        try:
            if model_name == "SenseVoiceSmall":
                segments = self._transcribe_sensevoice(
                    audio_path=request.audio_path,
                    language=language,
                    use_itn=use_itn,
                    progress_callback=progress_callback,
                )
            else:  # paraformer-zh
                segments = self._transcribe_paraformer(
                    audio_path=request.audio_path,
                    max_speakers=max_speakers,
                    progress_callback=progress_callback,
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
            api_calls=0,  # 本地引擎无 API 调用
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
    
    def _transcribe_sensevoice(
        self,
        audio_path: Path,
        language: str,
        use_itn: bool,
        progress_callback: Optional[callable] = None,
    ) -> List[STTSegment]:
        """
        使用 SenseVoiceSmall 模型识别
        
        采用 VAD 分段 + 逐段识别的方式
        """
        from funasr import AutoModel
        from funasr.utils.postprocess_utils import rich_transcription_postprocess
        
        # 使用 ModelSourceConfig 获取模型路径
        from ..config import ModelSourceConfig
        model_config = ModelSourceConfig.from_env()
        
        # 获取各模型路径 (会自动尝试本地 -> 内网下载 -> 返回 None)
        sensevoice_path = model_config.get_model_path("SenseVoiceSmall")
        vad_path = model_config.get_model_path("fsmn-vad")
        
        # 注意: SenseVoiceSmall 自带标点能力，不需要额外的 punc_model
        # ct-punc 模型在新版 funasr 中有兼容性问题 (CTTransformer not registered)
        
        # 如果获取到本地路径，使用绝对路径；否则用 modelscope ID
        if sensevoice_path:
            # 本地模式：使用绝对路径
            logger.info(f"使用本地模型: {sensevoice_path}")
            model = AutoModel(
                model=str(sensevoice_path),
                device=self.device,
                disable_update=True,
                disable_progress_bar=True,
                disable_log=True,
                trust_remote_code=True,
            )
        else:
            # 在线模式：从 ModelScope 下载
            logger.info("本地模型不存在，从 ModelScope 下载...")
            model = AutoModel(
                model="iic/SenseVoiceSmall",
                device=self.device,
                disable_update=True,
                disable_progress_bar=True,
                disable_log=True,
                trust_remote_code=True,
                hub='ms',
        )
        
        # 加载 VAD 模型
        logger.info("加载 VAD 模型...")
        if vad_path:
            vad_model = AutoModel(
                model=str(vad_path),
                max_single_segment_time=5000,  # 5秒
                max_end_silence_time=500,  # 500ms
                disable_update=True,
                disable_progress_bar=True,
                disable_log=True,
                device=self.device,
            )
        else:
            vad_model = AutoModel(
                model="fsmn-vad",
                max_single_segment_time=5000,  # 5秒
                max_end_silence_time=500,  # 500ms
                hub='ms',
                disable_update=True,
                disable_progress_bar=True,
                disable_log=True,
                device=self.device,
            )
        
        # VAD 分段
        logger.info("执行 VAD 分段...")
        vad_result = vad_model.generate(input=str(audio_path))
        
        # 加载音频用于分割
        from pydub import AudioSegment as PydubSegment
        audio_data = PydubSegment.from_file(str(audio_path))
        
        # 逐段识别
        segments = []
        is_cjk = language[:2] in ['zh', 'ja', 'ko', 'yu', 'yue']
        
        vad_segments = vad_result[0].get('value', []) if vad_result else []
        total = len(vad_segments)
        
        # 报告 VAD 切分完成
        if progress_callback:
            try:
                progress_callback(0, total, f"VAD 切分完成，共 {total} 段")
            except Exception:
                pass
        
        logger.info(f"VAD 切分完成，共 {total} 段待识别")
        
        for i, (start_ms, end_ms) in enumerate(vad_segments):
            logger.debug(f"识别片段 [{i+1}/{total}]: {start_ms}ms - {end_ms}ms")
            
            # 报告当前进度
            if progress_callback:
                try:
                    progress_callback(i, total, f"识别第 {i + 1}/{total} 段")
                except Exception:
                    pass
            
            # 切割音频片段
            chunk = audio_data[start_ms:end_ms]
            chunk_path = audio_path.parent / f"_chunk_{start_ms}_{end_ms}.wav"
            chunk.export(str(chunk_path), format="wav")
            
            try:
                # 识别
                res = model.generate(
                    input=str(chunk_path),
                    language=language[:2],
                    use_itn=use_itn,
                    batch_size=1,
                    disable_pbar=True,
                )
                
                # 后处理
                text = res[0].get("text", "") if res else ""
                text = _remove_unwanted_characters(rich_transcription_postprocess(text))
                
                # CJK 语言去空格
                if is_cjk:
                    text = text.replace(' ', '')
                
                if text.strip():
                    segments.append(STTSegment(
                        start_ms=start_ms,
                        end_ms=end_ms,
                        text=text.strip(),
                    ))
            finally:
                # 清理临时文件
                if chunk_path.exists():
                    chunk_path.unlink()
        
        # 报告识别完成
        if progress_callback:
            try:
                progress_callback(total, total, f"识别完成，共 {len(segments)} 段")
            except Exception:
                pass
        
        # 清理模型
        self._cleanup_models(model, vad_model)
        
        return segments
    
    def _transcribe_paraformer(
        self,
        audio_path: Path,
        max_speakers: int,
        progress_callback: Optional[callable] = None,
    ) -> List[STTSegment]:
        """
        使用 Paraformer 模型识别 (中文专用)
        
        内置 VAD，支持说话人分离
        
        注意: Paraformer 内部处理 VAD，无法报告逐段进度，
        只能报告大致阶段 (加载模型 → 识别中 → 完成)
        """
        from funasr import AutoModel
        
        # 使用 ModelSourceConfig 获取模型路径
        from ..config import ModelSourceConfig
        model_config = ModelSourceConfig.from_env()
        
        # 获取各模型路径
        paraformer_path = model_config.get_model_path("paraformer-zh")
        vad_path = model_config.get_model_path("fsmn-vad")
        punc_path = model_config.get_model_path("ct-punc")
        cam_path = model_config.get_model_path("cam++") if max_speakers > -1 else None
        
        # 判断是否本地模式
        is_local = paraformer_path and vad_path and punc_path
        
        if is_local:
            logger.info(f"使用本地模型: {paraformer_path}")
            model = AutoModel(
                model=str(paraformer_path),
                vad_model=str(vad_path),
                punc_model=str(punc_path),
                spk_model=str(cam_path) if cam_path else None,
                disable_update=True,
                disable_progress_bar=True,
                disable_log=True,
                device=self.device,
            )
        else:
            logger.info("本地模型不存在，从 ModelScope 下载...")
            model = AutoModel(
                model="paraformer-zh",
                vad_model="fsmn-vad",
                punc_model="ct-punc",
                hub='ms',
                spk_model="cam++" if max_speakers > -1 else None,
                disable_update=True,
                disable_progress_bar=True,
                disable_log=True,
                device=self.device,
            )
        
        # 报告开始识别
        if progress_callback:
            try:
                progress_callback(0, 1, "模型加载完成，开始识别...")
            except Exception:
                pass
        
        logger.info("开始识别...")
        res = model.generate(
            input=str(audio_path),
            return_raw_text=True,
            is_final=True,
            batch_size=16,
            sentence_timestamp=True,
            disable_pbar=True,
        )
        
        # 解析结果
        segments = []
        sentence_info = res[0].get('sentence_info', []) if res else []
        
        for item in sentence_info:
            text = item.get('text', '').strip()
            if not text:
                continue
            
            segments.append(STTSegment(
                start_ms=item['start'],
                end_ms=item['end'],
                text=text,
            ))
        
        # 报告识别完成
        if progress_callback:
            try:
                progress_callback(1, 1, f"识别完成，共 {len(segments)} 段")
            except Exception:
                pass
        
        # 清理模型
        self._cleanup_models(model)
        
        return segments
    
    def _cleanup_models(self, *models) -> None:
        """清理模型释放内存"""
        try:
            import torch
            for model in models:
                if model is not None:
                    del model
            
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            gc.collect()
        except Exception as e:
            logger.warning(f"清理模型时出错: {e}")
    
    def get_models(self) -> List[str]:
        """获取支持的模型列表"""
        return list(FUNASR_MODELS.keys())
    
    def check_available(self) -> Tuple[bool, str]:
        """
        检查引擎是否可用
        
        Returns:
            Tuple[bool, str]: (是否可用, 原因)
        """
        # 检查 funasr 是否安装
        try:
            import funasr
            return True, f"funasr {funasr.__version__} 已安装"
        except ImportError:
            return False, "funasr 未安装，请运行: pip install funasr"
    
    def cleanup(self) -> None:
        """释放所有资源"""
        super().cleanup()
        self._cleanup_models(self._model, self._vad_model)
        self._model = None
        self._vad_model = None
        self._current_model_name = ""
