# STT 模块 AI 协作指令

> 本目录存放与 `stt/` 模块相关的 AI 协作提示词和自动化规则

## 模块特定规则

### 1. 修改 exceptions.py 时
```yaml
必须:
  - 继承 STTException 基类
  - 定义 error_code 类属性
  - 提供有意义的默认 message
  
示例:
  class NewError(STTException):
      error_code = "NEW_ERROR"
      def __init__(self, detail: str = ""):
          super().__init__(f"描述: {detail}", self.error_code)
```

### 2. 修改 dto.py 时
```yaml
必须:
  - 使用 @dataclass 装饰器
  - 所有字段添加类型注解
  - 可选字段使用 Optional 或 field(default=...)
  - 实现 to_dict() 方法用于 JSON 序列化
```

### 3. 修改 registry.py 时
```yaml
禁止:
  - 直接修改 _engine_registry (使用 register/unregister 函数)
  - 在模块加载时执行耗时操作
  
必须:
  - 保持引擎注册的幂等性
  - 引擎加载失败时静默跳过，不影响其他引擎
```

### 4. 修改 audio_utils.py 时
```yaml
必须:
  - 所有路径参数使用 Path 类型
  - Windows 路径传给 FFmpeg 前用 to_ffmpeg_path() 转换
  - 子进程调用设置合理超时
  - 捕获并转换为自定义异常
```

### 5. 修改 compat.py 时
```yaml
必须:
  - 支持 Windows/Linux/macOS 三平台
  - 目录创建使用 mkdir(parents=True, exist_ok=True)
  - 环境变量读取提供默认值
```

## 常用代码片段

### 添加新异常
```python
class MyNewError(STTException):
    """我的新异常"""
    error_code = "MY_NEW_ERROR"
    
    def __init__(self, context: str = ""):
        message = f"发生了新错误"
        if context:
            message += f": {context}"
        super().__init__(message, self.error_code)
```

### 添加新 DTO
```python
@dataclass
class MyDTO:
    """我的数据对象"""
    required_field: str
    optional_field: Optional[str] = None
    list_field: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "required_field": self.required_field,
            "optional_field": self.optional_field,
            "list_field": self.list_field,
        }
```

### 音频处理模板
```python
from .compat import to_ffmpeg_path
from .exceptions import FFmpegNotFoundError

def my_audio_function(input_path: Path) -> Path:
    if not check_ffmpeg():
        raise FFmpegNotFoundError()
    
    ffmpeg_input = to_ffmpeg_path(input_path)
    # ... 处理逻辑
```

## 测试检查清单

修改本模块后，确保以下测试通过：

- [ ] `python -c "from backend.app.services.stt import *"` 无报错
- [ ] `tests/unit/test_exceptions/` 异常类测试
- [ ] `tests/unit/test_dto/` DTO 序列化测试
- [ ] `tests/unit/test_registry/` 注册中心测试
- [ ] `tests/quick_test.py` 快速集成测试
