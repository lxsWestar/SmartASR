"""
Qwen3-ASR 本地引擎
=================

基于 Qwen3-ASR 开源模型（Alibaba Qwen 团队）的本地推理引擎。

支持模型:
  - Qwen/Qwen3-ASR-0.6B  轻量级，速度优先
  - Qwen/Qwen3-ASR-1.7B  平衡精度与速度

依赖:
  pip install transformers torch torchaudio

模型来源: https://github.com/QwenLM/Qwen-ASR
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
from ..exceptions import EngineNotAvailableError, ModelNotFoundError, TranscriptionError

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
        "features": ["timestamps", "multi_language"],
    },
    "Qwen3-ASR-1.7B": {
        "hf_id": "Qwen/Qwen3-ASR-1.7B",
        "display_name": "Qwen3-ASR 1.7B",
        "description": "标准模型（1.7B参数），精度与速度平衡",
        "size": "~3.4GB",
        "languages": ["zh", "en", "ja", "ko", "auto"],
        "default": False,
        "features": ["timestamps", "multi_language"],
    },
}

DEFAULT_MODEL = "Qwen3-ASR-0.6B"

# 本地模型缓存目录（可通过环境变量覆盖）
_MODELS_DIR = Path(os.environ.get("STT_MODELS_DIR", "./models"))


# ── エンジン実装 ────────────────────────────────────────────────────────────

@register_engine
@dataclass
class QwenLocalEngine(BaseSTTEngine):
    """
    Qwen3-ASR 本地推理引擎

    基于 transformers 库加载 Qwen3-ASR 开源模型，
    支持 0.6B 和 1.7B 两种规格。
    """

    # 引擎标识
    name: str = field(default="qwen_local", init=False)
    display_name: str = field(default="Qwen3-ASR", init=False)
    engine_type: str = field(default="local", init=False)
    vendor: str = field(default="Alibaba", init=False)

    # 运行时状态
    _processor: Any = field(default=None, init=False, repr=False)
    _model: Any = field(default=None, init=False, repr=False)
    _current_model_name: str = field(default="", init=False)

    @classmethod
    def get_metadata(cls) -> EngineMetadata:
        """返回引擎元数据"""
        models = []
        for model_key, info in QWEN_LOCAL_MODELS.items():
            models.append(ModelInfo(
                name=model_key,
                display_name=info["display_name"],
                description=info["description"],
                languages=info["languages"],
                size=info["size"],
                default=info["default"],
                features=info["features"],
            ))

        return EngineMetadata(
            name="qwen_local",
            display_name="Qwen3-ASR",
            vendor="Alibaba",
            type="local",
            description="Qwen3-ASR 开源本地模型，支持 0.6B / 1.7B 两种规格",
            version="3.0.0",
            supported_languages=["zh", "en", "ja", "ko", "auto"],
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
                    name="beam_size",
                    type="integer",
                    required=False,
                    default=5,
                    options=[1, 3, 5, 10],
                    description="Beam search 宽度，越大越准但越慢",
                ),
            ],
        )

    def check_available(self) -> Tuple[bool, str]:
        """检查引擎依赖是否满足"""
        missing = []
        try:
            import torch  # noqa: F401
        except ImportError:
            missing.append("torch")

        try:
            import transformers  # noqa: F401
        except ImportError:
            missing.append("transformers")

        try:
            import librosa  # noqa: F401
        except ImportError:
            missing.append("librosa")

        if missing:
            return False, f"缺少依赖：{', '.join(missing)}。请运行: pip install {' '.join(missing)}"

        return True, "依赖已满足"

    def get_models(self) -> List[str]:
        """返回支持的模型列表"""
        return list(QWEN_LOCAL_MODELS.keys())

    def _get_hf_id(self, model_name: Optional[str]) -> str:
        """将用户传入的 model 名称映射到 HuggingFace 模型 ID"""
        name = model_name or DEFAULT_MODEL
        if name in QWEN_LOCAL_MODELS:
            return QWEN_LOCAL_MODELS[name]["hf_id"]
        # 兼容直接传 HF ID 的情况（如 Qwen/Qwen3-ASR-0.6B）
        for info in QWEN_LOCAL_MODELS.values():
            if info["hf_id"] == name:
                return name
        raise ModelNotFoundError(f"未知模型: {name}", engine_name=self.name, model_name=name)

    def _load_model(self, hf_id: str) -> None:
        """懒加载模型，相同模型不重复加载"""
        if self._current_model_name == hf_id and self._model is not None:
            return

        try:
            import torch
            from transformers import AutoProcessor, AutoModelForCausalLM
        except ImportError as e:
            raise EngineNotAvailableError(f"依赖未安装: {e}", engine_name=self.name)

        logger.info("加载 Qwen3-ASR 模型: %s (device=%s)", hf_id, self.device)

        # 优先从本地缓存目录加载
        local_path = _MODELS_DIR / hf_id.replace("/", "--")
        model_path = str(local_path) if local_path.exists() else hf_id

        try:
            self._processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
            self._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if self.is_cuda else torch.float32,
                device_map=self.device,
                trust_remote_code=True,
            )
            self._model.eval()
            self._current_model_name = hf_id
            logger.info("Qwen3-ASR 模型加载成功: %s", hf_id)
        except Exception as exc:
            raise TranscriptionError(f"模型加载失败: {exc}", engine_name=self.name)

    def transcribe(self, request: STTRequest) -> STTResponse:
        """执行语音识别"""
        available, reason = self.check_available()
        if not available:
            raise EngineNotAvailableError(reason, engine_name=self.name)

        import torch
        import librosa

        hf_id = self._get_hf_id(request.model)
        self._load_model(hf_id)

        beam_size: int = int((request.options or {}).get("beam_size", 5))

        try:
            # 加载音频（统一 16kHz 单声道）
            audio, _ = librosa.load(str(request.audio_path), sr=16000, mono=True)

            # 预处理
            inputs = self._processor(
                audios=[audio],
                return_tensors="pt",
                sampling_rate=16000,
            )
            if self.is_cuda:
                inputs = {k: v.to("cuda") if hasattr(v, "to") else v for k, v in inputs.items()}

            # 推理
            with torch.no_grad():
                generated_ids = self._model.generate(
                    **inputs,
                    num_beams=beam_size,
                    max_new_tokens=512,
                )

            # 解码
            text = self._processor.batch_decode(
                generated_ids,
                skip_special_tokens=True,
            )[0].strip()

            duration_ms = int(len(audio) / 16000 * 1000)

            return STTResponse(
                text=text,
                segments=[STTSegment(start_ms=0, end_ms=duration_ms, text=text)],
                language=request.language or "auto",
                engine=self.name,
                model=request.model or DEFAULT_MODEL,
                duration_ms=duration_ms,
            )

        except (EngineNotAvailableError, ModelNotFoundError, TranscriptionError):
            raise
        except Exception as exc:
            logger.exception("Qwen3-ASR 识别失败: %s", exc)
            raise TranscriptionError(f"识别失败: {exc}", engine_name=self.name)
