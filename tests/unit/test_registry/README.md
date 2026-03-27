# tests/unit/test_registry/

## 本目录职责

单元测试：验证引擎注册表的注册、查找、创建、列举功能，使用动态创建的 Mock 引擎**完全隔离真实引擎**。

## 文件清单

| 文件 | 职责 |
|------|------|
| `test_registry.py` | 测试引擎注册表全部操作 |

## 测试覆盖内容

| 函数 | 测试要点 |
|------|----------|
| `register_engine(name, cls)` | 注册新引擎、重复注册覆盖/报错 |
| `get_engine_class(name)` | 已注册引擎可查到、未注册引擎抛异常 |
| `create_engine(name, config)` | 创建实例、传入 config 正确、未知引擎抛异常 |
| `list_engines()` | 返回已注册引擎名列表 |

## 设计约束（AI 必读）

> ⚠️ **最容易犯的错误**

1. **必须使用 Mock 引擎，不得导入真实引擎**（funasr、whisper 等），否则测试会依赖模型文件和 GPU
2. **每个测试后必须清理注册表**——使用 `conftest.py` 中的 fixture 恢复初始状态，防止测试间污染
3. **不要依赖注册表的初始状态**——测试开始时注册表可能有也可能没有真实引擎，用 fixture 隔离
4. **`create_engine` 失败场景必须测试**——未知引擎名应抛出具体异常（不是通用 `Exception`）

## Mock 引擎示例

```python
import pytest
from backend.app.services.stt.registry import register_engine, get_engine_class

class MockEngine:
    """测试专用伪引擎，不依赖任何外部库"""
    name = "mock-engine"

    def __init__(self, config):
        self.config = config

    def transcribe(self, audio_path, **kwargs):
        return MagicMock(text="mock result")

@pytest.fixture(autouse=True)
def clean_registry():
    """每个测试前后清理注册表，避免污染"""
    original = get_registry_snapshot()  # 记录初始状态
    yield
    restore_registry(original)          # 恢复初始状态
```

## 运行命令

```bash
pytest tests/unit/test_registry/ -v
```

## 上下游关系

```
[测试目标] backend/app/services/stt/registry.py（引擎注册表）
[Mock 对象] 真实引擎类（funasr、whisper 等）→ 用 MockEngine 替代
[不依赖] 模型文件、GPU、网络
[清理机制] conftest.py fixture 负责注册表状态隔离
```
