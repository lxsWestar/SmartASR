"""
config.py - 配置管理命令
=========================

作用: 查看和设置配置项
维护: AI + Human

用法:
    smartasr config show
    smartasr config set models_dir /path/to/models
"""

import os
from typing import Optional, Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..utils.console import console, print_error, print_success, print_info

app = typer.Typer(
    help="配置管理命令",
    no_args_is_help=True,
)


# 配置项定义
CONFIG_ITEMS = {
    "models_dir": {
        "env": "STT_MODELS_DIR",
        "description": "模型存储目录",
        "type": "path",
    },
    "model_server": {
        "env": "STT_MODEL_SERVER",
        "description": "模型服务器地址",
        "type": "url",
    },
    "default_engine": {
        "env": "STT_DEFAULT_ENGINE",
        "description": "默认引擎名称",
        "type": "string",
    },
    "ffmpeg_path": {
        "env": "FFMPEG_PATH",
        "description": "FFmpeg 可执行文件路径",
        "type": "path",
    },
    "log_level": {
        "env": "STT_LOG_LEVEL",
        "description": "日志级别 (DEBUG, INFO, WARNING, ERROR)",
        "type": "string",
    },
}


def get_config_value(key: str) -> Optional[str]:
    """获取配置值"""
    if key in CONFIG_ITEMS:
        env_name = CONFIG_ITEMS[key]["env"]
        return os.environ.get(env_name)
    return None


def set_config_value(key: str, value: str) -> bool:
    """设置配置值 (仅当前会话)"""
    if key in CONFIG_ITEMS:
        env_name = CONFIG_ITEMS[key]["env"]
        os.environ[env_name] = value
        return True
    return False


@app.command(name="show")
def show_command() -> None:
    """
    显示当前配置
    
    [bold]示例:[/bold]
    
        [cyan]smartasr config show[/cyan]
    """
    table = Table(
        title="当前配置",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("配置项")
    table.add_column("环境变量")
    table.add_column("当前值")
    table.add_column("描述")
    
    for key, info in CONFIG_ITEMS.items():
        env_name = info["env"]
        value = os.environ.get(env_name, "[dim]未设置[/dim]")
        table.add_row(key, env_name, value, info["description"])
    
    console.print(table)
    
    # 显示设置提示
    console.print("\n[bold]设置方式:[/bold]")
    console.print("  [dim]# 临时设置 (当前会话)[/dim]")
    console.print("  [cyan]smartasr config set models_dir /path/to/models[/cyan]")
    console.print("")
    console.print("  [dim]# 永久设置 (环境变量)[/dim]")
    console.print("  [cyan]$env:STT_MODELS_DIR = \"D:\\models\"[/cyan]  [dim]# PowerShell[/dim]")
    console.print("  [cyan]export STT_MODELS_DIR=/path/to/models[/cyan]  [dim]# Bash[/dim]")


@app.command(name="set")
def set_command(
    key: Annotated[
        str,
        typer.Argument(help="配置项名称"),
    ],
    value: Annotated[
        str,
        typer.Argument(help="配置值"),
    ],
) -> None:
    """
    设置配置项 (仅当前会话)
    
    [bold]示例:[/bold]
    
        [cyan]smartasr config set models_dir /path/to/models[/cyan]
        
        [cyan]smartasr config set default_engine ali_funasr[/cyan]
    
    [bold yellow]注意:[/bold yellow] 此设置仅在当前会话有效。要永久设置，请使用环境变量。
    """
    if key not in CONFIG_ITEMS:
        print_error(f"未知的配置项: {key}")
        console.print(f"\n[dim]可用配置项: {', '.join(CONFIG_ITEMS.keys())}[/dim]")
        raise typer.Exit(1)
    
    if set_config_value(key, value):
        print_success(f"已设置 {key} = {value}")
        console.print(f"\n[yellow]注意: 此设置仅在当前会话有效[/yellow]")
        console.print(f"[dim]永久设置: $env:{CONFIG_ITEMS[key]['env']} = \"{value}\"[/dim]")
    else:
        print_error("设置失败")
        raise typer.Exit(1)


@app.command(name="get")
def get_command(
    key: Annotated[
        str,
        typer.Argument(help="配置项名称"),
    ],
) -> None:
    """
    获取配置项的值
    
    [bold]示例:[/bold]
    
        [cyan]smartasr config get models_dir[/cyan]
    """
    if key not in CONFIG_ITEMS:
        print_error(f"未知的配置项: {key}")
        console.print(f"\n[dim]可用配置项: {', '.join(CONFIG_ITEMS.keys())}[/dim]")
        raise typer.Exit(1)
    
    value = get_config_value(key)
    if value:
        console.print(value)
    else:
        console.print("[dim]未设置[/dim]")


@app.command(name="env")
def env_command() -> None:
    """
    显示环境变量设置脚本
    
    [bold]示例:[/bold]
    
        [cyan]smartasr config env[/cyan]
    """
    console.print("[bold]PowerShell 设置脚本:[/bold]")
    console.print()
    
    for key, info in CONFIG_ITEMS.items():
        value = os.environ.get(info["env"], "")
        if value:
            console.print(f'$env:{info["env"]} = "{value}"')
        else:
            console.print(f'# $env:{info["env"]} = ""  # {info["description"]}')
    
    console.print()
    console.print("[bold]Bash 设置脚本:[/bold]")
    console.print()
    
    for key, info in CONFIG_ITEMS.items():
        value = os.environ.get(info["env"], "")
        if value:
            console.print(f'export {info["env"]}="{value}"')
        else:
            console.print(f'# export {info["env"]}=""  # {info["description"]}')
