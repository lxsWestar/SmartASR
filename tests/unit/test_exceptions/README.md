# tests/unit/test_exceptions/

## 本目录职责

单元测试：验证所有 STT 异常类的继承关系、属性和实例化行为。

## 文件清单

| 文件 | 职责 |
|------|------|
| `test_exceptions.py` | 测试 STTException 基类及 11 个子类 |

## 测试覆盖的异常类

所有异常类定义于 `backend/app/services/stt/exceptions.py`：

| 类名 | 类型 | 测试要点 |
|------|------|----------|
| `STTException` | 基类 | 可实例化，`message` 属性，`is` isinstance 基类 |
| 11 个子类 | 具体异常 | 继承自 `STTException`，各自的错误码/消息格式 |

## 设计约束（AI 必读）

> ⚠️ **最容易犯的错误**

1. **禁止在此测试目录修改异常类**——异常定义只能在 `backend/app/services/stt/exceptions.py` 中修改
2. **新增异常子类时**，先在 `exceptions.py` 中定义，再在此处添加测试，不能反向操作
3. **继承关系测试是关键**——必须验证所有子类都 `isinstance(e, STTException)`，确保上层 `except STTException` 能统一捕获
4. **不得在测试中 Mock 异常类**——直接实例化验证，异常类本身不依赖外部

## 测试示例

```python
def test_all_exceptions_inherit_base():
    """所有子类必须继承 STTException，确保统一捕获"""
    subclasses = STTException.__subclasses__()
    assert len(subclasses) == 11  # 当前 11 个子类

    for exc_class in subclasses:
        instance = exc_class("测试消息")
        assert isinstance(instance, STTException)
        assert isinstance(instance, Exception)
```

## 运行命令

```bash
pytest tests/unit/test_exceptions/ -v
```

## 上下游关系

```
[测试目标] backend/app/services/stt/exceptions.py
[不依赖] 引擎、网络、文件系统
[被依赖] 整个 services/stt/ 层抛出的异常都来自该文件
```
