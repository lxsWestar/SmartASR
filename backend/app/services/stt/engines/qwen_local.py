"""
Qwen3-ASR 本地引擎
=================

基于 Qwen3-ASR 开源模型（Alibaba Qwen 团队）的本地推理引擎。

支持模型:
  - Qwen3-ASR-0.6B  轻量级，速度优先
  - Qwen3-ASR-1.7B  平衡精度与速度

依赖:
  pip install qwen-asr torch

模型下载（推荐 git clone，稳定快速）:
  # HuggingFace
  git clone https://huggingface.co/Qwen/Qwen3-ASR-0.6B ./models/Qwen3-ASR-0.6B
  git clone https://huggingface.co/Qwen/Qwen3-ASR-1.7B ./models/Qwen3-ASR-1.7B

  # 或 ModelScope（国内推荐）
  git clone https://modelscope.cn/Qwen/Qwen3-ASR-0.6B.git ./models/Qwen3-ASR-0.6B

模型目录结构 (STT_MODELS_DIR, 默认 ./models):
  models/
    Qwen3-ASR-0.6B/   ← git clone 目标
    Qwen3-ASR-1.7B/

模型来源: https://github.com/QwenLM/Qwen3-ASR
官方包:   pip install qwen-asr
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Tuple

from ..base import BaseSTTEngine
from ..registry import register_engine
from ..dto import (
    EngineMetadata,
    ModelInfo,
    ParameterSpec,
    STTRequest,
    STTResponse,
    STTSegment,
)
from ..exceptions import ModelNotFoundError, TranscriptionError

logger = logging.getLogger(__name__)

# ── モデル定義 ──────────────────────────────────────────────────────────────

QWEN_LOCAL_MODELS: dict[str, dict] = {
    "Qwen3-ASR-0.6B": {
        "hf_id": "Qwen/Qwen3-ASR-0.6B",
        "display_name": "Qwen3-ASR 0.6B",
        "description": "轻量级模型（0.6B参数），速度优先，适合实时场景",
        "size": "~1.2GB",
        "languages": ["zh", "en", "ja", "ko", "auto"],
        "default": True,
        "features": ["multi_language"],
    },
    "Qwen3-ASR-1.7B": {
        "hf_id": "Qwen/Qwen3-ASR-1.7B",
        "display_name": "Qwen3-ASR 1.7B",
        "description": "标准模型（1.7B参数），精度与速度平衡",
        "size": "~3.4GB",
        "languages": ["zh", "en", "ja", "ko", "auto"],
        "default": False,
        "features": ["multi_language"],
    },
}

DEFAULT_MODEL = "Qwen3-ASR-0.6B"

# 本地模型根目录（可通过环境变量覆盖）
_MODELS_DIR = Path(os.environ.get("STT_MODELS_DIR", "./models"))

# ISO 639-1 语言代码 → qwen-asr 语言名称映射
_LANG_CODE_TO_QWEN: dict[str, str] = {
    "zh": "Chinese",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "yue": "Cantonese",
    "ar": "Arabic",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "pt": "Portuguese",
    "ru": "Russian",
    "th": "Thai",
    "vi": "Vietnamese",
    "tr": "Turkish",
    "hi": "Hindi",
    "it": "Italian",
}


def _to_qwen_language(lang: Optional[str]) -> Optional[str]:
    """将 ISO 语言代码转换为 qwen-asr 接受的全称（auto/None → None 表示自动检测）"""
    if not lang or lang == "auto":
        return None
    return _LANG_CODE_TO_QWEN.get(lang, lang)


# ── エンジン実装 ────────────────────────────────────────────────────────────

@register_engine
@dataclass
class QwenLocalEngine(BaseSTTEngine):
    """
    Qwen3-ASR 本地推理引擎

    使用官方 qwen-asr 包（pip install qwen-asr）加载 Qwen3-ASR-0.6B / 1.7B。
    模型通过 git clone HuggingFace / ModelScope 仓库下载到本地。
    """

    # 引擎标识
    name: str = field(default="qwen_local", init=False)
    display_name: str = field(default="Qwen3-ASR", init=False)
    engine_type: str = field(default="local", init=False)
    vendor: str = field(default="Alibaba", init=False)

    # 运行时状态（懒加载缓存）
    _model: Any = field(default=None, init=False, repr=False)
    _current_model_key: str = field(default="", init=False)

    @classmethod
    def get_metadata(cls) -> EngineMetadata:
        """返回引擎元数据"""
        models = [
            ModelInfo(
                name=key,
                display_name=info["display_name"],
                description=info["description"],
                languages=info["languages"],
                size=info["size"],
                default=info["default"],
                features=info["features"],
            )
            for key, info in QWEN_LOCAL_MODELS.items()
        ]

        return EngineMetadata(
            name="qwen_local",
            display_name="Qwen3-ASR",
            vendor="Alibaba",
            type="local",
            description="Qwen3-ASR 开源本地模型，支持 0.6B / 1.7B 两种规格，52 种语言",
            version="3.0.0",
            supported_languages=list(_LANG_CODE_TO_QWEN.keys()) + ["auto"],
            requires_api_key=False,
            models=models,
            parameters=[
                ParameterSpec(
                    name="language",
                    type="string",
                    required=False,
                    default="auto",
                    options=["auto", "zh", "en", "ja", "ko"],
                    description="识别语言（auto 表示自动检测）",
                ),
                ParameterSpec(
                    name="max_new_tokens",
                    type="integer",
                    required=False,
                    default=256,
                    description="最大生成 token 数量，长音频可适当调大",
                ),
            ],
        )

    def check_available(self) -> Tuple[bool, str]:
        """检查引擎依赖是否满足"""
        try:
            import qwen_asr  # noqa: F401
        except ImportError:
            return False, "缺少依赖 qwen-asr。请运行: pip install qwen-asr"

        try:
            import torch  # noqa: F401
        except ImportError:
            return False, "缺少依赖 torch。请运行: pip install torch"

        return True, "依赖已满足"

    def get_models(self) -> List[str]:
        """返回支持的模型列表"""
        return list(QWEN_LOCAL_MODELS.keys())

    def _resolve_model_path(self, model_key: str) -> str:
        """
        解析模型路径。
        优先使用本地 git clone 目录，否则回退到 HuggingFace Hub ID（需联网）。
        """
        if model_key not in QWEN_LOCAL_MODELS:
            raise ModelNotFoundError(
                f"未知模型: {model_key}，支持: {list(QWEN_LOCAL_MODELS.keys())}",
                engine_name=self.name,
                model_name=model_key,
            )
        hf_id = QWEN_LOCAL_MODELS[model_key]["hf_id"]
        # 尝试 models/Qwen3-ASR-0.6B 目录（git clone 结果）
        local_dir = _MODELS_DIR / model_key
        if local_dir.exists():
            logger.info("使用本地模型目录: %s", local_dir)
            return str(local_dir)
        # 也兼容 models/Qwen--Qwen3-ASR-0.6B 格式（部分工具的下载习惯）
        alt_dir = _MODELS_DIR / hf_id.replace("/", "--")
        if alt_dir.exists():
            logger.info("使用本地模型目录: %s", alt_dir)
            return str(alt_dir)
        logger.warning("本地模型目录不存在，将尝试从 HuggingFace 下载: %s", hf_id)
        return hf_id

    def _load_model(self, model_key: str) -> None:
        """懒加载模型，相同模型不重复加载"""
        if self._current_model_key == model_key and self._model is not None:
            return

        try:
            import torch
            from qwen_asr import Qwen3ASRModel
        except ImportError as exc:
            raise TranscriptionError(f"依赖未安装: {exc}", engine_name=self.name)

        model_path = self._resolve_model_path(model_key)
        dtype = torch.bfloat16 if self.is_cuda else torch.float32
        device_map = self.device

        logger.info("加载 Qwen3-ASR 模型: %s (dtype=%s, device=%s)", model_path, dtype, device_map)
        try:
            self._model = Qwen3ASRModel.from_pretrained(
                model_path,
                dtype=dtype,
                device_map=device_map,
                max_inference_batch_size=4,
                max_new_tokens=256,
            )
            self._current_model_key = model_key
            logger.info("Qwen3-ASR 模型加载成功: %s", model_key)
        except Exception as exc:
            raise TranscriptionError(f"模型加载失败: {exc}", engine_name=self.name)

    def transcribe(self, request: STTRequest) -> STTResponse:
        """执行语音识别"""
        available, reason = self.check_available()
        if not available:
            raise TranscriptionError(f"引擎不可用: {reason}", engine_name=self.name)

        model_key = request.model or DEFAULT_MODEL
        self._load_model(model_key)

        max_new_tokens: int = int((request.options or {}).get("max_new_tokens", 256))
        qwen_lang = _to_qwen_language(request.language)

        try:
            results = self._model.transcribe(
                audio=str(request.audio_path),
                language=qwen_lang,
                max_new_tokens=max_new_tokens,
            )
            if not results:
                raise TranscriptionError("模型返回空结果", engine_name=self.name)
            result = results[0]
            text = result.text.strip()
            detected_lang = result.language or request.language or "auto"

            # qwen-asr 不直接返回 duration；用 soundfile 或 wave 获取
            duration_ms = self._get_audio_duration_ms(request.audio_path)

            return STTResponse(
                text=text,
                segments=[STTSegment(start_ms=0, end_ms=duration_ms, text=text)],
                language_detected=detected_lang,
                engine=self.name,
                model=model_key,
                duration_ms=duration_ms,
            )

        except (ModelNotFoundError, TranscriptionError):
            raise
        except Exception as exc:
            logger.exception("Qwen3-ASR 识别失败: %s", exc)
            raise TranscriptionError(f"识别失败: {exc}", engine_name=self.name)

    @staticmethod
    def _get_audio_duration_ms(audio_path: Path) -> int:
        """获取音频时长（毫秒），尽量不引入额外依赖"""
        try:
            import wave
            with wave.open(str(audio_path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return int(frames / rate * 1000)
        except Exception:
            pass
        try:
            import soundfile as sf
            info = sf.info(str(audio_path))
            return int(info.duration * 1000)
        except Exception:
            pass
        return 0
