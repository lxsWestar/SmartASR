"""
transcribe.py - 语音识别命令
=============================

作用: 核心识别命令实现
维护: AI + Human

用法:
    smartasr transcribe audio.mp3
    smartasr transcribe audio.mp3 -o result.srt
    smartasr transcribe *.mp3 -o output_dir/
"""

import sys
import time
from pathlib import Path
from typing import Optional, List, Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

from ..utils.console import console, err_console, print_error, print_success, print_info, is_verbose
from ..formatters import get_formatter, list_formats, detect_format_from_path

# 创建子应用
app = typer.Typer(
    help="语音识别命令",
    no_args_is_help=True,
)


# 支持的音频格式
SUPPORTED_AUDIO_FORMATS = {
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac",
    ".webm", ".mp4", ".mkv", ".avi", ".mov", ".wma",
}


def validate_audio_file(path: Path) -> bool:
    """验证音频文件"""
    if not path.exists():
        return False
    if not path.is_file():
        return False
    if path.suffix.lower() not in SUPPORTED_AUDIO_FORMATS:
        return False
    return True


def get_stt_service():
    """延迟导入 STT 服务"""
    from backend.app.services.stt import (
        create_engine,
        list_engines,
        check_ffmpeg,
        convert_to_16k_wav,
        STTRequest,
        STTResponse,
    )
    from backend.app.services.stt.compat import get_cache_dir
    return {
        "create_engine": create_engine,
        "list_engines": list_engines,
        "check_ffmpeg": check_ffmpeg,
        "convert_to_16k_wav": convert_to_16k_wav,
        "STTRequest": STTRequest,
        "get_cache_dir": get_cache_dir,
    }


def transcribe_single_file(
    audio_path: Path,
    engine_name: str,
    model: Optional[str],
    language: str,
    stt: dict,
    progress: Optional[Progress] = None,
    task_id: Optional[int] = None,
) -> Optional[dict]:
    """
    识别单个文件
    
    Returns:
        识别结果字典，失败返回 None
    """
    create_engine = stt["create_engine"]
    check_ffmpeg = stt["check_ffmpeg"]
    convert_to_16k_wav = stt["convert_to_16k_wav"]
    STTRequest = stt["STTRequest"]
    get_cache_dir = stt["get_cache_dir"]
    
    # 检查 FFmpeg
    if not check_ffmpeg():
        print_error("FFmpeg 未安装或不在 PATH 中")
        print_info("请安装 FFmpeg: https://ffmpeg.org/download.html")
        return None
    
    # 预处理音频
    cache_dir = get_cache_dir() / "cli_temp"
    cache_dir.mkdir(parents=True, exist_ok=True)
    processed_path = cache_dir / f"{audio_path.stem}_{int(time.time())}_16k.wav"
    
    try:
        if progress and task_id is not None:
            progress.update(task_id, description=f"[cyan]转换音频: {audio_path.name}[/cyan]")
        
        convert_to_16k_wav(audio_path, processed_path)
        
        # 创建引擎
        if progress and task_id is not None:
            progress.update(task_id, description=f"[cyan]加载引擎: {engine_name}[/cyan]")
        
        engine = create_engine(engine_name)
        
        # 检查可用性
        available, reason = engine.check_available()
        if not available:
            print_error(f"引擎不可用: {reason}")
            return None
        
        # 创建请求
        request = STTRequest(
            audio_path=processed_path,
            language=language,
            engine=engine_name,
            model=model,
        )
        
        # 执行识别
        if progress and task_id is not None:
            progress.update(task_id, description=f"[cyan]识别中: {audio_path.name}[/cyan]")
        
        start_time = time.time()
        result = engine.transcribe(request)
        elapsed = time.time() - start_time
        
        # 计算 RTF
        rtf = elapsed / (result.duration_ms / 1000) if result.duration_ms > 0 else 0
        
        return {
            "result": result,
            "elapsed": elapsed,
            "rtf": rtf,
            "audio_path": audio_path,
        }
        
    except Exception as e:
        print_error(f"识别失败: {e}")
        if is_verbose():
            import traceback
            err_console.print(traceback.format_exc())
        return None
        
    finally:
        # 清理临时文件
        if processed_path.exists():
            try:
                processed_path.unlink()
            except Exception:
                pass


def transcribe_files(
    inputs: List[Path],
    output: Optional[Path] = None,
    output_format: Optional[str] = None,
    engine: str = "ali_funasr",
    model: Optional[str] = None,
    language: str = "auto",
) -> int:
    """
    批量识别文件
    
    Returns:
        成功处理的文件数
    """
    # 验证输入文件
    valid_inputs = []
    for path in inputs:
        if validate_audio_file(path):
            valid_inputs.append(path)
        else:
            print_error(f"无效的音频文件: {path}")
    
    if not valid_inputs:
        print_error("没有有效的输入文件")
        return 0
    
    # 加载 STT 服务
    try:
        stt = get_stt_service()
    except ImportError as e:
        print_error(f"无法加载 STT 服务: {e}")
        return 0
    
    # 确定输出格式
    if output_format is None and output is not None:
        output_format = detect_format_from_path(output)
    if output_format is None:
        output_format = "txt"
    
    # 获取格式化器
    formatter = get_formatter(output_format)
    if formatter is None:
        print_error(f"不支持的输出格式: {output_format}")
        print_info(f"支持的格式: {', '.join(list_formats())}")
        return 0
    
    # 判断输出是目录还是文件
    output_is_dir = False
    if output:
        if output.is_dir():
            output_is_dir = True
        elif len(valid_inputs) > 1:
            # 多文件时，输出路径作为目录
            output_is_dir = True
            output.mkdir(parents=True, exist_ok=True)
    
    # 处理文件
    success_count = 0
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        disable=not sys.stdout.isatty(),
    ) as progress:
        task_id = progress.add_task(
            "[cyan]准备中...[/cyan]",
            total=len(valid_inputs),
        )
        
        for i, audio_path in enumerate(valid_inputs):
            progress.update(task_id, completed=i)
            
            result = transcribe_single_file(
                audio_path=audio_path,
                engine_name=engine,
                model=model,
                language=language,
                stt=stt,
                progress=progress,
                task_id=task_id,
            )
            
            if result:
                results.append(result)
                success_count += 1
                
                # 格式化输出
                output_text = formatter.format(result["result"])
                
                # 写入或打印
                if output:
                    if output_is_dir:
                        out_file = output / f"{audio_path.stem}.{formatter.extension}"
                    else:
                        out_file = output
                    
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    out_file.write_text(output_text, encoding="utf-8")
                    
                    if is_verbose():
                        print_success(f"已保存: {out_file}")
                else:
                    # 输出到控制台
                    console.print(output_text)
        
        progress.update(task_id, completed=len(valid_inputs), description="[green]完成[/green]")
    
    # 打印统计信息
    if is_verbose() and results:
        _print_statistics(results)
    
    return success_count


def _print_statistics(results: List[dict]) -> None:
    """打印统计信息"""
    table = Table(title="识别统计", show_header=True, header_style="bold cyan")
    table.add_column("文件", style="dim")
    table.add_column("时长", justify="right")
    table.add_column("耗时", justify="right")
    table.add_column("RTF", justify="right")
    
    total_duration = 0
    total_elapsed = 0
    
    for r in results:
        audio_path = r["audio_path"]
        result = r["result"]
        elapsed = r["elapsed"]
        rtf = r["rtf"]
        
        duration_s = result.duration_ms / 1000
        total_duration += duration_s
        total_elapsed += elapsed
        
        table.add_row(
            audio_path.name,
            f"{duration_s:.1f}s",
            f"{elapsed:.2f}s",
            f"{rtf:.3f}",
        )
    
    # 添加汇总行
    if len(results) > 1:
        avg_rtf = total_elapsed / total_duration if total_duration > 0 else 0
        table.add_row(
            "[bold]总计[/bold]",
            f"[bold]{total_duration:.1f}s[/bold]",
            f"[bold]{total_elapsed:.2f}s[/bold]",
            f"[bold]{avg_rtf:.3f}[/bold]",
            style="bold",
        )
    
    console.print(table)


@app.command(name="run")
def transcribe_command(
    inputs: Annotated[
        List[Path],
        typer.Argument(
            help="输入音频文件 (支持多个文件)",
        ),
    ],
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output", "-o",
            help="输出文件或目录 (不指定则输出到控制台)",
        ),
    ] = None,
    output_format: Annotated[
        Optional[str],
        typer.Option(
            "--format", "-f",
            help=f"输出格式: {', '.join(list_formats())}",
        ),
    ] = None,
    engine: Annotated[
        str,
        typer.Option(
            "--engine", "-e",
            help="引擎名称",
        ),
    ] = "ali_funasr",
    model: Annotated[
        Optional[str],
        typer.Option(
            "--model", "-m",
            help="模型名称 (默认使用引擎默认模型)",
        ),
    ] = None,
    language: Annotated[
        str,
        typer.Option(
            "--language", "-l",
            help="语言: auto, zh, en, ja, ko, yue",
        ),
    ] = "auto",
) -> None:
    """
    语音识别 - 将音频转换为文字
    
    [bold]示例:[/bold]
    
        [cyan]smartasr transcribe run audio.mp3[/cyan]
        
        [cyan]smartasr transcribe run audio.mp3 -o result.srt[/cyan]
        
        [cyan]smartasr transcribe run *.mp3 -o output/ -f srt[/cyan]
        
        [cyan]smartasr transcribe run audio.mp3 -e ali_funasr -m SenseVoiceSmall[/cyan]
    
    [bold]支持的音频格式:[/bold]
    
        mp3, wav, flac, ogg, m4a, aac, webm, mp4, mkv, avi, mov, wma
    
    [bold]输出格式:[/bold]
    
        txt   - 纯文本
        srt   - SRT 字幕
        vtt   - WebVTT 字幕
        json  - JSON (含完整元数据)
        tsv   - 制表符分隔表格
    """
    # 验证输入文件存在
    for path in inputs:
        if not path.exists():
            print_error(f"文件不存在: {path}")
            raise typer.Exit(1)
    
    success = transcribe_files(
        inputs=inputs,
        output=output,
        output_format=output_format,
        engine=engine,
        model=model,
        language=language,
    )
    
    if success == 0:
        raise typer.Exit(1)
    elif success < len(inputs):
        print_info(f"部分成功: {success}/{len(inputs)} 个文件")
        raise typer.Exit(1)
    else:
        if is_verbose():
            print_success(f"全部完成: {success} 个文件")


# 让 `smartasr transcribe audio.mp3` 直接工作 (不需要 run 子命令)
@app.callback(invoke_without_command=True)
def transcribe_callback(
    ctx: typer.Context,
    inputs: Annotated[
        Optional[List[Path]],
        typer.Argument(
            help="输入音频文件",
        ),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output", "-o",
            help="输出文件或目录",
        ),
    ] = None,
    output_format: Annotated[
        Optional[str],
        typer.Option(
            "--format", "-f",
            help="输出格式",
        ),
    ] = None,
    engine: Annotated[
        str,
        typer.Option(
            "--engine", "-e",
            help="引擎名称",
        ),
    ] = "ali_funasr",
    model: Annotated[
        Optional[str],
        typer.Option(
            "--model", "-m",
            help="模型名称",
        ),
    ] = None,
    language: Annotated[
        str,
        typer.Option(
            "--language", "-l",
            help="语言",
        ),
    ] = "auto",
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose", "-v",
            help="显示详细输出",
        ),
    ] = False,
) -> None:
    """
    语音识别 - 将音频转换为文字
    """
    # 设置 verbose 模式
    if verbose:
        import backend.app.cli.utils.console as console_utils
        console_utils.VERBOSE = True
    
    # 如果有子命令被调用，跳过
    if ctx.invoked_subcommand is not None:
        return
    
    # 如果没有输入，显示帮助
    if not inputs:
        console.print(ctx.get_help())
        raise typer.Exit(0)
    
    # 验证输入文件存在
    for path in inputs:
        if not path.exists():
            print_error(f"文件不存在: {path}")
            raise typer.Exit(1)
    
    success = transcribe_files(
        inputs=inputs,
        output=output,
        output_format=output_format,
        engine=engine,
        model=model,
        language=language,
    )
    
    if success == 0:
        raise typer.Exit(1)
