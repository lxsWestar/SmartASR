"""
config_api.py - 配置管理 API
===============================

端点:
- GET /config - 获取当前配置
- PUT /config - 更新配置
- PUT /config/api-keys/{engine_name} - 设置引擎 API Key
- DELETE /config/api-keys/{engine_name} - 删除引擎 API Key
"""

import os
import logging
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.stt import list_engines
from backend.app.services.stt.config import get_config, set_config, STTConfig
from backend.app.services.stt.audio_utils import SUPPORTED_FORMATS

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Pydantic 模型 ============

class APIKeyStatus(BaseModel):
    """API Key 状态"""
    configured: bool
    masked: Optional[str] = None  # 脱敏显示，如 "sk-***xxx"


class ConfigResponse(BaseModel):
    """配置响应"""
    default_engine: str
    default_language: str = "auto"
    max_file_size_mb: int
    api_timeout: int
    supported_formats: List[str]
    models_dir: str
    cache_dir: str
    api_keys: Dict[str, APIKeyStatus]


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    default_engine: Optional[str] = Field(None, description="默认引擎")
    default_language: Optional[str] = Field(None, description="默认语言")
    max_file_size_mb: Optional[int] = Field(None, ge=1, le=5000, description="最大文件大小 (MB)")
    api_timeout: Optional[int] = Field(None, ge=10, le=3600, description="API 超时时间 (秒)")


class ConfigUpdateResponse(BaseModel):
    """配置更新响应"""
    success: bool
    message: str
    updated_fields: List[str]


class APIKeySetRequest(BaseModel):
    """设置 API Key 请求"""
    api_key: str = Field(..., min_length=1, description="API Key")


class APIKeyResponse(BaseModel):
    """API Key 操作响应"""
    success: bool
    message: str


# ============ 辅助函数 ============

def _mask_api_key(key: str) -> str:
    """
    脱敏 API Key
    
    例: "sk-abc123xyz789" -> "sk-***789"
    """
    if not key or len(key) < 8:
        return "***"
    
    # 保留前缀和最后3个字符
    if key.startswith("sk-"):
        return f"sk-***{key[-3:]}"
    return f"***{key[-3:]}"


def _get_api_key_status(engine_name: str) -> APIKeyStatus:
    """获取引擎的 API Key 状态"""
    config = get_config()
    
    # 定义引擎对应的环境变量名
    env_key_map = {
        "ali_qwen": "DASHSCOPE_API_KEY",
        "openai_whisper": "OPENAI_API_KEY",
        "google_stt": "GOOGLE_APPLICATION_CREDENTIALS",
        "azure_speech": "AZURE_SPEECH_KEY",
    }
    
    env_key = env_key_map.get(engine_name)
    api_key = None
    
    # 从环境变量获取
    if env_key:
        api_key = os.environ.get(env_key)
    
    # 从配置获取
    if not api_key:
        api_key = config.engine_configs.get("api_keys", {}).get(engine_name)
    
    if api_key:
        return APIKeyStatus(configured=True, masked=_mask_api_key(api_key))
    
    return APIKeyStatus(configured=False, masked=None)


def _get_all_api_keys_status() -> Dict[str, APIKeyStatus]:
    """获取所有引擎的 API Key 状态"""
    result = {}
    
    # 获取已注册的引擎
    engines = list_engines()
    
    # 需要 API Key 的引擎列表
    cloud_engines = ["ali_qwen", "openai_whisper", "google_stt", "azure_speech"]
    
    for engine_name in engines:
        if engine_name in cloud_engines:
            result[engine_name] = _get_api_key_status(engine_name)
    
    # 添加未注册但可能配置的引擎
    for engine_name in cloud_engines:
        if engine_name not in result:
            status = _get_api_key_status(engine_name)
            if status.configured:
                result[engine_name] = status
    
    return result


# ============ API 端点 ============

@router.get(
    "/config",
    response_model=ConfigResponse,
    summary="获取配置",
    description="获取当前服务配置，包括默认引擎、文件限制、API Key 状态等",
)
async def get_service_config() -> ConfigResponse:
    """获取当前服务配置"""
    config = get_config()
    
    # 构建支持的格式列表 (去掉点号)
    formats = [f.lstrip(".") for f in SUPPORTED_FORMATS]
    
    return ConfigResponse(
        default_engine=config.default_engine,
        default_language="auto",  # TODO: 添加到 STTConfig
        max_file_size_mb=config.max_file_size_mb,
        api_timeout=config.api_timeout,
        supported_formats=formats,
        models_dir=str(config.models_dir),
        cache_dir=str(config.cache_dir),
        api_keys=_get_all_api_keys_status(),
    )


@router.put(
    "/config",
    response_model=ConfigUpdateResponse,
    summary="更新配置",
    description="更新服务配置，只更新提供的字段",
)
async def update_service_config(request: ConfigUpdateRequest) -> ConfigUpdateResponse:
    """更新服务配置"""
    config = get_config()
    updated_fields = []
    
    # 验证引擎是否存在
    if request.default_engine is not None:
        available_engines = list_engines()
        if request.default_engine not in available_engines:
            raise HTTPException(
                status_code=400,
                detail=f"引擎 '{request.default_engine}' 不存在。可用引擎: {available_engines}"
            )
        config.default_engine = request.default_engine
        updated_fields.append("default_engine")
    
    # 更新其他字段
    if request.max_file_size_mb is not None:
        config.max_file_size_mb = request.max_file_size_mb
        updated_fields.append("max_file_size_mb")
    
    if request.api_timeout is not None:
        config.api_timeout = request.api_timeout
        updated_fields.append("api_timeout")
    
    # 更新全局配置
    set_config(config)
    
    if not updated_fields:
        return ConfigUpdateResponse(
            success=True,
            message="没有字段需要更新",
            updated_fields=[],
        )
    
    logger.info(f"配置已更新: {updated_fields}")
    
    return ConfigUpdateResponse(
        success=True,
        message=f"已更新 {len(updated_fields)} 个配置项",
        updated_fields=updated_fields,
    )


@router.put(
    "/config/api-keys/{engine_name}",
    response_model=APIKeyResponse,
    summary="设置 API Key",
    description="为指定引擎设置 API Key",
)
async def set_api_key(engine_name: str, request: APIKeySetRequest) -> APIKeyResponse:
    """设置引擎 API Key"""
    config = get_config()
    
    # 定义引擎对应的环境变量名
    env_key_map = {
        "ali_qwen": "DASHSCOPE_API_KEY",
        "openai_whisper": "OPENAI_API_KEY",
        "google_stt": "GOOGLE_APPLICATION_CREDENTIALS",
        "azure_speech": "AZURE_SPEECH_KEY",
    }
    
    # 设置环境变量 (运行时生效)
    env_key = env_key_map.get(engine_name)
    if env_key:
        os.environ[env_key] = request.api_key
        logger.info(f"已设置环境变量 {env_key}")
    
    # 同时保存到配置
    if "api_keys" not in config.engine_configs:
        config.engine_configs["api_keys"] = {}
    config.engine_configs["api_keys"][engine_name] = request.api_key
    
    set_config(config)
    
    return APIKeyResponse(
        success=True,
        message=f"引擎 '{engine_name}' 的 API Key 已设置",
    )


@router.delete(
    "/config/api-keys/{engine_name}",
    response_model=APIKeyResponse,
    summary="删除 API Key",
    description="删除指定引擎的 API Key",
)
async def delete_api_key(engine_name: str) -> APIKeyResponse:
    """删除引擎 API Key"""
    config = get_config()
    
    # 定义引擎对应的环境变量名
    env_key_map = {
        "ali_qwen": "DASHSCOPE_API_KEY",
        "openai_whisper": "OPENAI_API_KEY",
        "google_stt": "GOOGLE_APPLICATION_CREDENTIALS",
        "azure_speech": "AZURE_SPEECH_KEY",
    }
    
    removed = False
    
    # 删除环境变量
    env_key = env_key_map.get(engine_name)
    if env_key and env_key in os.environ:
        del os.environ[env_key]
        removed = True
        logger.info(f"已删除环境变量 {env_key}")
    
    # 从配置中删除
    if "api_keys" in config.engine_configs:
        if engine_name in config.engine_configs["api_keys"]:
            del config.engine_configs["api_keys"][engine_name]
            removed = True
    
    set_config(config)
    
    if removed:
        return APIKeyResponse(
            success=True,
            message=f"引擎 '{engine_name}' 的 API Key 已删除",
        )
    
    return APIKeyResponse(
        success=True,
        message=f"引擎 '{engine_name}' 没有配置 API Key",
    )


@router.get(
    "/config/api-keys",
    response_model=Dict[str, APIKeyStatus],
    summary="获取所有 API Key 状态",
    description="获取所有引擎的 API Key 配置状态",
)
async def get_all_api_keys_status() -> Dict[str, APIKeyStatus]:
    """获取所有 API Key 状态"""
    return _get_all_api_keys_status()
