"""
config.py - 配置管理
========================

作用: 统一管理环境变量、配置文件和默认值。
关键 API: STTConfig, get_config(), get_api_key()
维护: AI + Human

模型源配置 (企业部署):
- STT_MODEL_SOURCE: 模型源类型 (local/network/auto)
- STT_MODELS_DIR: 本地模型目录 (预下载)
- STT_MODEL_SERVER: 内网模型服务器 URL (如 http://192.168.1.100:8000/models)
- FUNASR_HUB: 官方源选择 (hf/ms)
"""

import os
import json
import shutil
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Literal
from urllib.parse import urljoin

from .compat import get_cache_dir, get_models_dir, setup_environment


logger = logging.getLogger(__name__)


# 模型源类型
ModelSourceType = Literal["local", "network", "official", "auto"]


@dataclass
class ModelSourceConfig:
    """
    模型源配置
    
    支持三种模型来源:
    1. local - 本地预下载目录 (离线部署)
    2. network - 内网服务器 (公司共享)
    3. official - 官方源 (HuggingFace/ModelScope)
    
    加载顺序: local -> network -> official
    """
    
    # 源类型: local/network/official/auto
    source_type: ModelSourceType = "auto"
    
    # 本地模型目录 (预下载好的模型)
    local_dir: Optional[Path] = None
    
    # 内网模型服务器 URL (如 http://192.168.1.100:8000/models)
    network_server: Optional[str] = None
    
    # 官方 hub 选择 (hf=HuggingFace, ms=ModelScope)
    official_hub: str = "hf"
    
    @classmethod
    def from_env(cls) -> "ModelSourceConfig":
        """从环境变量创建配置，自动检测本地模型目录"""
        # 使用 get_models_dir() 自动检测 (会按优先级检查 环境变量 -> ./models -> 系统目录)
        local_dir = get_models_dir()
        network_server = os.environ.get("STT_MODEL_SERVER") or os.environ.get("FUNASR_MODEL_URL")
        
        return cls(
            source_type=os.environ.get("STT_MODEL_SOURCE", "auto"),  # type: ignore
            local_dir=local_dir,
            network_server=network_server,
            official_hub=os.environ.get("FUNASR_HUB", "ms"),  # 默认用 ModelScope
        )
    
    def get_model_path(self, model_name: str, download_if_missing: bool = True) -> Optional[Path]:
        """
        获取模型路径
        
        按优先级尝试: local -> network -> official
        
        Args:
            model_name: 模型名称 (如 "SenseVoiceSmall", "paraformer-zh")
            download_if_missing: 如果不存在是否下载
            
        Returns:
            模型目录路径，或 None (让 FunASR 自行下载)
        """
        # 1. 检查本地目录
        if self.local_dir:
            local_path = self._find_in_local(model_name)
            if local_path:
                logger.info(f"使用本地模型: {local_path}")
                return local_path
        
        # 2. 检查/下载从内网服务器
        if self.network_server and download_if_missing:
            network_path = self._download_from_network(model_name)
            if network_path:
                logger.info(f"从内网服务器下载模型: {network_path}")
                return network_path
        
        # 3. 返回 None，让 FunASR 从官方源下载
        logger.info(f"模型将从官方源 ({self.official_hub}) 下载")
        return None
    
    def _find_in_local(self, model_name: str) -> Optional[Path]:
        """在本地目录中查找模型"""
        if not self.local_dir or not self.local_dir.exists():
            return None
        
        # 可能的目录名称
        possible_names = [
            model_name,
            model_name.lower(),
            model_name.replace("-", "_"),
            f"iic/{model_name}",  # ModelScope 格式
            f"funasr/{model_name}",  # HuggingFace 格式
        ]
        
        for name in possible_names:
            # 直接子目录
            path = self.local_dir / name
            if path.exists() and path.is_dir():
                return path
            
            # hub 子目录格式 (如 hub/iic/SenseVoiceSmall)
            for subdir in ["hub", "models", "modelscope", "huggingface"]:
                path = self.local_dir / subdir / name
                if path.exists() and path.is_dir():
                    return path
        
        return None
    
    def _download_from_network(self, model_name: str) -> Optional[Path]:
        """从内网服务器下载模型"""
        if not self.network_server:
            return None
        
        try:
            import urllib.request
            import zipfile
            import tempfile
            
            # 目标目录 (下载到本地模型目录)
            target_dir = self.local_dir / model_name if self.local_dir else get_models_dir() / model_name
            if target_dir.exists() and any(target_dir.iterdir()):
                logger.info(f"模型已存在: {target_dir}")
                return target_dir
            
            # 构建下载 URL: http://server:port/models/{model_name}
            base_url = self.network_server.rstrip("/")
            model_url = f"{base_url}/models/{model_name}"
            
            logger.info(f"从内网下载模型: {model_url}")
            
            # 下载到临时文件
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                urllib.request.urlretrieve(model_url, tmp.name)
                tmp_path = tmp.name
            
            # 解压到目标目录
            target_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(tmp_path, "r") as zf:
                zf.extractall(target_dir)
            
            # 清理临时文件
            Path(tmp_path).unlink()
            
            logger.info(f"模型下载完成: {target_dir}")
            return target_dir
            
        except Exception as e:
            logger.warning(f"从内网下载模型失败: {e}")
            return None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "source_type": self.source_type,
            "local_dir": str(self.local_dir) if self.local_dir else None,
            "network_server": self.network_server,
            "official_hub": self.official_hub,
        }


@dataclass
class STTConfig:
    """STT 服务配置"""
    
    # 目录配置
    models_dir: Path = field(default_factory=get_models_dir)
    cache_dir: Path = field(default_factory=get_cache_dir)
    
    # 音频处理
    max_file_size_mb: int = 500       # 最大文件大小 (MB)
    default_sample_rate: int = 16000  # 默认采样率
    
    # 默认引擎
    default_engine: str = "ali_funasr"
    
    # API 配置
    api_timeout: int = 300            # API 超时时间 (秒)
    
    # 模型源配置
    model_source: ModelSourceConfig = field(default_factory=ModelSourceConfig.from_env)
    
    # 引擎特定配置
    engine_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后设置环境变量"""
        setup_environment()
        
        # 确保目录存在
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_env(cls) -> "STTConfig":
        """从环境变量创建配置"""
        return cls(
            models_dir=Path(os.environ.get("STT_MODELS_DIR", get_models_dir())),
            cache_dir=Path(os.environ.get("STT_CACHE_DIR", get_cache_dir())),
            max_file_size_mb=int(os.environ.get("STT_MAX_FILE_SIZE_MB", "500")),
            default_engine=os.environ.get("STT_DEFAULT_ENGINE", "ali_funasr"),
            api_timeout=int(os.environ.get("STT_API_TIMEOUT", "300")),
            model_source=ModelSourceConfig.from_env(),
        )
    
    @classmethod
    def from_file(cls, path: Path) -> "STTConfig":
        """从配置文件创建配置"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 解析模型源配置
        model_source_data = data.get("model_source", {})
        model_source = ModelSourceConfig(
            source_type=model_source_data.get("source_type", "auto"),
            local_dir=Path(model_source_data["local_dir"]) if model_source_data.get("local_dir") else None,
            network_server=model_source_data.get("network_server"),
            official_hub=model_source_data.get("official_hub", "hf"),
        )
        
        return cls(
            models_dir=Path(data.get("models_dir", get_models_dir())),
            cache_dir=Path(data.get("cache_dir", get_cache_dir())),
            max_file_size_mb=data.get("max_file_size_mb", 500),
            default_engine=data.get("default_engine", "ali_funasr"),
            api_timeout=data.get("api_timeout", 300),
            model_source=model_source,
            engine_configs=data.get("engine_configs", {}),
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "models_dir": str(self.models_dir),
            "cache_dir": str(self.cache_dir),
            "max_file_size_mb": self.max_file_size_mb,
            "default_sample_rate": self.default_sample_rate,
            "default_engine": self.default_engine,
            "api_timeout": self.api_timeout,
            "model_source": self.model_source.to_dict(),
            "engine_configs": self.engine_configs,
        }
    
    def save(self, path: Path) -> None:
        """保存配置到文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    def get_engine_config(self, engine_name: str) -> Dict[str, Any]:
        """获取引擎特定配置"""
        return self.engine_configs.get(engine_name, {})
    
    def set_engine_config(self, engine_name: str, config: Dict[str, Any]) -> None:
        """设置引擎特定配置"""
        self.engine_configs[engine_name] = config
    
    def get_api_key(self, key_name: str) -> Optional[str]:
        """
        获取 API Key
        
        优先从环境变量获取，然后从配置获取。
        
        Args:
            key_name: Key 名称，如 "DASHSCOPE_API_KEY"
            
        Returns:
            API Key 或 None
        """
        # 先从环境变量获取
        value = os.environ.get(key_name)
        if value:
            return value
        
        # 再从配置获取
        return self.engine_configs.get("api_keys", {}).get(key_name)


# 全局配置实例
_config: Optional[STTConfig] = None

# 配置文件搜索路径
CONFIG_SEARCH_PATHS = [
    Path.cwd() / "config.json",  # 当前目录
    Path(__file__).parent.parent.parent.parent.parent / "config.json",  # 项目根目录
]


def get_config() -> STTConfig:
    """
    获取全局配置实例
    
    加载顺序:
    1. 环境变量 STT_CONFIG_FILE 指定的文件
    2. 当前目录 config.json
    3. 项目根目录 config.json
    4. 从环境变量构建默认配置
    """
    global _config
    if _config is None:
        # 1. 检查环境变量指定的配置文件
        config_file = os.environ.get("STT_CONFIG_FILE")
        if config_file:
            config_path = Path(config_file)
            if config_path.exists():
                logger.info(f"从配置文件加载: {config_path}")
                _config = STTConfig.from_file(config_path)
                return _config
        
        # 2. 搜索默认路径
        for search_path in CONFIG_SEARCH_PATHS:
            if search_path.exists():
                logger.info(f"从配置文件加载: {search_path}")
                _config = STTConfig.from_file(search_path)
                return _config
        
        # 3. 从环境变量创建
        logger.info("使用环境变量配置")
        _config = STTConfig.from_env()
    return _config


def set_config(config: STTConfig) -> None:
    """设置全局配置实例"""
    global _config
    _config = config


def reset_config() -> None:
    """重置全局配置"""
    global _config
    _config = None
