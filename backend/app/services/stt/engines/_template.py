"""
引擎模板
========

这是一个引擎开发模板，复制此文件并重命名（去掉下划线前缀）即可开发新引擎。

文件名规则：
- 以 _ 开头的文件不会被自动加载
- 正式引擎应移除 _ 前缀，如 ali_funasr.py

使用步骤：
1. 复制此文件到 engines/ 目录
2. 重命名为你的引擎名称（如 my_engine.py）
3. 修改类名和属性
4. 实现所有抽象方法
5. 引擎会自动被注册和发现
"""

from dataclasses import dataclass, field
from typing import List, Tuple

from ..base import BaseSTTEngine
from ..registry import register_engine
from ..dto import (
    STTRequest,
    STTResponse,
    STTSegment,
    EngineMetadata,
    ModelInfo,
    ParameterSpec,
)
from ..exceptions import TranscriptionError, ModelNotFoundError


# 注意：正式引擎需要取消下面的注释
# @register_engine
@dataclass
class TemplateEngine(BaseSTTEngine):
    """
    模板引擎 - 不会被自动加载
    
    实现你自己的引擎时，需要：
    1. 修改类名
    2. 修改 name, display_name, engine_type 类属性
    3. 实现 get_metadata, transcribe, get_models, check_available 方法
    """
    
    # 引擎标识信息 - 必须修改
    name: str = field(default="template", init=False)
    display_name: str = field(default="模板引擎", init=False)
    engine_type: str = field(default="local", init=False)  # "local" 或 "cloud"
    
    @classmethod
    def get_metadata(cls) -> EngineMetadata:
        """
        返回引擎元数据 - 用于 API 自描述
        
        此方法定义引擎的所有配置项，包括：
        - 基本信息 (名称、类型、描述)
        - 支持的语言列表
        - 可用模型及其特性
        - 引擎级和模型级参数
        
        返回的元数据会被：
        - API: GET /api/stt/engines/{name} 返回给前端
        - CLI: engines list 命令展示
        - 库: get_engine_metadata() 函数返回
        """
        return EngineMetadata(
            name="template",
            display_name="模板引擎",
            type="local",  # "local" (本地) 或 "cloud" (云端)
            description="这是一个引擎开发模板",
            version="1.0.0",
            supported_languages=["zh", "en", "auto"],  # 支持的语言代码
            requires_api_key=False,  # 云端引擎设为 True
            
            # ========== 引擎级参数 ==========
            # 所有模型共享的参数，在 transcribe() 中通过 request.options 读取
            parameters=[
                ParameterSpec(
                    name="use_itn",
                    type="boolean",      # 类型: string/boolean/integer/float
                    required=False,      # 是否必填
                    default=True,        # 默认值
                    description="是否使用逆文本正则化 (数字转汉字等)",
                ),
                ParameterSpec(
                    name="max_speakers",
                    type="integer",
                    required=False,
                    default=-1,
                    options=[-1, 2, 3, 4, 5],  # 可选值列表 (用于枚举)
                    description="最大说话人数 (-1 表示禁用说话人分离)",
                ),
                ParameterSpec(
                    name="output_language",
                    type="string",
                    required=False,
                    default="auto",
                    options=["auto", "zh", "en", "ja"],
                    description="输出语言 (auto 表示自动检测)",
                ),
            ],
            
            # ========== 模型列表 ==========
            models=[
                ModelInfo(
                    name="model_small",
                    display_name="小模型 (多语言)",
                    description="轻量级多语言模型，速度快，适合实时场景",
                    languages=["zh", "en", "ja", "ko"],  # 模型支持的语言
                    size="~500MB",                       # 模型大小
                    default=True,                        # 是否为默认模型
                    features=["timestamps", "vad"],      # 特性标签
                    # 模型级参数 - 仅此模型可用
                    parameters=[
                        ParameterSpec(
                            name="beam_size",
                            type="integer",
                            default=5,
                            options=[1, 3, 5, 10],
                            description="Beam search 宽度，越大越准但越慢",
                        ),
                    ],
                ),
                ModelInfo(
                    name="model_large",
                    display_name="大模型 (高精度)",
                    description="高精度模型，支持说话人分离",
                    languages=["zh", "en"],
                    size="~2GB",
                    default=False,
                    features=["timestamps", "vad", "speaker_diarization"],
                ),
            ],
        )
    
    def transcribe(self, request: STTRequest) -> STTResponse:
        """
        执行语音识别
        
        Args:
            request: 识别请求，包含:
                - audio_path: 音频文件路径
                - language: 语言代码 (zh/en/auto)
                - model: 模型名称 (可选)
                - options: 参数字典 (从 get_metadata().parameters 读取)
            
        Returns:
            STTResponse: 识别结果
            
        参数读取示例:
            use_itn = request.options.get("use_itn", True)
            max_speakers = request.options.get("max_speakers", -1)
        """
        # TODO: 实现实际的识别逻辑
        raise TranscriptionError("模板引擎不支持实际识别", engine_name=self.name)
    
    def get_models(self) -> List[str]:
        """获取支持的模型列表"""
        return ["model_small", "model_large"]
    
    def check_available(self) -> Tuple[bool, str]:
        """
        检查引擎是否可用
        
        Returns:
            Tuple[bool, str]: (是否可用, 原因说明)
            
        检查内容示例:
            1. 依赖库: try: import xxx except ImportError
            2. 模型文件: Path(model_path).exists()
            3. API Key: os.environ.get("XXX_API_KEY")
        """
        # TODO: 实现可用性检查
        return False, "模板引擎仅供参考，不可实际使用"
