"""
Pytest 配置和共享 Fixtures
===========================
"""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """创建临时目录，测试后自动清理"""
    dir_path = Path(tempfile.mkdtemp())
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture
def sample_audio_path(temp_dir):
    """创建示例音频文件路径（不创建实际文件）"""
    return temp_dir / "sample.wav"


@pytest.fixture
def project_root():
    """返回项目根目录"""
    return Path(__file__).parent.parent


@pytest.fixture
def stt_module_path(project_root):
    """返回 STT 模块路径"""
    return project_root / "backend" / "app" / "services" / "stt"
