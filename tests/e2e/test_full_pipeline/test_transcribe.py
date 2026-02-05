"""
完整流程端到端测试
==================

测试从音频输入到文字输出的完整流程。
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


# 默认跳过，除非环境配置正确
pytestmark = pytest.mark.skipif(
    True,
    reason="端到端测试需要完整的引擎和模型配置"
)


class TestFullPipeline:
    """完整流程测试"""
    
    def test_transcribe_mp3(self):
        """测试 MP3 文件识别"""
        # TODO: 配置环境后启用
        pass
    
    def test_transcribe_wav(self):
        """测试 WAV 文件识别"""
        # TODO: 配置环境后启用
        pass
    
    def test_transcribe_long_audio(self):
        """测试长音频识别"""
        # TODO: 配置环境后启用
        pass
    
    def test_transcribe_chinese_path(self):
        """测试中文路径"""
        # TODO: 配置环境后启用
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
