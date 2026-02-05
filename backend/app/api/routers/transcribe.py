"""
transcribe.py - 语音识别 API
==============================

端点:
- POST /transcribe - 同步识别 (适合短音频)
- POST /transcribe/async - 异步识别 (适合长音频)
"""

import json
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Any, Dict

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from typing import List

from backend.app.services.stt import (
    create_engine,
    check_ffmpeg,
    convert_to_16k_wav,
    STTRequest,
    STTResponse,
    STTSegment,
    EngineNotFoundError,
    ModelNotFoundError,
    TranscriptionError,
    FFmpegNotFoundError,
)
from backend.app.services.stt.compat import get_cache_dir

from .tasks import task_manager, TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Pydantic 响应模型 ============

class SegmentResponse(BaseModel):
    """识别片段"""
    start_ms: int
    end_ms: int
    text: str


class TranscribeResponse(BaseModel):
    """同步识别响应"""
    text: str
    segments: List[SegmentResponse]
    duration_ms: int
    engine: str
    model: str
    language_detected: Optional[str] = None


class AsyncTranscribeResponse(BaseModel):
    """异步识别响应"""
    task_id: str
    status: str
    message: str


# ============ 辅助函数 ============

def _save_upload_file(upload_file: UploadFile) -> Path:
    """
    保存上传文件到临时目录
    
    Returns:
        Path: 保存的文件路径
    """
    cache_dir = get_cache_dir() / "uploads"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # 保留原始扩展名
    suffix = Path(upload_file.filename).suffix if upload_file.filename else ".tmp"
    temp_file = cache_dir / f"upload_{id(upload_file)}{suffix}"
    
    with open(temp_file, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    
    return temp_file


def _preprocess_audio(audio_path: Path) -> Path:
    """
    预处理音频文件 (转为 16kHz WAV)
    
    Returns:
        Path: 处理后的文件路径
    """
    # 如果已经是 16kHz WAV，直接返回
    if audio_path.suffix.lower() == ".wav":
        # TODO: 检查采样率，如果已是 16kHz 则跳过
        pass
    
    # 转换
    output_path = audio_path.parent / f"{audio_path.stem}_16k.wav"
    convert_to_16k_wav(audio_path, output_path)
    return output_path


def _cleanup_files(*files: Path) -> None:
    """清理临时文件"""
    for f in files:
        try:
            if f and f.exists():
                f.unlink()
        except Exception:
            pass


# ============ API 端点 ============

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_sync(
    file: UploadFile = File(..., description="音频文件"),
    engine: str = Form(default="ali_funasr", description="引擎名称"),
    model: Optional[str] = Form(default=None, description="模型名称"),
    language: str = Form(default="auto", description="语言 (zh/en/ja/ko/auto)"),
    options: Optional[str] = Form(default=None, description="引擎特定参数 (JSON)"),
):
    """
    同步语音识别
    
    上传音频文件并立即返回识别结果。适合短音频 (< 1分钟)。
    
    **支持格式**: mp3, wav, flac, ogg, m4a, aac, webm, mp4, mkv, avi
    
    **示例 options**:
    ```json
    {"use_itn": true, "max_speakers": 2}
    ```
    """
    # 检查 FFmpeg
    if not check_ffmpeg():
        raise HTTPException(status_code=500, detail="FFmpeg 未安装")
    
    # 解析 options
    options_dict: Dict[str, Any] = {}
    if options:
        try:
            options_dict = json.loads(options)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="options 必须是有效的 JSON")
    
    # 保存上传文件
    upload_path = None
    processed_path = None
    
    try:
        upload_path = _save_upload_file(file)
        logger.info(f"保存上传文件: {upload_path}")
        
        # 预处理音频
        processed_path = _preprocess_audio(upload_path)
        logger.info(f"预处理完成: {processed_path}")
        
        # 创建引擎
        try:
            stt_engine = create_engine(engine)
        except EngineNotFoundError:
            raise HTTPException(status_code=404, detail=f"引擎 '{engine}' 不存在")
        
        # 检查引擎可用性
        available, reason = stt_engine.check_available()
        if not available:
            raise HTTPException(status_code=503, detail=f"引擎不可用: {reason}")
        
        # 构建请求
        request = STTRequest(
            audio_path=processed_path,
            language=language,
            engine=engine,
            model=model,
            options=options_dict,
        )
        
        # 执行识别
        try:
            result = stt_engine.transcribe(request)
        except ModelNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except TranscriptionError as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        # 返回结果
        return TranscribeResponse(
            text=result.text,
            segments=[
                SegmentResponse(
                    start_ms=seg.start_ms,
                    end_ms=seg.end_ms,
                    text=seg.text,
                )
                for seg in result.segments
            ],
            duration_ms=result.duration_ms,
            engine=result.engine,
            model=result.model,
            language_detected=result.language_detected,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"识别失败: {e}")
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")
    finally:
        # 清理临时文件
        _cleanup_files(upload_path, processed_path)


@router.post("/transcribe/async", response_model=AsyncTranscribeResponse)
async def transcribe_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="音频文件"),
    engine: str = Form(default="ali_funasr", description="引擎名称"),
    model: Optional[str] = Form(default=None, description="模型名称"),
    language: str = Form(default="auto", description="语言 (zh/en/ja/ko/auto)"),
    options: Optional[str] = Form(default=None, description="引擎特定参数 (JSON)"),
    callback_url: Optional[str] = Form(default=None, description="完成回调 URL"),
):
    """
    异步语音识别
    
    提交音频文件并返回任务 ID，通过 `/tasks/{task_id}` 查询结果。
    适合长音频 (> 1分钟)。
    
    **回调**: 如果提供 `callback_url`，任务完成时会 POST 结果到该地址。
    """
    # 检查 FFmpeg
    if not check_ffmpeg():
        raise HTTPException(status_code=500, detail="FFmpeg 未安装")
    
    # 解析 options
    options_dict: Dict[str, Any] = {}
    if options:
        try:
            options_dict = json.loads(options)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="options 必须是有效的 JSON")
    
    # 保存上传文件 (异步任务需要保留文件)
    try:
        upload_path = _save_upload_file(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    
    # 创建任务
    task_id = task_manager.create_task(
        engine=engine,
        model=model,
        audio_path=str(upload_path),
        callback_url=callback_url,
    )
    
    # 添加后台任务
    background_tasks.add_task(
        _run_transcription_task,
        task_id=task_id,
        audio_path=upload_path,
        engine=engine,
        model=model,
        language=language,
        options=options_dict,
        callback_url=callback_url,
    )
    
    return AsyncTranscribeResponse(
        task_id=task_id,
        status=TaskStatus.PENDING.value,
        message="任务已提交",
    )


async def _run_transcription_task(
    task_id: str,
    audio_path: Path,
    engine: str,
    model: Optional[str],
    language: str,
    options: Dict[str, Any],
    callback_url: Optional[str],
) -> None:
    """后台执行识别任务"""
    processed_path = None
    
    # 进度回调函数
    def progress_callback(current: int, total: int, message: str) -> None:
        """更新任务进度"""
        if total > 0:
            progress = current / total
        else:
            progress = 0.0
        task_manager.update_task(
            task_id,
            progress=progress,
            progress_current=current,
            progress_total=total,
            progress_message=message,
        )
        logger.debug(f"任务 {task_id} 进度: {current}/{total} - {message}")
    
    try:
        # 更新状态为处理中
        task_manager.update_task(task_id, status=TaskStatus.PROCESSING)
        
        # 预处理音频
        processed_path = _preprocess_audio(audio_path)
        
        # 创建引擎
        stt_engine = create_engine(engine)
        
        # 检查可用性
        available, reason = stt_engine.check_available()
        if not available:
            raise TranscriptionError(f"引擎不可用: {reason}", engine_name=engine)
        
        # 执行识别 (带进度回调)
        request = STTRequest(
            audio_path=processed_path,
            language=language,
            engine=engine,
            model=model,
            options=options,
            progress_callback=progress_callback,
        )
        result = stt_engine.transcribe(request)
        
        # 转换结果
        result_dict = result.to_dict()
        
        # 更新任务完成
        task_manager.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            progress=1.0,
            result=result_dict,
        )
        
        # 发送回调
        if callback_url:
            await _send_callback(callback_url, task_id, TaskStatus.COMPLETED, result_dict)
            
    except Exception as e:
        logger.exception(f"任务 {task_id} 执行失败: {e}")
        error_msg = str(e)
        task_manager.update_task(
            task_id,
            status=TaskStatus.FAILED,
            error=error_msg,
        )
        
        if callback_url:
            await _send_callback(callback_url, task_id, TaskStatus.FAILED, None, error_msg)
    
    finally:
        # 清理临时文件
        _cleanup_files(audio_path, processed_path)


async def _send_callback(
    url: str,
    task_id: str,
    status: TaskStatus,
    result: Optional[Dict],
    error: Optional[str] = None,
) -> None:
    """发送 Webhook 回调"""
    import httpx
    
    payload = {
        "event": f"task.{status.value}",
        "task_id": task_id,
        "status": status.value,
    }
    
    if result:
        payload["result"] = result
    if error:
        payload["error"] = error
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=10.0)
            logger.info(f"回调发送成功: {url}")
    except Exception as e:
        logger.warning(f"回调发送失败: {url}, 错误: {e}")
