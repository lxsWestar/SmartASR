"""
serve.py - API 服务命令
========================

作用: 启动 FastAPI 服务
维护: AI + Human

用法:
    smartasr serve
    smartasr serve --port 8000 --reload
"""

from typing import Annotated

import typer

from ..utils.console import console, print_info

app = typer.Typer(
    help="启动 API 服务",
)


@app.callback(invoke_without_command=True)
def serve_command(
    host: Annotated[
        str,
        typer.Option(
            "--host", "-h",
            help="监听地址",
        ),
    ] = "0.0.0.0",
    port: Annotated[
        int,
        typer.Option(
            "--port", "-p",
            help="监听端口",
        ),
    ] = 8000,
    reload: Annotated[
        bool,
        typer.Option(
            "--reload", "-r",
            help="开发模式 (自动重载)",
        ),
    ] = False,
    workers: Annotated[
        int,
        typer.Option(
            "--workers", "-w",
            help="工作进程数 (生产模式)",
        ),
    ] = 1,
) -> None:
    """
    启动 SmartASR API 服务
    
    [bold]示例:[/bold]
    
        [cyan]smartasr serve[/cyan]
        
        [cyan]smartasr serve --port 8080[/cyan]
        
        [cyan]smartasr serve --reload[/cyan]  [dim]# 开发模式[/dim]
        
        [cyan]smartasr serve --workers 4[/cyan]  [dim]# 生产模式[/dim]
    
    [bold]API 文档:[/bold]
    
        启动后访问 http://localhost:8000/docs 查看 API 文档
    """
    try:
        import uvicorn
    except ImportError:
        console.print("[red]错误: 缺少 uvicorn[/red]")
        console.print("[dim]安装: pip install uvicorn[/dim]")
        raise typer.Exit(1)
    
    print_info(f"启动 SmartASR API 服务...")
    print_info(f"地址: http://{host}:{port}")
    print_info(f"文档: http://{host}:{port}/docs")
    console.print()
    
    uvicorn.run(
        "backend.app.api.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
    )
