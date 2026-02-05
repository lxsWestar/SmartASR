"""
health.py - 健康检查 API
===========================

端点:
- GET /health - 增强版健康检查
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.stt import (
    list_engines,
    create_engine,
    check_ffmpeg,
)
from backend.app.services.stt.audio_utils import get_ffmpeg_version

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Pydantic 响应模型 ============

class FFmpegStatus(BaseModel):
    """FFmpeg 状态"""
    available: bool
    version: Optional[str] = None


class EngineStatus(BaseModel):
    """引擎状态"""
    available: bool
    reason: str
    cuda: Optional[bool] = None
    api_key_configured: Optional[bool] = None


class SystemStatus(BaseModel):
    """系统状态"""
    cuda_available: bool
    cuda_device_count: int = 0
    cuda_device_name: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str  # "healthy", "degraded", "unhealthy"
    version: str
    timestamp: str
    ffmpeg: FFmpegStatus
    system: SystemStatus
    engines: Dict[str, EngineStatus]
    engines_count: int


# ============ 辅助函数 ============

def _check_cuda() -> Dict[str, Any]:
    """检查 CUDA 状态"""
    result = {
        "cuda_available": False,
        "cuda_device_count": 0,
        "cuda_device_name": None,
    }
    
    try:
        import torch
        result["cuda_available"] = torch.cuda.is_available()
        if result["cuda_available"]:
            result["cuda_device_count"] = torch.cuda.device_count()
            if result["cuda_device_count"] > 0:
                result["cuda_device_name"] = torch.cuda.get_device_name(0)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"检查 CUDA 状态失败: {e}")
    
    return result


def _check_engine_status(engine_name: str) -> Dict[str, Any]:
    """检查单个引擎状态"""
    result = {
        "available": False,
        "reason": "未知错误",
        "cuda": None,
        "api_key_configured": None,
    }
    
    try:
        engine = create_engine(engine_name)
        available, reason = engine.check_available()
        result["available"] = available
        result["reason"] = reason
        
        # 检查 CUDA (本地引擎)
        metadata = engine.get_metadata()
        if metadata.type == "local":
            result["cuda"] = getattr(engine, "is_cuda", False)
        
        # 检查 API Key (云端引擎)
        if metadata.requires_api_key:
            # 尝试获取配置状态
            result["api_key_configured"] = available  # 如果可用，说明 key 已配置
            
    except Exception as e:
        result["reason"] = str(e)
        logger.warning(f"检查引擎 {engine_name} 状态失败: {e}")
    
    return result


# ============ API 端点 ============

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="返回服务详细健康状态，包括 FFmpeg、CUDA、各引擎可用性",
)
async def health_check() -> HealthResponse:
    """
    增强版健康检查
    
    返回:
    - status: healthy (全部正常) / degraded (部分可用) / unhealthy (全部不可用)
    - ffmpeg: FFmpeg 可用性和版本
    - system: 系统信息 (CUDA)
    - engines: 各引擎状态
    """
    from backend.app.services.stt import __version__
    
    # 检查 FFmpeg
    ffmpeg_available = check_ffmpeg()
    ffmpeg_version = None
    if ffmpeg_available:
        try:
            ffmpeg_version = get_ffmpeg_version()
        except Exception:
            ffmpeg_version = "unknown"
    
    ffmpeg_status = FFmpegStatus(
        available=ffmpeg_available,
        version=ffmpeg_version,
    )
    
    # 检查 CUDA
    cuda_info = _check_cuda()
    system_status = SystemStatus(**cuda_info)
    
    # 检查所有引擎
    engine_names = list_engines()
    engines_status: Dict[str, EngineStatus] = {}
    available_count = 0
    
    for name in engine_names:
        status_info = _check_engine_status(name)
        engines_status[name] = EngineStatus(**status_info)
        if status_info["available"]:
            available_count += 1
    
    # 计算整体状态
    total_engines = len(engine_names)
    if not ffmpeg_available:
        overall_status = "unhealthy"
    elif total_engines == 0:
        overall_status = "degraded"  # 无引擎但 FFmpeg 可用
    elif available_count == total_engines:
        overall_status = "healthy"
    elif available_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        version=__version__,
        timestamp=datetime.now().isoformat(),
        ffmpeg=ffmpeg_status,
        system=system_status,
        engines=engines_status,
        engines_count=total_engines,
    )


@router.get(
    "/health/simple",
    summary="简单健康检查",
    description="快速返回服务是否存活，用于负载均衡器探测",
)
async def health_simple() -> Dict[str, str]:
    """
    简单健康检查 - 仅返回存活状态
    
    用于 Kubernetes liveness probe 或负载均衡器
    """
    return {"status": "ok"}


@router.get(
    "/health/ready",
    summary="就绪检查",
    description="检查服务是否准备好接收请求",
)
async def health_ready() -> Dict[str, Any]:
    """
    就绪检查 - 检查核心依赖是否就绪
    
    用于 Kubernetes readiness probe
    """
    ffmpeg_ok = check_ffmpeg()
    engines = list_engines()
    engines_ok = len(engines) > 0
    
    ready = ffmpeg_ok and engines_ok
    
    return {
        "ready": ready,
        "checks": {
            "ffmpeg": ffmpeg_ok,
            "engines": engines_ok,
        }
    }
