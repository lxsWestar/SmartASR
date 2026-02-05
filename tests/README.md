# tests/ - 测试目录

> 使用 pytest 框架，按测试层级组织

## 职责
存放 SmartASR 项目的所有测试代码。

## 目录结构
```
tests/
├── README.md          # 本文件
├── conftest.py        # pytest 全局配置和 fixtures
├── quick_test.py      # 快速集成测试脚本
│
├── unit/              # 单元测试 (隔离测试单个模块)
│   ├── test_exceptions/
│   │   ├── test_exceptions.py
│   │   └── fixtures/
│   ├── test_dto/
│   │   ├── test_dto.py
│   │   └── fixtures/
│   ├── test_audio_utils/
│   │   ├── test_audio_utils.py
│   │   └── fixtures/
│   └── test_registry/
│       ├── test_registry.py
│       └── fixtures/
│
├── integration/       # 集成测试 (测试模块间交互)
│   ├── test_funasr/
│   │   ├── test_funasr_engine.py
│   │   └── fixtures/
│   └── test_api/
│       ├── test_api_endpoints.py
│       └── fixtures/
│
└── e2e/               # 端到端测试 (完整流程)
    └── test_full_pipeline/
        ├── test_transcribe.py
        └── fixtures/
```

## 测试层级说明

### unit/ - 单元测试
- **目标**: 隔离测试单个函数/类
- **特点**: 快速、无外部依赖、Mock 外部调用
- **命名**: `test_{模块名}/test_{功能}.py`

### integration/ - 集成测试
- **目标**: 测试模块间交互
- **特点**: 可能需要真实依赖 (FFmpeg)、较慢
- **命名**: `test_{功能组}/test_{场景}.py`

### e2e/ - 端到端测试
- **目标**: 完整业务流程
- **特点**: 需要完整环境、最慢
- **命名**: `test_{流程名}/test_{用例}.py`

## 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行特定测试文件
pytest tests/unit/test_exceptions/test_exceptions.py

# 运行带覆盖率
pytest --cov=backend/app/services/stt --cov-report=html

# 快速集成测试 (不需要 pytest)
python tests/quick_test.py
```

## 编写测试指南

### 文件命名
```
tests/unit/test_{模块名}/
├── __init__.py
├── test_{功能1}.py
├── test_{功能2}.py
└── fixtures/          # 测试数据
    └── sample.mp3
```

### Fixture 使用
```python
# conftest.py 中定义全局 fixture
@pytest.fixture
def sample_audio():
    return Path(__file__).parent / "fixtures" / "sample.mp3"

# 测试文件中使用
def test_transcribe(sample_audio):
    result = transcribe(sample_audio)
    assert result.text
```

### Mock 示例
```python
from unittest.mock import patch, MagicMock

def test_check_ffmpeg_not_found():
    with patch("subprocess.run", side_effect=FileNotFoundError):
        assert check_ffmpeg() == False
```

## 上下游关系
```
测试对象:
  └── backend/app/services/stt/ (核心模块)

依赖:
  ├── pytest
  ├── pytest-cov (可选，覆盖率)
  └── pytest-mock (可选，Mock 工具)
```

## 隐含契约

### 测试独立性
- 每个测试必须独立运行
- 不依赖其他测试的执行顺序
- 测试后清理临时文件

### 命名规范
- 测试函数: `test_{被测功能}_{场景}()`
- 测试类: `Test{被测类名}`
- Fixture: `{资源类型}_{描述}`

### 断言风格
```python
# 推荐: 明确的断言
assert result.text == "预期文本"
assert len(result.segments) > 0

# 避免: 模糊的断言
assert result  # 不清楚在检查什么
```

## 当前测试状态

| 测试目录 | 状态 | 覆盖模块 |
|----------|------|----------|
| unit/test_exceptions | 🔲 待编写 | exceptions.py |
| unit/test_dto | 🔲 待编写 | dto.py |
| unit/test_audio_utils | 🔲 待编写 | audio_utils.py |
| unit/test_registry | 🔲 待编写 | registry.py |
| integration/test_funasr | 🔲 待编写 | FunASR 引擎 |
| quick_test.py | ✅ 可用 | 快速集成验证 |
