"""
API 端点集成测试
================

注意：这些测试需要 API 服务实现后才能运行。
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


# 标记这些测试需要 API 服务
pytestmark = pytest.mark.skipif(
    True,  # 默认跳过，除非 API 服务可用
    reason="API 服务未实现"
)


class TestAPIEndpoints:
    """API 端点测试"""
    
    def test_list_engines(self):
        """测试列出引擎 API"""
        # TODO: 实现 API 后启用
        pass
    
    def test_get_engine_info(self):
        """测试获取引擎信息 API"""
        # TODO: 实现后启用
        pass
    
    def test_transcribe(self):
        """测试识别 API"""
        # TODO: 实现后启用
        pass
    
    def test_health_check(self):
        """测试健康检查 API"""
        # TODO: 实现后启用
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
