"""
engines.py - 引擎管理 API
===========================

端点:
- GET /engines - 列出所有引擎
- GET /engines/{engine_name} - 获取引擎详情
- GET /engines/{engine_name}/models - 列出引擎模型
- GET /engines/{engine_name}/models/{model_name} - 获取模型详情
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.app.services.stt import (
    list_engines,
    get_engine_class,
    get_engine_metadata,
    create_engine,
    EngineNotFoundError,
    ModelNotFoundError,
)

router = APIRouter()


# ============ Pydantic 响应模型 ============

class EngineBasicInfo(BaseModel):
    """引擎基本信息"""
    name: str
    display_name: str
    type: str        # "local" 或 "cloud"
    vendor: str      # 厂商，如 "Alibaba"
    models: List[str]


class EnginesListResponse(BaseModel):
    """引擎列表响应"""
    engines: List[EngineBasicInfo]


class ParameterInfo(BaseModel):
    """参数信息"""
    name: str
    type: str
    required: bool = False
    default: Any = None
    options: Optional[List[Any]] = None
    description: str = ""


class ModelDetailInfo(BaseModel):
    """模型详细信息"""
    name: str
    display_name: str
    description: str
    languages: List[str]
    size: str
    default: bool = False
    parameters: List[ParameterInfo] = []
    features: List[str] = []


class EngineDetailResponse(BaseModel):
    """引擎详情响应"""
    name: str
    display_name: str
    type: str
    description: str
    version: str
    available: bool
    available_reason: str
    supported_languages: List[str]
    requires_api_key: bool
    default_model: str
    models: List[ModelDetailInfo]
    parameters: List[ParameterInfo]


class ModelsListResponse(BaseModel):
    """模型列表响应"""
    engine: str
    models: List[ModelDetailInfo]


class ModelDetailResponse(BaseModel):
    """单个模型详情响应"""
    name: str
    engine: str
    display_name: str
    description: str
    languages: List[str]
    size: str
    default: bool
    parameters: List[ParameterInfo]
    features: List[str]


# ============ API 端点 ============

@router.get("/engines", response_model=EnginesListResponse)
async def get_engines():
    """
    列出所有可用引擎
    
    返回所有已注册引擎的基本信息，包括名称、类型和支持的模型列表。
    """
    engine_names = list_engines()
    engines_info = []
    
    for name in engine_names:
        try:
            metadata = get_engine_metadata(name)
            engines_info.append(EngineBasicInfo(
                name=metadata.name,
                display_name=metadata.display_name,
                type=metadata.type,
                vendor=getattr(metadata, "vendor", ""),
                models=[m.name for m in metadata.models],
            ))
        except Exception:
            # 跳过获取元数据失败的引擎
            pass
    
    return EnginesListResponse(engines=engines_info)


@router.get("/engines/{engine_name}", response_model=EngineDetailResponse)
async def get_engine_detail(engine_name: str):
    """
    获取引擎详细信息
    
    返回指定引擎的完整元数据，包括：
    - 支持的语言和模型
    - 是否需要 API Key
    - 可配置参数
    - 当前可用状态
    """
    try:
        metadata = get_engine_metadata(engine_name)
    except EngineNotFoundError:
        raise HTTPException(status_code=404, detail=f"引擎 '{engine_name}' 不存在")
    
    # 检查可用性
    try:
        engine = create_engine(engine_name)
        available, available_reason = engine.check_available()
        default_model = engine.get_default_model()
    except Exception as e:
        available = False
        available_reason = str(e)
        default_model = metadata.models[0].name if metadata.models else ""
    
    # 转换模型信息
    models_info = []
    for m in metadata.models:
        models_info.append(ModelDetailInfo(
            name=m.name,
            display_name=m.display_name,
            description=m.description,
            languages=m.languages,
            size=m.size,
            default=m.default,
            parameters=[ParameterInfo(**p.to_dict()) for p in m.parameters],
            features=m.features,
        ))
    
    # 转换参数信息
    params_info = [ParameterInfo(**p.to_dict()) for p in metadata.parameters]
    
    return EngineDetailResponse(
        name=metadata.name,
        display_name=metadata.display_name,
        type=metadata.type,
        description=metadata.description,
        version=metadata.version,
        available=available,
        available_reason=available_reason,
        supported_languages=metadata.supported_languages,
        requires_api_key=metadata.requires_api_key,
        default_model=default_model,
        models=models_info,
        parameters=params_info,
    )


@router.get("/engines/{engine_name}/models", response_model=ModelsListResponse)
async def get_engine_models(engine_name: str):
    """
    列出引擎支持的模型
    
    返回指定引擎支持的所有模型及其详细信息。
    """
    try:
        metadata = get_engine_metadata(engine_name)
    except EngineNotFoundError:
        raise HTTPException(status_code=404, detail=f"引擎 '{engine_name}' 不存在")
    
    models_info = []
    for m in metadata.models:
        models_info.append(ModelDetailInfo(
            name=m.name,
            display_name=m.display_name,
            description=m.description,
            languages=m.languages,
            size=m.size,
            default=m.default,
            parameters=[ParameterInfo(**p.to_dict()) for p in m.parameters],
            features=m.features,
        ))
    
    return ModelsListResponse(engine=engine_name, models=models_info)


@router.get("/engines/{engine_name}/models/{model_name}", response_model=ModelDetailResponse)
async def get_model_detail(engine_name: str, model_name: str):
    """
    获取模型详细信息
    
    返回指定引擎中指定模型的完整信息和可配置参数。
    """
    try:
        metadata = get_engine_metadata(engine_name)
    except EngineNotFoundError:
        raise HTTPException(status_code=404, detail=f"引擎 '{engine_name}' 不存在")
    
    # 查找模型
    model_info = None
    for m in metadata.models:
        if m.name == model_name:
            model_info = m
            break
    
    if model_info is None:
        raise HTTPException(
            status_code=404, 
            detail=f"模型 '{model_name}' 在引擎 '{engine_name}' 中不存在"
        )
    
    return ModelDetailResponse(
        name=model_info.name,
        engine=engine_name,
        display_name=model_info.display_name,
        description=model_info.description,
        languages=model_info.languages,
        size=model_info.size,
        default=model_info.default,
        parameters=[ParameterInfo(**p.to_dict()) for p in model_info.parameters],
        features=model_info.features,
    )
