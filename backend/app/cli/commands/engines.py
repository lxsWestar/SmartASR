"""
engines.py - 引擎管理命令
==========================

作用: 列出、检查和查看引擎信息
维护: AI + Human

用法:
    smartasr engines list
    smartasr engines info ali_funasr
    smartasr engines check
"""

from typing import Optional, Annotated

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree

from ..utils.console import console, print_error, print_success, print_info, is_verbose

app = typer.Typer(
    help="引擎管理命令",
    no_args_is_help=True,
)


def get_engine_service():
    """延迟导入引擎服务"""
    from backend.app.services.stt import (
        list_engines,
        create_engine,
        get_engine_metadata,
    )
    from backend.app.services.stt.registry import get_all_engines
    return {
        "list_engines": list_engines,
        "get_all_engines": get_all_engines,
        "create_engine": create_engine,
        "get_engine_metadata": get_engine_metadata,
    }


@app.command(name="list")
def list_command(
    available_only: Annotated[
        bool,
        typer.Option(
            "--available", "-a",
            help="只显示可用的引擎",
        ),
    ] = False,
) -> None:
    """
    列出所有引擎
    
    [bold]示例:[/bold]
    
        [cyan]smartasr engines list[/cyan]
        
        [cyan]smartasr engines list --available[/cyan]
    """
    try:
        svc = get_engine_service()
        engine_names = svc["list_engines"]()
    except ImportError as e:
        print_error(f"无法加载引擎服务: {e}")
        raise typer.Exit(1)
    
    table = Table(
        title="可用引擎",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("状态", width=4)
    table.add_column("引擎", style="bold")
    table.add_column("类型")
    table.add_column("描述")
    table.add_column("模型数")
    
    for name in engine_names:
        # 获取元数据
        try:
            meta = svc["get_engine_metadata"](name)
        except Exception:
            meta = None
        
        # 检查可用性
        try:
            engine = svc["create_engine"](name)
            available, reason = engine.check_available()
        except Exception:
            available = False
            reason = "加载失败"
        
        if available_only and not available:
            continue
        
        status = "[green]✓[/green]" if available else "[red]✗[/red]"
        engine_type = meta.engine_type if meta and hasattr(meta, "engine_type") else "unknown"
        model_count = len(meta.models) if meta and hasattr(meta, "models") else 0
        description = meta.description if meta and hasattr(meta, "description") else ""
        
        table.add_row(
            status,
            name,
            engine_type,
            description,
            str(model_count),
        )
    
    console.print(table)
    
    if not available_only:
        console.print("\n[dim]提示: 使用 --available 只显示可用引擎[/dim]")


@app.command(name="info")
def info_command(
    engine_name: Annotated[
        str,
        typer.Argument(help="引擎名称"),
    ],
) -> None:
    """
    查看引擎详细信息
    
    [bold]示例:[/bold]
    
        [cyan]smartasr engines info ali_funasr[/cyan]
    """
    try:
        svc = get_engine_service()
        meta = svc["get_engine_metadata"](engine_name)
        engine = svc["create_engine"](engine_name)
    except ImportError as e:
        print_error(f"无法加载引擎服务: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"引擎不存在: {engine_name}")
        raise typer.Exit(1)
    
    # 检查可用性
    available, reason = engine.check_available()
    status = "[green]可用[/green]" if available else f"[red]不可用: {reason}[/red]"
    
    # 基本信息
    info_text = f"""
[bold]引擎:[/bold] {meta.name}
[bold]类型:[/bold] {meta.engine_type if hasattr(meta, 'engine_type') else 'unknown'}
[bold]状态:[/bold] {status}
[bold]描述:[/bold] {meta.description if hasattr(meta, 'description') else 'N/A'}
"""
    
    console.print(Panel(info_text.strip(), title=f"引擎信息: {engine_name}", border_style="cyan"))
    
    # 模型列表
    if hasattr(meta, "models") and meta.models:
        console.print("\n[bold]支持的模型:[/bold]")
        
        models_table = Table(show_header=True, header_style="bold")
        models_table.add_column("模型名称")
        models_table.add_column("语言")
        models_table.add_column("大小")
        models_table.add_column("描述")
        
        for model in meta.models:
            if hasattr(model, "name"):
                languages = ", ".join(model.languages) if hasattr(model, "languages") and model.languages else "N/A"
                size = model.size if hasattr(model, "size") else "N/A"
                desc = model.description if hasattr(model, "description") else ""
                models_table.add_row(model.name, languages, size, desc)
            else:
                # 简单字符串模型名
                models_table.add_row(str(model), "N/A", "N/A", "")
        
        console.print(models_table)
    
    # 参数规格
    if hasattr(meta, "parameters") and meta.parameters:
        console.print("\n[bold]支持的参数:[/bold]")
        
        params_table = Table(show_header=True, header_style="bold")
        params_table.add_column("参数")
        params_table.add_column("类型")
        params_table.add_column("默认值")
        params_table.add_column("描述")
        
        for param in meta.parameters:
            if hasattr(param, "name"):
                params_table.add_row(
                    param.name,
                    param.type if hasattr(param, "type") else "any",
                    str(param.default) if hasattr(param, "default") else "N/A",
                    param.description if hasattr(param, "description") else "",
                )
        
        console.print(params_table)


@app.command(name="check")
def check_command() -> None:
    """
    检查所有引擎状态
    
    [bold]示例:[/bold]
    
        [cyan]smartasr engines check[/cyan]
    """
    try:
        svc = get_engine_service()
        engine_names = svc["list_engines"]()
    except ImportError as e:
        print_error(f"无法加载引擎服务: {e}")
        raise typer.Exit(1)
    
    console.print("[bold]检查引擎状态...[/bold]\n")
    
    available_count = 0
    total_count = len(engine_names)
    
    for name in engine_names:
        try:
            engine = svc["create_engine"](name)
            available, reason = engine.check_available()
        except Exception as e:
            available = False
            reason = str(e)
        
        if available:
            available_count += 1
            console.print(f"  [green]✓[/green] {name}")
        else:
            console.print(f"  [red]✗[/red] {name}: {reason}")
    
    console.print(f"\n[bold]结果:[/bold] {available_count}/{total_count} 引擎可用")
    
    if available_count == 0:
        print_error("没有可用的引擎")
        console.print("\n[dim]提示: 请安装至少一个引擎的依赖[/dim]")
        console.print("[dim]  pip install funasr  # FunASR 本地引擎[/dim]")
        raise typer.Exit(1)
