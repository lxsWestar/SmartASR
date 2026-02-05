"""
main.py - CLI 主程序
=====================

作用: 定义 CLI 应用和全局选项
维护: AI + Human

设计决策:
- 使用 typer 作为 CLI 框架 (基于 click，支持类型提示)
- 使用 rich 提供美化输出
- 子命令分离到 commands/ 目录
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

# 版本信息
__version__ = "0.1.0"

# 全局控制台实例
console = Console()
err_console = Console(stderr=True)

# 创建主应用
app = typer.Typer(
    name="smartasr",
    help="SmartASR - 轻量级语音转文字工具",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
)


def version_callback(value: bool) -> None:
    """显示版本信息"""
    if value:
        console.print(f"[bold blue]SmartASR[/bold blue] v{__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="显示版本信息",
        callback=version_callback,
        is_eager=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="显示详细输出",
    ),
) -> None:
    """
    SmartASR - 轻量级语音转文字工具
    
    支持多种本地和云端语音识别引擎，提供统一的命令行接口。
    
    [bold]快速开始:[/bold]
    
        [cyan]smartasr transcribe audio.mp3[/cyan]
        
        [cyan]smartasr transcribe audio.mp3 -o result.srt[/cyan]
    
    [bold]更多帮助:[/bold]
    
        [cyan]smartasr transcribe --help[/cyan]
    """
    # 将 verbose 存储到上下文中供子命令使用
    # typer 没有直接的上下文传递，使用模块级变量
    import backend.app.cli.utils.console as console_utils
    console_utils.VERBOSE = verbose


# 导入并注册子命令
from .commands import transcribe, engines, config, serve

app.add_typer(transcribe.app, name="transcribe", help="语音识别")
app.add_typer(engines.app, name="engines", help="引擎管理")
app.add_typer(config.app, name="config", help="配置管理")
app.add_typer(serve.app, name="serve", help="启动 API 服务")


# 添加快捷命令：直接 `smartasr audio.mp3` 等同于 `smartasr transcribe audio.mp3`
@app.command(hidden=True)
def default_transcribe(
    inputs: list[Path] = typer.Argument(
        ...,
        help="输入音频文件",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="输出文件或目录",
    ),
) -> None:
    """快捷识别命令 (等同于 smartasr transcribe)"""
    # 委托给 transcribe 命令
    from .commands.transcribe import transcribe_files
    transcribe_files(inputs=inputs, output=output)


def main() -> None:
    """CLI 入口函数"""
    try:
        app()
    except KeyboardInterrupt:
        err_console.print("\n[yellow]操作已取消[/yellow]")
        sys.exit(130)
    except Exception as e:
        err_console.print(f"[red]错误: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
