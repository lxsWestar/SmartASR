# backend/app/cli/commands/

## 本目录职责

每个文件实现一个顶级 CLI 子命令，基于 Typer 框架。父级入口 `backend/app/cli/main.py` 统一注册。

> 详细的 CLI 整体设计见 [`backend/app/cli/README.md`](../README.md)，本文档聚焦各命令文件的职责划分及扩展规则。

## 文件清单

| 文件 | 命令 | 职责 |
|------|------|------|
| `serve.py` | `smartasr serve` | 启动 FastAPI HTTP 服务，管理 uvicorn 进程 |
| `transcribe.py` | `smartasr transcribe` | 命令行直接转写音频文件，输出格式化结果 |
| `engines.py` | `smartasr engines` | 列出/查询可用引擎及其支持的参数 |
| `config.py` | `smartasr config` | 读取、验证、展示当前配置 |
| `__init__.py` | — | 包标识，通常为空 |

## 注册规则

新增命令文件后，**必须** 在 `backend/app/cli/main.py` 中注册：

```python
# main.py
from backend.app.cli.commands import new_cmd
app.add_typer(new_cmd.app, name="new-command")
```

## 设计约束（AI 必读）

> ⚠️ **添加新命令时最容易犯的错误**

1. **命令层禁止直接 `print()`**——所有终端输出必须通过 `backend/app/cli/utils/console.py` 的工具函数（`print_error`, `print_success` 等）
2. **transcribe 命令不通过 HTTP**——直接调用 `backend/app/services/stt/` 服务层，不依赖服务是否启动
3. **serve 命令不包含业务逻辑**——只负责启动/停止 uvicorn 进程，配置加载由服务层处理
4. **参数命名遵循 CLI 惯例**——多词用连字符 `--output-format`，不用下划线 `--output_format`
5. **错误处理统一用 `typer.Exit(code=1)` 退出**，先调用 `print_error()` 打印原因

## 上下游关系

```
[上游] backend/app/cli/main.py
    → add_typer 注册各子命令

[下游] backend/app/services/stt/
    → transcribe 命令直接调用（不经过 HTTP）

[下游] uvicorn（系统进程）
    → serve 命令启动 HTTP 服务

[下游] backend/app/cli/utils/console.py
    → 所有命令的终端输出

[下游] backend/app/cli/formatters/
    → transcribe 命令根据 -f 参数选择输出格式化器
```
