# backend/app/cli/utils/

## 本目录职责

提供 CLI 层统一的终端输出工具，基于 Rich 库。**全局单例，所有命令必须通过此模块输出，禁止直接 `print()`。**

## 文件清单

| 文件 | 职责 |
|------|------|
| `console.py` | 全局 Rich Console 实例 + 格式化输出函数 |
| `__init__.py` | 导出 `console`, `err_console` 及所有工具函数 |

## console.py 提供的接口

### 全局实例

```python
console     # Rich Console，输出到 stdout
err_console # Rich Console，输出到 stderr（用于错误和警告）
```

### 工具函数

| 函数 | 输出目标 | 样式 | 用途 |
|------|----------|------|------|
| `print_success(msg)` | stdout | 绿色 ✓ | 操作成功提示 |
| `print_error(msg)` | stderr | 红色 ✗ | 错误信息 |
| `print_info(msg)` | stdout | 蓝色 ℹ | 普通提示 |
| `print_warning(msg)` | stderr | 黄色 ⚠ | 警告信息 |
| `is_verbose()` | — | — | 返回当前是否为 verbose 模式 |

## 设计约束（AI 必读）

> ⚠️ **最容易犯的错误**

1. **所有 CLI 命令禁止直接 `print()`**——必须调用本模块的工具函数，保证样式统一且可测试
2. **错误/警告必须输出到 stderr**（用 `print_error` / `print_warning`），正常结果输出到 stdout，确保管道重定向行为正确
3. **不得在此模块中添加业务逻辑**——此模块只做输出格式化，不做判断
4. **不得创建额外的 Console 实例**——始终使用 `console` 和 `err_console` 两个全局实例，避免输出交错

## 使用示例

```python
from backend.app.cli.utils.console import print_error, print_success, is_verbose

# ✅ 正确
print_success("转写完成")
print_error("引擎未安装，请运行 pip install funasr")

# ❌ 错误
print("转写完成")
import sys; print("错误", file=sys.stderr)
```

## 上下游关系

```
[上游] backend/app/cli/commands/ 下的所有命令文件
    → 导入并调用 print_* 函数进行终端输出

[下游] Rich 库（第三方）
    → 负责实际的终端渲染和颜色处理
```
