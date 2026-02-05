"""
console.py - 终端输出工具
==========================

作用: 统一的终端输出函数，支持 rich 美化
维护: AI + Human
"""

from rich.console import Console

# 全局控制台实例
console = Console()
err_console = Console(stderr=True)

# 详细模式标志 (由 main.py 设置)
VERBOSE = False


def is_verbose() -> bool:
    """检查是否启用详细模式"""
    return VERBOSE


def print_error(message: str) -> None:
    """打印错误信息"""
    err_console.print(f"[red]✗ 错误:[/red] {message}")


def print_success(message: str) -> None:
    """打印成功信息"""
    console.print(f"[green]✓[/green] {message}")


def print_info(message: str) -> None:
    """打印提示信息"""
    console.print(f"[blue]ℹ[/blue] {message}")


def print_warning(message: str) -> None:
    """打印警告信息"""
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_debug(message: str) -> None:
    """打印调试信息 (仅详细模式)"""
    if VERBOSE:
        console.print(f"[dim]DEBUG: {message}[/dim]")
